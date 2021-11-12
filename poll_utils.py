import re
import pandas as pd

# results_output = open('data/mnpoll_20200924_raw.txt', 'r').read()
# results_export_file = 'data/mnpoll_20200924_results.xlsx'

BREAKDOWN_ORDER = ['OVERALL', 'REGION', 'ETHNICITY', 'SEX', 'GENDERID', 'PARTYID', 'AGE', 'INCOME', 'EDUCATION', ]

SEGMENT_REPLACE_LOOKUP = {
    'STATE': 'OVERALL',
    'ASIAN': 'ASIAN',
    'BLACK': 'BLACK',
    'HISPANIC': 'HISPANIC',
    'OTHER': 'OTHER',
    'REFUSED': 'REFUSED',
    'WHITE': 'WHITE',
    'MALE': 'Men',
    'FEMALE': 'Women',
    'DFL/DEMOCRAT': 'DFL / Democrat',
    'DEM/DFL': 'DFL / Democrat',
    'DEMOCRAT': 'DFL / Democrat',
    'REP': 'Republican',
    'REPUBLICAN': 'Republican',
    'IND': 'Independent / Other',
    'INDEPENDENT': 'Independent / Other',
    'INDEPENDENT/OTHER': 'Independent / Other',
    '18-34': '18-34',
    '35-49': '35-49',
    '50-64': '50-64',
    '65+': '65+',
    '<50': 'Under 50',
    '50+': '50+',
    'REF': 'REF',
    '<$50,000': 'Under $50,000',
    '$50,000+': '$50,000 and over',
    '<$25,000': '<$25,000',
    '$25,000-$49,999': '$25,000-$49,999',
    '$50,000-$74,999': '$50,000-$74,999',
    '$75,000-$99,999': '$75,000-$99,999',
    '$100,000+': '$100,000 and over',
    'HENNEPIN/RAMSEY': 'Hennepin / Ramsey',
    'METRO SUBURBS': 'Metro Suburbs',
    'SOUTHERN MN': 'Southern Minn.',
    'NORTHERN MN': 'Northern Minn.',
    'NO COLLEGE DEGREE': 'No college degree',
    'COLLEGE GRAD': 'College graduate',
    'HIGH SCHOOL/LESS': 'High school / less',
    'HIGH SCHOOL': 'High school / less',
    'SOME COLLEGE/VOC': 'Some college / vocational',
    'SOME COLLEGE': 'Some college / vocational',
    'GRAD DEGREE': 'Graduate degree',
    'REFUSED': 'Refused to answer',
#     'NOTSURE': 'Not sure',
}
SEGMENT_ORDER = list(SEGMENT_REPLACE_LOOKUP.keys())


def find_questions(results_output):
    question_finder = r'(?P<question>(?:[\w 0-9\?\/\-]+\n){1,4})(?P<remainder>\s+\-{2,})'
    questions = re.findall(question_finder, results_output)
    # print(questions)
    # question_finder = r'(Task number.+?)\*+\n\*+'
    # question_finder = r'^\s+([\w 0-9\?\-\/]+\n*[\w 0-9\?\-\/]*\n*[\w 0-9\?\-\/]*)\n\s+-+'
    # question_finder = r'(?P<question>(?:[\w 0-9\?\/\-]+\n){1,4})\s+\-{2,}'
    # question_finder_2 = r'(?P<question>(?:[\w 0-9\?\/\-]+\n){1,4})\s+\-{2,}(?P<remainder>.*?)(?:~|$)'
    # questions = re.findall(question_finder, results_output, re.DOTALL)
    starts = []
    records = []
    for q in questions:
        start_pos = results_output.index(q[0])
        starts.append(start_pos)
        question_clean = re.sub(r'(?:-{2,}|\s{2,})', ' ', re.sub(r'\n+', '', q[0])).strip()
        records.append({
            'question': question_clean,
            'q_remainder': q[1],
            'start_pos': start_pos
        })
        print(question_clean)

    for k, r in enumerate(records):
        if k == len(records) - 1:
            end_pos = len(results_output)
        else:
            end_pos = records[k + 1]['start_pos']
        r['full_text'] = results_output[r['start_pos']:end_pos]

    q_count = 0
    for r in records:
    #     print(r['full_text'])
    #     print('break break break')
        q_count += 1
    print(q_count)
    return records


def parse_question_answers(q_text):
    '''Potential answers are 1 or more lines of text between a row of ---- and and row of ==='''
