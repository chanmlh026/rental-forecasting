"""Independent pandas reconciliation of the offline research against the ingested source."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[3]
OUT = BASE / 'reports/data_audits/014.3'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads((OUT/'range-evidence.json').read_text(encoding='utf-8'))
    roster = json.loads((OUT/'predecessors.json').read_text())['authorities']
    manifest = args.source_root/'data/processed/ons_ashe/snapshot=2026-11-21-task009-2/manifest.json'
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == evidence['manifest_sha256']
    for name, digest in json.loads(manifest.read_text())['checksums'].items():
        assert hashlib.sha256((manifest.parent/name).read_bytes()).hexdigest()==digest
    frame = pd.read_parquet(manifest.parent/'observations.parquet')
    records = evidence['source_observations']
    keys = []
    for r in evidence['ranges']:
        authority = next(a for a in roster if a['code']==r['authority'])
        assert 2015<=r['year']<=int(authority['reorganisation_date'][:4])
        expected = authority.get('before_2019',authority['predecessors']) if r['year']<2019 else authority['predecessors']
        if r['role']=='later_roster_source_vintage_supplement':
            assert authority['name']=='Somerset' and r['year']==2018
            expected=authority['predecessors']
        assert r['expected_codes']==expected and len(expected)==len(set(expected))
        subset=frame.loc[(frame.source_edition_id==r['edition']) & frame.source_code.isin(expected)]
        valid=subset.loc[subset.pay_state=='numeric','annual_gross_median_gbp']
        assert r['valid_count']==int(valid.count())
        assert r['complete']==(valid.count()==len(expected))
        assert set(r['absent_codes'])==set(expected)-set(subset.source_code)
        assert set(records[k]['source_code'] for k in r['nonnumeric_observations'])==set(subset.loc[subset.pay_state!='numeric','source_code'])
        for field, value in [('minimum_gbp',valid.min()),('maximum_gbp',valid.max())]:
            assert r[field] is None if valid.empty else r[field]==value
        if len(valid)<2:
            assert r['observed_span_gbp'] is None and r['observed_span_percent_min'] is None
        else:
            span=float(valid.max()-valid.min())
            assert r['observed_span_gbp']==span
            assert math.isclose(r['observed_span_percent_min'],100*span/float(valid.min()),rel_tol=1e-12)
        for key in r['numeric_observations']+r['nonnumeric_observations']:
            o=records[key]
            source=subset.loc[subset.source_code==o['source_code']]
            assert len(source)==1
            source=source.iloc[0]
            for field,value in o.items():
                if field in source.index:
                    actual=source[field]
                    assert (value is None and pd.isna(actual)) or actual==value, (key,field)
        keys.append((r['authority'],r['year'],r['edition'],r['role']))
    assert len(keys)==len(set(keys))==142
    primary=[r for r in evidence['ranges'] if r['role']=='calendar_date_roster' and r['period']=='pre_reorganisation']
    assert len(primary)==119 and len(set((r['authority'],r['year']) for r in primary))==65
    assert len(set(r['authority'] for r in primary))==11
    same_edition_count=0
    for c in evidence['comparators']:
        r=next(r for r in evidence['ranges'] if (r['authority'],r['year'],r['edition'],r['role'])==(c['authority'],c['year'],c['predecessor_edition'],c['role']))
        assert c['complete_predecessors']==r['complete']
        if c['kind'].startswith('same_edition'):
            o=records[c['observation']]
            assert o['edition']==r['edition']
            assert c['combined_value_gbp']==o['annual_gross_median_gbp']
            same_edition_count+=1
        if r['minimum_gbp'] is not None:
            assert c['inside_observed_interval']==(r['minimum_gbp']<=c['combined_value_gbp']<=r['maximum_gbp'])
    result=json.loads((OUT/'validation-evidence.json').read_text())
    result['independent_pandas_range_reconciliation']='pass: all 142 records, including numeric counts, missing/suppressed identities and arithmetic'
    result['source_observation_fields_reconciled']='pass: original pay/CV markers, styles, source identities and population flags'
    result['comparator_pairing_and_interval_checks']='pass'
    result['source_manifest_and_snapshot_rechecked']='pass: all 4 files unchanged'
    (OUT/'validation-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
