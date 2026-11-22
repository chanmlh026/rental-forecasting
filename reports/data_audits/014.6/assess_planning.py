"""Offline planning research inventory; never adds or allocates statistical counts."""

import argparse
import csv
import hashlib
import gzip
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'reports/data_audits/014.6'
MEASURES = {'ps1_full': ['Applications received', 'Applications decided'],
            'ps2_full': ['Total granted; major dwellings (all)',
                         'Total granted; minor dwellings (all)']}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(name, rows):
    compressed = name.endswith('.csv')
    buffer = io.StringIO(newline='') if compressed else None
    with (buffer if compressed else (OUT / name).open('w', newline='', encoding='utf-8')) as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        if compressed:
            (OUT / (name + '.gz')).write_bytes(gzip.compress(f.getvalue().encode('utf-8'), mtime=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    args = parser.parse_args()
    snap = 'snapshot=2026-11-22-task012'
    folder = args.source_root / 'data/processed/mhclg_planning' / snap
    manifest = json.loads((folder / 'manifest.json').read_text())
    fingerprints = {folder / 'manifest.json': sha(folder / 'manifest.json')}
    for name, expected in manifest['checksums'].items():
        path = folder / name
        assert sha(path) == expected, name
        fingerprints[path] = expected
    raw_root = args.source_root / 'data/raw/mhclg_planning' / snap
    for path in raw_root.rglob('response.bin'):
        fingerprints[path] = sha(path)
    ref_path = ROOT / 'configs/ons_lad_apr2025_v2.csv'
    fingerprints[ref_path] = sha(ref_path)
    ref = pd.read_csv(ref_path, encoding='utf-8-sig')
    ref = ref.loc[ref.target_eligible]
    assert len(ref) == 294 and ref.gss_code.nunique() == 294
    names = dict(zip(ref.gss_code, ref.local_authority_name))
    quarters = [f'{y}Q{q}' for y in range(2015, 2027) for q in range(1, 5)
                if (y, q) <= (2026, 2)]
    roster_path = ROOT / 'reports/data_audits/014.3/predecessors.json'
    roster = {a['code']: a for a in json.loads(roster_path.read_text())['authorities']}
    fingerprints[roster_path] = sha(roster_path)
    relations = json.loads((OUT / 'official-relationships.json').read_text())
    source_inventory = json.loads((ROOT / 'configs/mhclg_planning_sources.json').read_text())
    source_rows, field_coverage, full_history, groups = [], [], [], {}
    for edition, selected in MEASURES.items():
        native = pd.read_parquet(folder / (edition + '_values.parquet'))
        original = pd.read_parquet(folder / (edition + '_source.parquet'))
        native['audit_quarter'] = native.Quarter.str.replace(' ', '')
        original = original.set_index('source_record')
        assert original.index.is_unique
        source_columns = next(s['columns'] for s in source_inventory['sources']
                              if s['edition_id'] == edition)
        numeric_fields = [c for c in source_columns[4:] if c != 'F_Year']
        full_history.append(dict(edition=edition, rows=len(native),
            quarters=native.audit_quarter.nunique(),
            non_gss_rows=int((~native.LPACD.str.match(r'^E[0-9]{8}$')).sum()),
            code_quarter_collision_rows=int(native.source_authority_period_collision.sum()),
            duplicate_payload_rows=int(native.source_duplicate_payload.sum())))
        frame = native.loc[native.audit_quarter.isin(quarters)].copy()
        frame['audit_numeric_count'] = frame[numeric_fields].notna().sum(axis=1)
        assert frame.audit_quarter.nunique() == 46
        for quarter, part in frame.groupby('audit_quarter'):
            for field in numeric_fields:
                field_coverage.append(dict(edition=edition, quarter=quarter, field=field,
                    numeric_rows=int(part[field].notna().sum()),
                    missing_rows=int(part[field].isna().sum()), total_rows=len(part)))
        for _, r in frame.iterrows():
            key = (edition, r.LPACD, r.audit_quarter)
            groups.setdefault(key, []).append(r)
            item = dict(edition=edition, quarter=r.audit_quarter,
                native_quarter=r.Quarter, code=r.LPACD, name=r.LPANM,
                source_record=int(r.source_record), source_url=r.source_url,
                source_sha256=r.source_sha256,
                authority_type='National Park/Broads' if r.LPACD.startswith('E26') else
                    'Development corporation' if r.LPACD.startswith('E51') else
                    'Cohort council' if r.LPACD in names else 'Former/excluded council',
                numeric_count_fields=int(r.audit_numeric_count),
                missing_count_fields=len(numeric_fields)-int(r.audit_numeric_count))
            for field in selected:
                item[field] = str(original.loc[r.source_record, field])
            source_rows.append(item)
    # CSV union schema keeps PS1/PS2 fields distinct, including original '..' markers.
    keys = list(source_rows[0]) + MEASURES['ps2_full']
    source_rows = [{k: r.get(k, '') for k in keys} for r in source_rows]
    write_csv('source-authority-quarters.csv', source_rows)
    write_csv('all-field-quarter-availability.csv', field_coverage)
    latest, matrix, mismatch = [], [], []
    for code, name in names.items():
        links = [r for r in relations['relationships'] if code in r['la_codes']
                 and not r.get('ended_by_latest', False)]
        shared = [r for r in links if len(r['la_codes']) > 1]
        latest.append(dict(code=code, name=name,
            relationship='Shared' if shared else 'Split within one LA' if links else 'Unresolved',
            associated_native_lpa_codes=';'.join(sorted({code} | {r['source_code'] for r in links})),
            relationship_ids=';'.join(r['id'] for r in links),
            scope='Documented non-coterminous cases; absence from list is not coterminosity. Lookup unavailable.'))
        for quarter in quarters:
            a = roster.get(code)
            before = bool(a and quarter < a['reorganisation_date'][:4] + 'Q2')
            predecessors = (a.get('before_2019', a['predecessors'])
                            if before and quarter < '2019Q2' else a['predecessors'] if before else [])
            for edition, fields in MEASURES.items():
                direct = groups.get((edition, code, quarter), [])
                if not direct:
                    mismatch.append(dict(edition=edition, code=code, name=name,
                        quarter=quarter, predecessor_codes=';'.join(predecessors)))
                for field in fields:
                    pred = [r for c in predecessors for r in groups.get((edition, c, quarter), [])]
                    nums = [r for r in pred if pd.notna(r[field])]
                    # Only dated corporation evidence is extrapolated through its documented tenure.
                    active = [r for r in relations['relationships'] if code in r['la_codes']
                              and r.get('historical_start') and
                              r['historical_start'] <= quarter <= r.get('historical_end', '2026Q2')]
                    split = [r for r in active if r.get('complete_partition_verified')]
                    allocation = [r for r in active if len(r['la_codes']) > 1]
                    required = sorted({code} | {r['source_code'] for r in split})
                    required_rows = [r for c in required for r in groups.get((edition, c, quarter), [])]
                    complete_partition = bool(split and len(required_rows) == len(required)
                                              and all(pd.notna(r[field]) for r in required_rows))
                    # No Direct without a verified coterminous lookup/history. No count summation.
                    status = 'Additive' if complete_partition else 'Allocation required' if allocation else 'Unverified'
                    reason = ('Documented whole-LA partition; all required native observations numeric'
                              if complete_partition else 'Documented cross-LA planning total cannot be assigned'
                              if allocation else 'Coterminous/historical LPA relationship not established')
                    if split and not complete_partition:
                        status = 'Missing'
                        reason = 'Verified partition lacks a unique numeric required observation'
                    elif not direct and not nums and not allocation:
                        status = 'Missing'
                        reason = 'No direct or numeric statutory-predecessor candidate in inspected records'
                    matrix.append(dict(edition=edition, measure=field, code=code, name=name,
                        quarter=quarter, classification=status, reason=reason,
                        direct_records=';'.join(str(int(r.source_record)) for r in direct),
                        direct_numeric=len([r for r in direct if pd.notna(r[field])]),
                        direct_missing=len([r for r in direct if pd.isna(r[field])]),
                        predecessor_codes=';'.join(predecessors),
                        predecessor_records=';'.join(str(int(r.source_record)) for r in pred),
                        predecessor_numeric_codes=';'.join(sorted({r.LPACD for r in nums})),
                        predecessor_missing_codes=';'.join(c for c in predecessors if
                            len(groups.get((edition,c,quarter),[])) != 1 or
                            any(pd.isna(r[field]) for r in groups.get((edition,c,quarter),[]))),
                        required_partition_codes=';'.join(required) if split else '',
                        geography_evidence_ids=';'.join(r['id'] for r in active)))
    write_csv('latest-la-relationships.csv', latest)
    write_csv('la-quarter-measure-coverage.csv', matrix)
    write_csv('historical-code-mismatches.csv', mismatch)
    assert len(matrix) == 294 * 46 * 4
    assert len(mismatch) == 271 * 2
    assert all(r['code'] in roster for r in mismatch)
    assert all(sha(p) == d for p, d in fingerprints.items())
    summary = dict(status='partial: geography lookup/history evidence prerequisite unresolved',
        cohort=294, quarters=46, measures=MEASURES,
        latest_relationship_counts=dict(Counter(r['relationship'] for r in latest)),
        latest_direct_coterminous_verified=0,
        latest_direct_note='Zero certified by evidence available here, not zero actually coterminous.',
        full_history=full_history, source_rows_in_scope=len(source_rows),
        original_nonstandard_code_rows_in_scope=sum(not re_gss(r['code']) for r in source_rows),
        per_edition_mismatches=dict(Counter(r['edition'] for r in mismatch)),
        unique_mismatch_authority_quarters=len({(r['code'],r['quarter']) for r in mismatch}),
        classification_counts=dict(Counter(r['classification'] for r in matrix)),
        per_measure_counts={f:dict(Counter(r['classification'] for r in matrix if r['measure']==f))
                            for fields in MEASURES.values() for f in fields},
        unique_la_quarter_statuses={s:len({(r['code'],r['quarter']) for r in matrix if r['classification']==s})
            for s in ['Direct','Additive','Allocation required','Missing','Unverified']},
        mismatch_complete_numeric_predecessor_candidates_by_measure={f:sum(
            bool(r['predecessor_codes']) and not r['predecessor_missing_codes']
            for r in matrix if r['measure']==f and not r['direct_records'])
            for fields in MEASURES.values() for f in fields},
        verified_recovery_of_271_code_gaps=0,
        source_files_unchanged=len(fingerprints),
        input_hashes={str(p.relative_to(args.source_root)) if p.is_relative_to(args.source_root)
                      else str(p.relative_to(ROOT)): d for p,d in fingerprints.items()},
        no_reconstructed_counts=True, no_production_changes=True)
    (OUT/'assessment-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'input_hashes'},indent=2))


def re_gss(code):
    import re
    return bool(re.fullmatch(r'E[0-9]{8}',code))


if __name__ == '__main__':
    main()
