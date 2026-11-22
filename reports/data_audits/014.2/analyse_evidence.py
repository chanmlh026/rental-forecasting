"""Replay the small research evidence, without mapping or constructing model inputs."""

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import openpyxl
import xlrd

BASE = Path(__file__).resolve().parents[3]
OUT = BASE / 'reports/data_audits/014.2'
RAW = BASE / 'data/raw/ashe-014-2-investigation'
CODES = {'E06000058', 'E06000059', 'E06000060', 'E06000061', 'E06000062',
         'E06000063', 'E06000064', 'E06000065', 'E06000066', 'E07000244', 'E07000245'}


def digest(body):
    return hashlib.sha256(body).hexdigest()


def sheets(name, body):
    if name.endswith('.xlsx'):
        book = openpyxl.load_workbook(io.BytesIO(body), data_only=False, read_only=True)
        return {s.title: list(s.values) for s in book}
    book = xlrd.open_workbook(file_contents=body)
    return {s.name: [s.row_values(i) for i in range(s.nrows)] for s in book.sheets()}


def source_rows(book):
    rows = book['All']
    assert rows[4][3] == 'Median'
    title = ' '.join(str(v) for v in rows[0] if v)
    assert 'Annual pay - Gross' in title and 'all employee jobs' in title
    found = []
    for i, row in enumerate(rows, 1):
        code = str(row[1] or '').strip().lstrip("'")
        if code in CODES or str(row[0]).strip() in {'Buckinghamshire', 'North Yorkshire', 'Dorset', 'Somerset'}:
            found.append(dict(row=i, name=row[0], code=code, median=row[3], cell=f'All!D{i}'))
    notes = [dict(sheet=s, row=i, text=' '.join(str(v) for v in row if v).strip())
             for s, rows in book.items() if s in {'All', 'Notes'}
             for i, row in enumerate(rows, 1)
             if any(w in ' '.join(str(v) for v in row).lower()
                    for w in ['boundar', 'geograph', 'annual estimates', 'adult rates', 'ad hoc', 'query in'])]
    return title, found, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-root', type=Path)
    args = parser.parse_args()
    access = json.loads((OUT / 'access-evidence.json').read_text())
    for r in access:
        b = (RAW / r['name']).read_bytes()
        assert digest(b) == r['sha256'] and len(b) == r['bytes']

    # The original audit is inspected read-only. Cache only the small evidence subset.
    original_path = RAW / 'existing-ons-evidence.json'
    if args.original_root:
        previous = args.original_root
        extracts_path = previous / 'data/raw/ashe-009-1-investigation/selected-field-extracts.json'
        extracts = json.loads(extracts_path.read_text())
        fields = json.loads((previous / 'reports/data_audits/009.1/field-evidence.json').read_text())
        access_old = json.loads((previous / 'reports/data_audits/009.1/access-evidence.json').read_text())
        editions = []
        for extract, field in zip(extracts, fields, strict=True):
            if extract['year'] < 2015:
                continue
            match = next(a for a in access_old if a['url'] == extract['source'])
            metadata = match['metadata']
            expected = metadata['checksums']['response.bin']
            basename = extract['source'].split('/')[-1]
            candidates = [previous / 'data/raw/ashe-009-1-investigation' / (basename + suffix) / 'response.bin'
                          for suffix in ['', '.retry1']]
            body = next(p.read_bytes() for p in candidates if p.exists() and digest(p.read_bytes()) == expected)
            with zipfile.ZipFile(io.BytesIO(body)) as archive:
                member = field['pay']['workbook']
                pay = archive.read(member)
                assert digest(pay) == field['pay']['sha256']
                title, rows, notes = source_rows(sheets(member, pay))
                for row in rows:
                    prior = next(r for r in extract['rows'] if r['row'] == row['row'])
                    assert prior['code'] == row['code'] and prior['median'] == row['median']
                editions.append(dict(year=extract['year'], edition=extract['edition'], url=extract['source'],
                                     zip_sha256=expected, member=member, member_sha256=digest(pay),
                                     title=title, rows=rows, notes=notes))
        original = dict(prior_extract_sha256=digest(extracts_path.read_bytes()), editions=editions)
        original_path.write_text(json.dumps(original, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    original = json.loads(original_path.read_text(encoding='utf-8'))

    special = []
    with zipfile.ZipFile(RAW / 'special-residence.zip') as archive:
        for year in [2015, 2016, 2017]:
            for tag in ['7a', '7b']:
                member = next(n for n in archive.namelist() if f'.{tag}   Annual pay - Gross {year}' in n)
                body = archive.read(member)
                title, rows, notes = source_rows(sheets(member, body))
                special.append(dict(year=year, kind='pay' if tag == '7a' else 'cv_percent', member=member,
                                    member_sha256=digest(body), title=title,
                                    rows=[r for r in rows if r['code'] in {'E06000058', 'E06000059', 'E07000244', 'E07000245'}],
                                    notes=notes))
    assert all(len(s['rows']) == 4 for s in special)

    nomis = {}
    for filename in ['initial.csv', 'all-authorities.csv', 'district-authorities.csv',
                     'authorities-432.csv', 'authorities-434.csv']:
        rows = list(csv.DictReader((RAW / filename).read_text().splitlines()))
        assert len({(r['GEOGRAPHY'], r['DATE']) for r in rows}) == len(rows)
        assert all((r['SEX'], r['PAY'], r['ITEM'], r['MEASURES']) == ('7', '7', '2', '20100') for r in rows)
        assert all(r['OBS_STATUS'] in {'A', 'Q'} for r in rows)
        assert all(bool(r['OBS_VALUE']) == (r['OBS_STATUS'] == 'A') for r in rows)
        nomis[filename] = rows
    assert len(nomis['initial.csv']) == 15
    assert len(nomis['district-authorities.csv']) == 121
    lookup = {(r['GEOGRAPHY_CODE'], r['DATE']): r for r in nomis['all-authorities.csv']}
    for row in nomis['district-authorities.csv']:
        prior = lookup[row['GEOGRAPHY_CODE'], row['DATE']]
        assert (row['OBS_VALUE'], row['OBS_STATUS']) == (prior['OBS_VALUE'], prior['OBS_STATUS'])
    for row in nomis['initial.csv']:
        prior = lookup[row['GEOGRAPHY_CODE'], row['DATE']]
        assert row['OBS_VALUE'] == prior['OBS_VALUE'] and row['OBS_STATUS'] == prior['OBS_STATUS']

    # Exact source identities only; no predecessor-to-current mapping or aggregation.
    comparisons = []
    for query, records in nomis.items():
        if query in {'initial.csv', 'all-authorities.csv'}:
            continue
        for row in records:
            if row['OBS_STATUS'] != 'A':
                continue
            for edition in original['editions']:
                if str(edition['year']) != row['DATE']:
                    continue
                for source in edition['rows']:
                    if source['code'] == row['GEOGRAPHY_CODE'] and isinstance(source['median'], (int, float)):
                        comparisons.append(dict(query=query, year=row['DATE'], code=source['code'],
                                                nomis_value=row['OBS_VALUE'], ons_edition=edition['edition'],
                                                ons_value=source['median'], cell=source['cell'],
                                                difference=float(row['OBS_VALUE'])-source['median']))
    evidence = dict(definition=dict(dataset='NM_30_1', sex=7, pay=7, item=2, measures=20100,
                                   population='All employee jobs, both sexes, FT and PT; residence', unit='GBP per year'),
                    nomis={name: [{k: r[k] for k in [
                        'DATE', 'GEOGRAPHY', 'GEOGRAPHY_NAME', 'GEOGRAPHY_CODE', 'GEOGRAPHY_TYPECODE',
                        'OBS_VALUE', 'OBS_STATUS', 'OBS_STATUS_NAME', 'OBS_CONF', 'OBS_CONF_NAME']}
                        for r in rows] for name, rows in nomis.items()}, special_2019_boundaries=special,
                    existing_ons=original, exact_identity_comparisons=comparisons,
                    geography_classification='Nomis numeric cells remain geography unverified; special extract verified April 2019 reference')
    (OUT / 'coverage-evidence.json').write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    result = dict(status='pass', raw_bodies_hash_verified=len(access), initial_cells=15,
                  current_district_cells=121, statuses=dict(Counter(r['OBS_STATUS'] for r in nomis['district-authorities.csv'])),
                  older_family_cells=sum(len(nomis[f'authorities-{t}.csv']) for t in [432,434]),
                  special_pay_cells=12, special_cv_cells=12,
                  existing_ons_editions=len(original['editions']), exact_identity_comparisons=len(comparisons),
                  comparison_equal=sum(c['difference']==0 for c in comparisons),
                  comparison_different=sum(c['difference']!=0 for c in comparisons),
                  raw_source_data_modified=False)
    (OUT / 'validation-evidence.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