#     print(q_text)
    q_answers_raw = re.search(r'-{2,}\s+\n(.+?)\n\s+=', q_text, re.DOTALL).group(1)
    q_answers_lines = q_answers_raw.split('\n')

    leading_spaces = re.match(r'(\s+).+', q_answers_lines[0]).group(1)

    q_answers_lines_stripped = []
    for row in q_answers_lines:
        row = re.sub(r'^{}'.format(leading_spaces), '', row)
        q_answers_lines_stripped.append(row)

    row_item_regex = r'(\w+(?:\s{2,}|$))'
    first_row_items_raw = re.findall(row_item_regex, q_answers_lines_stripped[0])

    # Get length of each cell in first row
    cell_lens = [len(cell) for cell in first_row_items_raw]

    # Start a clean list of cell names with first line
    q_answers_lines_parsed = [i.strip() for i in first_row_items_raw]

    for row in q_answers_lines_stripped[1:]:
        start_char = 0
        for key, le in enumerate(cell_lens):
            q_answers_lines_parsed[key] += (row[start_char:start_char + le]).strip()
            start_char += le

    return q_answers_lines_parsed


def parse_table(table_text, choices):
    # Items in a table body have two line breaks between them
    lines = re.split(r'\n\s+\n', table_text)
    # print(lines)
    table_data = []
    for l in lines:
        # First row is raw counts, second row is percentages
        if l != '':
            line_label = re.search(r'(.+?)\s{2,}', l).group(1)
            raw_row = re.split('\n', l)[0]
            pct_row = re.split('\n', l)[1]
#             print(line_label, raw_row, pct_row)

            raw_row_data = re.findall(r'\s+(\d+)', raw_row)
            pct_row_data = re.findall(r'\s+([\d\.]+)', pct_row)
#             print(raw_row_data, pct_row_data)

#             line_data_tagged = []
#             for k, cell in enumerate(raw_row_data):
#                 line_data_tagged.append({'choice': choices[k]})

#             line_data = re.findall(r'\s{2,}([\d\.]+)', l)
            line_data_tagged = [{'choice': choices[k], 'count': cell, 'pct': pct_row_data[k]} for k, cell in enumerate(raw_row_data)]
            table_data.append({
                'segment': line_label,
                'data': line_data_tagged
            })
    return table_data


def parse_segments(q_text, q_choices):
    # Find segment headers and content of results table
    segment_finder = r'([\w\s]+)\n-{2,}\n(.*?)(?:(?:\n\s){2,}|$)'
#     segment_finder = r'\n([\w\s]+)\n-+\n(.+?(?=~|\Z))'
    segments = re.findall(segment_finder, q_text, re.DOTALL)
#     print(segments)
    segment_list = []
    for s in segments:
        cleaned_seg_name = re.sub(r'[\n ]', '', s[0])
        segment_name = 'OVERALL' if cleaned_seg_name == 'RESULTS' else cleaned_seg_name
        print('segname: {}'.format(cleaned_seg_name))
        print(s)
        segment_list.append({
            'segment_name': segment_name,
            'table_data': parse_table(s[1], q_choices)
        })
    return segment_list


# Change order
def assign_order(value, ordering_keys):
    return ordering_keys[value]


# Make Strib style
def reformat_segment(value):
    return SEGMENT_REPLACE_LOOKUP[value]


def make_dataframe(q_title, q_choices, q_segments):
#     print(q_segments)
    df = pd.DataFrame()
    for segment_type in q_segments:
        segment_name = segment_type['segment_name']
        for segment in segment_type['table_data']:
            seg_df = pd.DataFrame(segment['data'])
            print(segment['segment'])
            print(segment)
            display(seg_df)
            seg_df['count'] = seg_df['count'].astype(int)
            seg_df['pct'] = seg_df['pct'].astype(float)
            seg_df['segment'] = segment['segment']
            seg_df['breakdown'] = segment_name
            df = df.append(seg_df)

    # TODO: Pivot to video, er, Strib style
