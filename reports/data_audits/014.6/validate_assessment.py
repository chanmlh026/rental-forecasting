"""Independent raw-CSV reconciliation of the planning research outputs; offline."""

import argparse
import csv
import hashlib
import gzip
import io
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'reports/data_audits/014.6'


def csv_rows(path):
    if not path.exists() and path.with_suffix(path.suffix + '.gz').exists():
        path = path.with_suffix(path.suffix + '.gz')
    with (gzip.open(path, 'rt', newline='', encoding='utf-8-sig')
          if path.suffix == '.gz' else path.open(newline='', encoding='utf-8-sig')) as f:
        return list(csv.DictReader(f))


def numeric(token):
    return token not in ['', '..']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads((OUT / 'assessment-summary.json').read_text())
    # Original file hashes, including every processed output and retained raw body.
    for name, digest in summary['input_hashes'].items():
        normalized = name.replace('\\', '/')
        path = args.source_root / normalized if normalized.startswith('data/') else ROOT / normalized
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    reference = csv_rows(ROOT / 'configs/ons_lad_apr2025_v2.csv')
    cohort = {r['gss_code'] for r in reference if r['target_eligible'] == 'true'}
    inventory = json.loads((ROOT / 'configs/mhclg_planning_sources.json').read_text())
    selected = summary['measures']
    native = {}; periods = {}; fields = {}; required_rows = 0
    for edition in selected:
        path = args.source_root / 'data/raw/mhclg_planning/snapshot=2026-11-22-task012' / edition / 'response.bin'
        body = path.read_bytes()
        contract = next(s for s in inventory['sources'] if s['edition_id'] == edition)
        assert hashlib.sha256(body).hexdigest() == contract['source_sha256']
        rows = list(csv.reader(io.StringIO(body.decode('cp1252'))))
        header = next(i for i, row in enumerate(rows) if row[:4] == ['Region','LPANM','LPACD','Quarter'])
        columns = rows[header]; count_fields = [c for c in columns[4:] if c != 'F_Year']
        fields[edition] = count_fields
        periods[edition] = {}
        for record, row in enumerate(rows[header+1:], start=header+2):
            if not row:
                continue
            r = dict(zip(columns,row)); quarter = r['Quarter'].replace(' ','')
            if '2015Q1' <= quarter <= '2026Q2':
                native[edition, record] = r
                periods[edition].setdefault(quarter, set()).add(r['LPACD'])
                required_rows += 1
        assert len(periods[edition]) == 46
        assert sum(len(cohort - codes) for codes in periods[edition].values()) == 271
    audit = csv_rows(OUT / 'source-authority-quarters.csv')
    assert len(audit) == required_rows == 30002
    raw_cells = 0
    per_field_numeric = Counter()
    for r in audit:
        source = native[r['edition'], int(r['source_record'])]
        assert (r['code'],r['name'],r['native_quarter']) == (source['LPACD'],source['LPANM'],source['Quarter'])
        for field in selected[r['edition']]:
            assert r[field] == source[field]
            raw_cells += 1
        assert int(r['numeric_count_fields']) == sum(numeric(source[f]) for f in fields[r['edition']])
        assert int(r['missing_count_fields']) == sum(not numeric(source[f]) for f in fields[r['edition']])
        for field in fields[r['edition']]:
            per_field_numeric[r['edition'],r['quarter'],field] += numeric(source[field])
    assert sum(len(v) for v in fields.values()) == 417
    availability = csv_rows(OUT / 'all-field-quarter-availability.csv')
    assert len(availability) == 417 * 46
    for r in availability:
        assert int(r['numeric_rows']) == per_field_numeric[r['edition'],r['quarter'],r['field']]
        assert int(r['numeric_rows']) + int(r['missing_rows']) == int(r['total_rows'])
    matrix = csv_rows(OUT / 'la-quarter-measure-coverage.csv')
    assert len(matrix) == 54096
    assert len({(r['code'],r['quarter'],r['edition'],r['measure']) for r in matrix}) == len(matrix)
    assert Counter(r['classification'] for r in matrix) == summary['classification_counts']
    assert not any(r['classification'] == 'Direct' for r in matrix)
    index = {}
    for (edition, record), row in native.items():
        index.setdefault((edition,row['LPACD'],row['Quarter'].replace(' ','')), []).append((record,row))
    for r in matrix:
        edition = r['edition']; field = r['measure']; code = r['code']; quarter = r['quarter']
        direct = index.get((edition,code,quarter), [])
        assert int(r['direct_numeric']) == sum(numeric(row[field]) for rec,row in direct)
        assert int(r['direct_missing']) == sum(not numeric(row[field]) for rec,row in direct)
        expected_ids = {str(rec) for rec,row in direct}
        assert set(filter(None,r['direct_records'].split(';'))) == expected_ids
        if r['classification'] == 'Additive':
            assert code in ['E06000001','E06000002','E06000057']
            assert code != 'E06000057' or quarter >= '2022Q2'
            assert code == 'E06000057' or quarter >= '2023Q3'
            parts = r['required_partition_codes'].split(';')
            assert len(parts) == 2
            for part in parts:
                rows = index[edition,part,quarter]
                assert len(rows) == 1 and numeric(rows[0][1][field])
        for p in filter(None,r['predecessor_numeric_codes'].split(';')):
            assert any(numeric(row[field]) for rec,row in index[edition,p,quarter])
    mismatches = csv_rows(OUT / 'historical-code-mismatches.csv')
    for r in mismatches:
        assert r['code'] not in periods[r['edition']][r['quarter']]
    assert len(mismatches) == 542
    latest = csv_rows(OUT / 'latest-la-relationships.csv')
    assert len(latest) == len({r['code'] for r in latest}) == 294
    result = dict(status='pass with explicit geographical evidence limitations',
        independent_original_csv_selected_cells=raw_cells,
        independent_source_authority_quarters=len(audit),
        all_native_count_field_availability_checked=417,
        independently_checked_la_quarter_measure_rows=len(matrix),
        independently_reconciled_code_mismatches_per_asset=271,
        original_source_manifest_and_output_hashes_rechecked=len(summary['input_hashes']),
        geography_validation='Documentary relationships and classification preconditions checked; no independent polygon/lookup certification. 245 LA relationships remain unresolved.',
        no_source_acquisition=True, no_counts_reconstructed=True)
    (OUT / 'validation-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
