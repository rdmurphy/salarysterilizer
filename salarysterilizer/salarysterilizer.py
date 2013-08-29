import argparse
import json
import sys
from datetime import datetime

from name_cleaver import IndividualNameCleaver
from csvkit.unicsv import UnicodeCSVDictReader, UnicodeCSVDictWriter

def column_config(category, columns, rows):
    sys.stdout.write('\nExamples for {0}\n===\n'.format(category))
    if category != 'gender':
        for row in rows[:10]:
            print([row[k] for k in columns])
    else:
        gender_options = set()
        for row in rows:
            gender_options.add(row[columns[0]])
        for entry in gender_options:
            sys.stdout.write('{0}\n'.format(entry))

    options = {}

    if category == 'name':
        last_name_space = raw_input('Is there no separator between the last and first name? E.g. SMITH JOHN (y/n)\n')
        if last_name_space is 'Y':
            options['last_name_space'] = True

    if category == 'gender':
        male_is = raw_input('How are men identified? E.g. \'M\', \'Male\'\n')
        female_is = raw_input('How are women identified? E.g. \'F\', \'Female\'\n')

        options['male_is'] = male_is
        options['female_is'] = female_is

    if category == 'title':
        remove_anything = raw_input('Do any characters need to be stripped from this string? (y/n)\n')

        if remove_anything == 'Y':
            remove_before = int(raw_input('How many characters need to be removed from the beginning? (expects a number)\n'))
            remove_after = int(raw_input('How many characters need to be removed from the end? (expects a number)\n'))

            if remove_before > 0:
                options['remove_before'] = remove_before

            if remove_after > 0:
                options['remove_after'] = remove_after

    if category == 'department':
        remove_anything = raw_input('Do any characters need to be stripped from this string? (y/n)\n')

        if remove_anything == 'Y':
            remove_before = int(raw_input('How many characters need to be removed from the beginning? (expects a number)\n'))
            remove_after = int(raw_input('How many characters need to be removed from the end? (expects a number)\n'))

            if remove_before > 0:
                options['remove_before'] = remove_before

            if remove_after > 0:
                options['remove_after'] = remove_after

    if category == 'hire_date':
        date_format = raw_input('How is the date formatted? (Use Python date formatting conventions)\n')
        options['date_format'] = date_format

    if category == 'salary':
        sys.stdout.write('Don\'t worry! Dollar signs and commas will be automatically removed.\n')

    return options


def generate_template(header, rows, filename):
    column_matches = {}

    for category in ('name', 'gender', 'title', 'department', 'hire_date', 'salary'):
        sys.stdout.write('\n')
        for i, v in enumerate(header):
            sys.stdout.write('{0}: {1}\n'.format(i, v))

        ids = raw_input('Which column index(es) represent an employee\'s {0}? (comma separated, in order)\n'.format(category))
        columns = [header[int(x)] for x in ids.split(',')]
        options = column_config(category, columns, rows)

        column_matches[category] = {
            'columns': columns,
            'options': options
        }

    column_matches['entity_name'] = raw_input('Finally, what is the proper title for this entity? (e.g. Austin ISD)\n')
    column_matches['entity_type'] = raw_input('What type of entity is this? (e.g. School District)\n')
    column_matches['received_date'] = raw_input('When was this data received from the agency? (e.g. 7/22/2013)\n')

    with open('template.json', 'wb') as fo:
        fo.write(json.dumps(column_matches, indent=2))

    sys.stdout.write('Template for {0} written to template.json'.format(filename))


def prepare_csv_for_reading(filename):
    with open(filename, 'rb') as f:
        reader = UnicodeCSVDictReader(f)
        payload = {
            'rows': [i for i in reader],
            'header': reader.fieldnames
        }

    return payload


def name(s, **kwargs):
    if not ' ' in s and ',' in s:  # fix for wonkiness in name_cleaver
        s = s.replace(',', ', ').strip()

    if 'last_name_space' in kwargs:
        first_space = s.find(' ')
        l = list(s)

        l[first_space] = ', '
        s = ''.join(l)

    name = IndividualNameCleaver(s).parse()

    return unicode(name)


def salary(n, **kwargs):
    n = n.replace('$', '').replace(',', '')

    try:
        return float(n)
    except ValueError:
        return 0.00


def hire_date(d, **kwargs):
    processed_date = datetime.strptime(d, kwargs['date_format']).date()
    return processed_date.strftime('%m/%d/%Y')


def title_department(s, **kwargs):
    if 'remove_before' in kwargs:
        s = s[kwargs['remove_before']:]

    if 'remove_after' in kwargs:
        s = s[:-kwargs['remove_after']]

    return unicode(s.strip())


def gender(s, **kwargs):
    if s.strip() == kwargs['male_is']:
        return 'M'

    if s.strip() == kwargs['female_is']:
        return 'F'

    return unicode(s.strip())


def entity(s, **kwargs):
    return unicode(s)


def collect_cells(row, columns):
    payload = ''
    for column in columns:
        payload += row[column] + ' '

    return payload.strip()


def process_csv(csv_data, template):

    standard_header = [
        'name',
        'gender',
        'title',
        'department',
        'hire_date',
        'salary',
        'entity',
        'type',
        'received_date',
    ]

    file_name = template['entity_name'].lower().replace(' ', '_')

    with open('{0}-ready.csv'.format(file_name), 'wb') as fo:
        writer = UnicodeCSVDictWriter(fo, standard_header)
        writer.writeheader()

        for row in csv_data['rows']:
            writer.writerow({
                'name': name(collect_cells(row, template['name']['columns']), **template['name']['options']),
                'gender': gender(collect_cells(row, template['gender']['columns']), **template['gender']['options']),
                'title': title_department(collect_cells(row, template['title']['columns']), **template['title']['options']),
                'department': title_department(collect_cells(row, template['department']['columns']), **template['department']['options']),
                'hire_date': hire_date(collect_cells(row, template['hire_date']['columns']), **template['hire_date']['options']),
                'salary': salary(collect_cells(row, template['salary']['columns']), **template['salary']['options']),
                'entity': template['entity_name'],
                'type': template['entity_type'],
                'received_date': template['received_date'],
            })

        sys.stdout.write('File processed.\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='the salary csv file that needs cleaning')
    parser.add_argument('-g', '--generate_template',
                        help='only generate a cleaning template (not execute it)',
                        action='store_true')
    parser.add_argument('-t', '--template', help='use a pre-existing template.json file')
    args = parser.parse_args()

    csv_data = prepare_csv_for_reading(args.filename)

    if not args.template:
        try:
            with open('template.json'):
                sys.stdout.write('You already have a template.json file! Pass it in using -t, or delete it to regenerate.\n')
                return
        except IOError:
           generate_template(csv_data['header'], csv_data['rows'], args.filename)

    if args.generate_template:
        return

    process_csv(csv_data, json.load(open('template.json', 'rb')))


if __name__ == '__main__':
    main()