#     pt = df.pivot_table(['count', 'pct'], ['breakdown', 'segment'], 'choice').reset_index()
    count_pt = df.pivot_table('count', ['breakdown', 'segment'], 'choice').reset_index()
    pct_pt = df.pivot_table('pct', ['breakdown', 'segment'], 'choice').reset_index()

    display(count_pt)
    display(pct_pt)
    merged_pt = count_pt.merge(
        pct_pt,
        how="left",
        on=['breakdown', 'segment']
    )
    merged_pt.columns = merged_pt.columns.str.replace("_x", "_count")
    merged_pt.columns = merged_pt.columns.str.replace("_y", "_pct")

    breakdown_ordering_keys = {v: k for k, v in enumerate(BREAKDOWN_ORDER)}
    segment_ordering_keys = {v: k for k, v in enumerate(SEGMENT_ORDER)}
    merged_pt['breakdown_order'] = merged_pt.breakdown.apply(assign_order, args=(breakdown_ordering_keys,))
    merged_pt['segment_order'] = merged_pt.segment.apply(assign_order, args=(segment_ordering_keys,))
    merged_pt.sort_values(['breakdown_order', 'segment_order'], inplace=True)

    merged_pt['segment'] = merged_pt.segment.map(reformat_segment)

    # Drop temp columns
    merged_pt.drop(columns=['breakdown_order', 'segment_order'], inplace=True)

    display(merged_pt)

    # Add "raw" columns and round orig columns
#     print(q_choices)
#     for c in q_choices:
#         pt['{}_raw'.format(c)] = pt[c]
#         pt[c] = pt[c].astype("float").round()
    return merged_pt


def format_value(str_input, add_pct):
    pct_value = '%' if add_pct else ''
    return '{}{}'.format(str(round(float(str_input))), pct_value)


def build_topline_chart(segments):
    html = ''
    chart_data = segments['table_data'][0]['data']
    header_items = ['<td class="label" width="{}">{}</td>'.format(format_value(dp['value'], True), dp['choice']) for dp in chart_data]
    header = '<tr>{}</tr>'.format(''.join(header_items))

    body_items = ['<td class="bar" width="{}">{}</td>'.format(format_value(dp['value'], True), format_value(dp['value'], True)) for dp in chart_data]
    body = '<tr>{}</tr>'.format(''.join(body_items))
    return '\n<table class="stacked-bar-graph"><tbody>\n{}\n{}\n</tbody></table>\n'.format(header, body)


def build_topline_chart_df(q_choices, df):
    html = ''

    header_items = ['<td class="label" width="{}">{}</td>\n'.format(df['{}_pct'.format(choice)], choice.title()) for choice in q_choices]
    header = '<tr>\n{}</tr>\n'.format(''.join(header_items))

    body_items = ['<td class="bar" width="{}">{}</td>\n'.format(format_value(df['{}_pct'.format(choice)], True), format_value(df['{}_pct'.format(choice)], True)) for choice in q_choices]
    body = '<tr>{}</tr>'.format(''.join(body_items))
    return '\n<table class="stacked-bar-graph"><tbody>\n{}\n{}\n</tbody></table>\n'.format(header, body)


def add_pct(row):
    if row.name == 0:
        return row.apply(lambda x: '{}%'.format(str(int(x))))
    return row.apply(lambda x: str(int(x)))

def build_question_html_df(q_title, q_choices, q_df):
    h_df = q_df.copy()

    # Build topline (first row) into chart
    topline_df = h_df.iloc[0]
    topline_chart = build_topline_chart_df(q_choices, topline_df)

    # Remove first row since it's in chart
    h_df = h_df.drop(h_df.index[0]).reset_index().drop(columns=["index"])

    # Remove REF row
    h_df = h_df[h_df['segment'] != 'REF']

    # Drop raw columns
    h_df = h_df[h_df.columns.drop(list(h_df.filter(regex='_raw')))]

    # Apply % to new first row
    q_choices_lookup = ['{}_pct'.format(c) for c in q_choices]
    h_df[q_choices_lookup] = h_df[q_choices_lookup].apply(add_pct, axis=1)

    html = '<thead>\n<tr><th>&nbsp;</th><th>{}</th></tr>\n</thead>\n'.format('</th><th>'.join([choice.title() for choice in q_choices]))
    for breakdown in BREAKDOWN_ORDER:
        if breakdown not in 'OVERALL':
            for index, row in h_df[h_df['breakdown'] == breakdown].copy().reset_index().iterrows():
                choice_values = [str(row[x]) for x in q_choices_lookup]
                if index == h_df[h_df['breakdown'] == breakdown].shape[0] - 1:
                    tr_class = ' class="last_line"'
                else:
                    tr_class = ''
                html += '<tr{}><th scope="row">{}</th><td>{}</td></tr>\n'.format(tr_class, row['segment'], '</td><td>'.join(choice_values))

    return '<h2>{}</h2>\n{}<table class="poll-question">\n<tbody>\n{}</tbody>\n</table>\n'.format(q_title, topline_chart, html)
