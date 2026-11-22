"""Independent source availability and report-integrity checks; no network or reconstruction."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd

BASE=Path(__file__).resolve().parents[3]
OUT=BASE/'reports/data_audits/014.4'


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,action='append',required=True)
    args=parser.parse_args()
    e=json.loads((OUT/'coverage-evidence.json').read_text(encoding='utf-8'))
    paths={}
    for key,source in e['sources'].items():
        p=next(r/'data/processed'/source['dataset']/source['snapshot'] for r in args.source_root if (r/'data/processed'/source['dataset']/source['snapshot']/'manifest.json').exists())
        assert digest(p/'manifest.json')==source['manifest_sha256']
        for name,meta in source['files'].items():assert digest(p/name)==meta['sha256'],(key,name)
        paths[source['dataset']+':'+source['snapshot']]=p
    for a in json.loads((OUT/'nomis-access-evidence.json').read_text()):
        p=BASE/'data/raw/geography-014-4'/a['name'];assert digest(p)==a['sha256']
        rs=list(csv.DictReader(p.read_text().splitlines()))
        assert len(rs)<25000 and all(r['ITEM']=='2' for r in rs)
        assert set(k.lower() for k in a['headers'])<={'content-type','etag','last-modified','retry-after'}
    details={d['id']:d for d in e['authority_year_source_details']}
    assert len(details)==len(e['authority_year_source_details'])
    matrix={(r['variable'],r['authority'],r['year']):r for r in e['matrix']}
    assert len(matrix)==27*11*12==3564
    assert set(r['status'] for r in matrix.values())=={'Confirmed','Unverified','Predecessor-only','Missing','Evidence gap'}
    for r in matrix.values():
        assert set(r['predecessor_numeric_codes'])<=set(e['predecessor_rosters'][r['predecessor_roster_key']])
        for ident in r['detail_ids']:
            d=details[ident];assert (d['variable'],d['authority'],d['year'])==(r['variable'],r['authority'],r['year'])
            assert d['original_code']==r['authority'] and d['version'] in e['versions']
            assert d['sample']['period'] in d['native_periods']
            if d.get('all_native_periods_numeric'):assert not d['markers']
            else:assert set(d['numeric_periods'])<=set(d['native_periods'])
            assert d['available_for_historical_forecast'] in e['availability_legend']
        if r['status']=='Confirmed':assert r['confirmed_versions']
        if r['status']=='Predecessor-only':assert r['predecessor_numeric_codes'] and not r['direct_numeric_versions'] and not r['county_candidates']
        if r['variable'] in ['hpi_index','hpi_price','pipr_1','pipr_2','pipr_3','umb_rate','umb_confidence']:assert r['status']!='Confirmed'
        if r['variable']=='planning_dwelling_units_granted':assert r['status']=='Evidence gap' and not r['detail_ids']
    # Independent source reconciliation of native year/period coverage for principal source tables.
    checks=0
    def check(frame,variable,code,year,period,version):
        nonlocal checks
        for authority in e['authorities']:
            for y in e['scope_years']:
                rows=frame.loc[(frame[code]==authority['code'])&(frame[year]==y)]
                ds=[d for d in details.values() if d['variable']==variable and d['authority']==authority['code'] and d['year']==y and d['version']==version]
                if rows.empty:assert not ds
                else:
                    assert len(ds)==1
                    expected=sorted(set(rows[period].astype(str)))
                    assert ds[0]['native_periods']==expected,(variable,authority['code'],y)
                    checks+=len(rows)
    p=paths['ons_population:snapshot=2026-11-22-task010']
    f=pd.read_parquet(p/'observations.parquet')
    for measure in ['population','internal_inflow','internal_outflow','internal_net','international_inflow','international_outflow','international_net']:
        subset=f.loc[(f.edition_id=='detail2025')&(f.measure==measure)].copy();subset['audit_period']=subset.period_end.where(subset.period_end!='',subset.reference_date)
        check(subset,measure,'source_code','reference_year','audit_period','population:detail2025:MYEB3')
        for a in e['authorities']:
            for y in range(2015,2026):assert matrix[measure,a['code'],y]['status']=='Confirmed'
    for key,p in paths.items():
        if not key.startswith('uk_hpi:'):continue
        f=pd.read_parquet(p/'observations.parquet',columns=['area_code','observation_month','average_price_gbp','house_price_index']);f['audit_year']=f.observation_month.str[:4].astype(int)
        for variable in ['hpi_price','hpi_index']:check(f,variable,'area_code','audit_year','observation_month','hpi:'+key.split(':',1)[1])
    p=paths['ons_pipr:release=2026-10-21'];f=pd.read_parquet(p/'rent_observations.parquet');f['audit_year']=f.observation_month.dt.year;f['audit_month']=f.observation_month.dt.strftime('%Y-%m')
    for bedroom in [1,2,3]:check(f.loc[f.bedroom_count==bedroom],'pipr_'+str(bedroom),'local_authority_code','audit_year','audit_month','pipr:2026-10-21')
    assert len([r for r in matrix.values() if r['variable']=='ashe' and r['status']=='Confirmed'])==12
    assert not any(e['versions'][v].get('url') is None for v in e['versions'])
    result=json.loads((OUT/'validation-evidence.json').read_text())
    result.update(independent_native_period_records_reconciled=checks,
                  independently_checked_grid_rows=len(matrix),
                  classification_coverage_refs_and_availability_invariants='pass',
                  all_source_manifest_file_and_query_hashes_rechecked='pass')
    (OUT/'validation-evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
