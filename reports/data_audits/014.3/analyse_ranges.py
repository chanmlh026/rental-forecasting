"""Offline ASHE predecessor range research. No network or production outputs."""

import argparse
import hashlib
import io
import json
import math
import zipfile
from collections import Counter
from decimal import Decimal
from pathlib import Path

import openpyxl
import pandas as pd
import xlrd

BASE = Path(__file__).resolve().parents[3]
OUT = BASE / 'reports/data_audits/014.3'


def sha(body):
    return hashlib.sha256(body).hexdigest()


def clean(value):
    if value is None or isinstance(value, float) and math.isnan(value):
        return None
    return value.item() if hasattr(value, 'item') else value


def read_all(name, body):
    if name.endswith('.xlsx'):
        book = openpyxl.load_workbook(io.BytesIO(body), data_only=False, read_only=True)
        rows = list(book['All'].values)
        book.close()
        return rows
    sheet = xlrd.open_workbook(file_contents=body).sheet_by_name('All')
    return [sheet.row_values(i) for i in range(sheet.nrows)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path,
                        help='Existing checkout containing the Task 009.2 outputs and Task 009.1 raw bundles')
    args = parser.parse_args()
    roster = json.loads((OUT / 'predecessors.json').read_text())
    snapshot = args.source_root / 'data/processed/ons_ashe/snapshot=2026-11-21-task009-2'
    manifest_body = (snapshot / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_body)
    before = {name: sha((snapshot / name).read_bytes()) for name in manifest['checksums']}
    assert before == manifest['checksums']
    frame = pd.read_parquet(snapshot / 'observations.parquet')
    frame = frame.loc[frame.observation_year.between(2015, 2023)].copy()
    assert (frame.unit == 'GBP/year').all() and (frame.source_sheet == 'All').all()
    names = {r.source_code: str(r.source_name).strip() for r in frame.itertuples() if r.source_code}
    all_codes = set()
    for authority in roster['authorities']:
        all_codes.update(authority['predecessors'])
        all_codes.update(authority.get('before_2019', []))
        all_codes.add(authority['code'])
        if authority.get('county_comparator'):
            all_codes.add(authority['county_comparator'])
    assert not frame.loc[frame.source_code.isin(all_codes)].duplicated(['source_edition_id', 'source_code']).any()
    observations, editions, direct_verified = {}, {}, 0
    keep = ['source_row', 'cv_source_row', 'source_name', 'source_code_raw', 'source_code',
            'annual_gross_median_gbp', 'pay_source_text', 'pay_marker', 'pay_state',
            'median_cv_percent', 'cv_source_text', 'cv_marker', 'cv_state',
            'pay_style_json', 'cv_style_json', 'reference_period_start', 'reference_period_end',
            'population_note_conflict']
    for edition, group in frame.groupby('source_edition_id', sort=True):
        first = group.iloc[0]
        metadata = {key: clean(first[key]) for key in ['observation_year', 'source_edition_label',
                    'source_edition_status', 'source_url', 'source_sha256', 'pay_workbook', 'cv_workbook',
                    'pay_workbook_sha256', 'cv_workbook_sha256', 'source_release_date', 'availability_evidence']}
        basename = str(first.source_url).split('/')[-1]
        candidates = [args.source_root / 'data/raw/ashe-009-1-investigation' / (basename + suffix) / 'response.bin'
                      for suffix in ['', '.retry1']]
        body = next(p.read_bytes() for p in candidates if p.exists() and sha(p.read_bytes()) == first.source_sha256)
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            pay, cv = z.read(first.pay_workbook), z.read(first.cv_workbook)
        assert sha(pay) == first.pay_workbook_sha256 and sha(cv) == first.cv_workbook_sha256
        pay_rows, cv_rows = read_all(first.pay_workbook, pay), read_all(first.cv_workbook, cv)
        assert pay_rows[4][3] == cv_rows[4][3] == 'Median'
        title = ' '.join(str(v) for v in pay_rows[0] if v)
        assert 'Annual pay - Gross' in title and 'all employee jobs' in title
        for _, row in group.loc[group.source_code.isin(all_codes)].iterrows():
            pay_cell = pay_rows[int(row.source_row) - 1]
            cv_cell = cv_rows[int(row.cv_source_row) - 1]
            assert str(pay_cell[1]).strip().lstrip("'") == row.source_code
            assert str(cv_cell[1]).strip().lstrip("'") == row.source_code
            assert str(pay_cell[0]).strip() == str(row.source_name).strip()
            for actual, value, marker, state in [(pay_cell[3], row.annual_gross_median_gbp, row.pay_marker, row.pay_state),
                                                  (cv_cell[3], row.median_cv_percent, row.cv_marker, row.cv_state)]:
                if state == 'numeric':
                    assert isinstance(actual, (int, float)) and float(actual) == float(value)
                else:
                    assert str(actual or '').strip() == str(clean(marker) or '').strip()
                direct_verified += 1
            key = f'{edition}:{int(row.source_row)}'
            observations[key] = {k: clean(row[k]) for k in keep}
            observations[key].update(edition=edition, pay_cell=f'All!D{int(row.source_row)}',
                                     cv_cell=f'All!D{int(row.cv_source_row)}')
        metadata['title'] = title
        editions[edition] = metadata
    by_identity = {(o['edition'], o['source_code']): key for key, o in observations.items()}
    results, comparators = [], []
    special_path = BASE / 'reports/data_audits/014.2/coverage-evidence.json'
    special = json.loads(special_path.read_text(encoding='utf-8'))['special_2019_boundaries']

    def analyse(authority, edition, expected, role):
        meta = editions[edition]
        year = int(meta['observation_year'])
        available, absent, nonnumeric = [], [], []
        for code in expected:
            key = by_identity.get((edition, code))
            if key is None:
                absent.append(code)
            elif observations[key]['pay_state'] == 'numeric':
                available.append(key)
            else:
                nonnumeric.append(key)
        values = [Decimal(str(observations[k]['annual_gross_median_gbp'])) for k in available]
        lo, hi = (min(values), max(values)) if values else (None, None)
        span = hi-lo if len(values) >= 2 else None
        complete = len(values) == len(expected)
        result = dict(authority=authority['code'], name=authority['name'], year=year, edition=edition,
                      role=role, period='pre_reorganisation' if year < int(authority['reorganisation_date'][:4]) else 'transition_year',
                      expected_codes=expected, expected_count=len(expected), numeric_observations=available,
                      nonnumeric_observations=nonnumeric, absent_codes=absent, valid_count=len(values),
                      complete=complete, minimum_gbp=float(lo) if lo is not None else None,
                      maximum_gbp=float(hi) if hi is not None else None,
                      observed_span_gbp=float(span) if span is not None else None,
                      observed_span_percent_min=float(span/lo*100) if span is not None and lo>0 else None,
                      range_status='complete' if complete else 'partial_observed_subset' if len(values)>=2 else 'unassessable_fewer_than_two',
                      geography='statutory roster; native source geography retained; no harmonisation')
        results.append(result)
        candidates = [authority['code']] + ([authority['county_comparator']] if authority.get('county_comparator') else [])
        for code in candidates:
            key = by_identity.get((edition, code))
            if key and observations[key]['pay_state'] == 'numeric':
                value = observations[key]['annual_gross_median_gbp']
                comparators.append(dict(authority=authority['code'], year=year, predecessor_edition=edition,
                                        role=role, kind='same_edition_county' if code != authority['code'] else 'same_edition_new_authority',
                                        observation=key, combined_value_gbp=value,
                                        complete_predecessors=complete,
                                        inside_observed_interval=lo<=Decimal(str(value))<=hi if lo is not None else None,
                                        interpretation='potential descriptive benchmark; not an approximation accuracy estimate'))
        for entry in special:
            if entry['kind'] != 'pay' or entry['year'] != year:
                continue
            row = next((r for r in entry['rows'] if r['code'] == authority['code']), None)
            if row:
                comparators.append(dict(authority=authority['code'], year=year, predecessor_edition=edition,
                                        role=role, kind='special_april_2019_boundaries_cross_publication',
                                        member=entry['member'], cell=row['cell'], member_sha256=entry['member_sha256'],
                                        combined_value_gbp=row['median'], complete_predecessors=complete,
                                        inside_observed_interval=lo<=Decimal(str(row['median']))<=hi if lo is not None else None,
                                        interpretation='cross-publication descriptive overlap only; revisions/processing may differ'))

    for authority in roster['authorities']:
        stop = int(authority['reorganisation_date'][:4])
        for edition, meta in sorted(editions.items(), key=lambda x:(x[1]['observation_year'], x[0])):
            year = int(meta['observation_year'])
            if year > stop:
                continue
            expected = authority.get('before_2019', authority['predecessors']) if year < 2019 else authority['predecessors']
            analyse(authority, edition, expected, 'calendar_date_roster')
            # Retain the distinct retrospectively regrouped Somerset roster without filling missing old districts.
            if authority['name']=='Somerset' and year==2018 and (edition, 'E07000246') in by_identity:
                analyse(authority, edition, authority['predecessors'], 'later_roster_source_vintage_supplement')
    # Cross-edition overlap for new authorities does not establish approximation accuracy.
    for result in list(results):
        if not result['complete']:
            continue
        for key, o in observations.items():
            if o['source_code']==result['authority'] and o['edition']!=result['edition'] and o['pay_state']=='numeric' and int(editions[o['edition']]['observation_year'])==result['year']:
                comparators.append(dict(authority=result['authority'], year=result['year'],
                                        predecessor_edition=result['edition'], role=result['role'], kind='new_authority_other_edition',
                                        observation=key, combined_value_gbp=o['annual_gross_median_gbp'], complete_predecessors=True,
                                        inside_observed_interval=result['minimum_gbp']<=o['annual_gross_median_gbp']<=result['maximum_gbp'],
                                        interpretation='not a clean validation pair: publication edition and geography assignment differ'))
    evidence=dict(definition='Table 8.7a All median gross annual residence pay; GBP/year; no combined median reconstructed',
                  input_parquet_sha256=before['observations.parquet'], manifest_sha256=sha(manifest_body),
                  task0142_comparator_evidence_sha256=sha(special_path.read_bytes()),
                  predecessor_roster_sha256=sha((OUT/'predecessors.json').read_bytes()),
                  editions=editions, source_observations=observations, ranges=results, comparators=comparators)
    (OUT/'range-evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# Predecessor median ranges by source edition', '',
           'All amounts are GBP/year. P/R labels are source editions, not a modelling-vintage policy.',
           'Partial spans describe observed predecessors only. Fewer than two numeric medians gives no span.',
           'The reorganisation year is a transition supplement. Somerset 2018 later-roster supplement is separate.', '',
           '| Authority | Year | Edition | Roster | Numeric / expected | Min | Max | Span GBP | Span % of min | Coverage | Non-numeric codes / markers | Absent source codes |',
           '|---|---:|---|---|---|---:|---:|---:|---:|---|---|---|']
    def fmt(v):
        return '—' if v is None else f'{v:,.2f}'
    for row in results:
        marks=', '.join(observations[k]['source_code']+':'+str(observations[k]['pay_marker'] or observations[k]['pay_state']) for k in row['nonnumeric_observations']) or '—'
        label='calendar' if row['role']=='calendar_date_roster' else 'later roster'
        lines.append(f"| {row['name']} | {row['year']} | {row['edition']} | {label} | {row['valid_count']}/{row['expected_count']} | {fmt(row['minimum_gbp'])} | {fmt(row['maximum_gbp'])} | {fmt(row['observed_span_gbp'])} | {fmt(row['observed_span_percent_min'])} | {row['range_status']} | {marks} | {', '.join(row['absent_codes']) or '—'} |")
    (OUT/'ranges-by-edition.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    after={name:sha((snapshot/name).read_bytes()) for name in before}
    assert before==after and sha((snapshot/'manifest.json').read_bytes())==sha(manifest_body)
    validation=dict(status='pass', source_snapshot_files_unchanged=len(before)+1,
                    source_editions_verified=len(editions), independent_raw_pay_cv_cells=direct_verified,
                    source_observation_records=len(observations), range_records=len(results),
                    range_statuses=dict(Counter(r['range_status'] for r in results)),
                    no_network_code=True, no_production_outputs=True)
    (OUT/'validation-evidence.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(validation,indent=2))


if __name__=='__main__':
    main()
