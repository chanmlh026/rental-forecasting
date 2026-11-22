"""Offline source-coverage research. Counts records; never reconstructs statistical values."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[3]
OUT = BASE/'reports/data_audits/014.4'
YEARS = list(range(2015, 2027))


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def value(v):
    if v is None or isinstance(v,float) and pd.isna(v): return None
    return v.item() if hasattr(v,'item') else v


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,action='append',required=True)
    parser.add_argument('--membership-root',type=Path,required=True)
    args=parser.parse_args()
    membership=args.membership_root/'reports/data_audits/014.3/predecessors.json'
    roster=json.loads(membership.read_text())['authorities']
    assert len(roster)==11
    codes={a['code'] for a in roster}; inspect=set(codes)
    for a in roster:
        inspect.update(a['predecessors']); inspect.update(a.get('before_2019',[]))
        if a.get('county_comparator'): inspect.add(a['county_comparator'])
    sources={}; versions={}; records=[]; fingerprints={}; notes={}

    def snapshot(dataset, name):
        paths=[p/'data/processed'/dataset/name for p in args.source_root]
        path=next(p for p in paths if (p/'manifest.json').exists())
        manifest=json.loads((path/'manifest.json').read_text())
        key=dataset+':'+name
        sources[key]={'dataset':dataset,'snapshot':name,'manifest_sha256':sha(path/'manifest.json'),'files':{}}
        fingerprints[path/'manifest.json']=sources[key]['manifest_sha256']
        return path,manifest,key

    def read(path, manifest, key, file, columns=None):
        p=path/file; digest=sha(p)
        expected=manifest.get('checksums',{}).get(file)
        if expected: assert digest==expected,(key,file)
        sources[key]['files'][file]={'sha256':digest,'bytes':p.stat().st_size,'matches_manifest':expected==digest if expected else None}
        fingerprints[p]=digest
        return pd.read_parquet(p,columns=columns)

    def add(variable, code, year, period, val, state, version, locator, flags=None):
        if code not in inspect or year not in YEARS: return
        numeric=state=='numeric' and value(val) is not None
        records.append({'variable':variable,'code':code,'year':int(year),'period':str(period),
                        'value':value(val) if numeric else None,'state':str(state),'version':version,
                        'locator':str(locator),'flags':flags or ''})

    def version(key, metadata):
        if key not in versions: versions[key]=metadata
        return key

    # Original annual earnings and published predecessor rows, all editions retained.
    p,m,k=snapshot('ons_ashe','snapshot=2026-11-21-task009-2')
    f=read(p,m,k,'observations.parquet');f=f.loc[f.source_code.isin(inspect)&f.observation_year.isin(YEARS)]
    for _,r in f.iterrows():
        v=version('ashe:'+r.source_edition_id,dict(source=k,url=r.source_url,source_sha256=r.source_sha256,
                  geographic_reference='native edition geography; historical current-code assignment unverified',
                  publication_date=value(r.source_release_date),unit='GBP/year',measure='Table 8.7a All median annual gross residence pay',support='U',sheet='All'))
        add('ashe',r.source_code,r.observation_year,r.reference_period_end,r.annual_gross_median_gbp,r.pay_state,v,
            r.pay_workbook+':All!D'+str(r.source_row),'pay_marker='+str(value(r.pay_marker))+'; CV='+str(value(r.median_cv_percent)))
    old=json.loads((BASE/'reports/data_audits/014.2/coverage-evidence.json').read_text(encoding='utf-8'))
    for entry in old['special_2019_boundaries']:
        if entry['kind']!='pay': continue
        v=version('ashe:special2019',dict(source='Task 014.2 ad hoc 11165',url='https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/adhocs/11165annualsurveyofhoursandearningsasheestimatesofannualandweeklyearningsbylocalauthorityusingapril2019localauthorityboundariesforplaceofworkandresidence2003to2017',
                  geographic_reference='explicit April 2019 boundaries; documented successor footprint compatible within the 11-authority structural-history scope',publication_date='2020-01-23',unit='GBP/year',support='C',reference_geography_confirmed=True))
        for row in entry['rows']:add('ashe',row['code'],entry['year'],str(entry['year'])+'-04-05',row['median'],'numeric',v,entry['member']+':'+row['cell'])

    # Primary UMB rate/confidence: preserve rolling periods; never average overlapping windows.
    p,m,k=snapshot('nomis_umb','snapshot=2026-11-22-task009-4')
    f=read(p,m,k,'observations.parquet');f=f.loc[f.gss_code.isin(inspect)]
    for _,r in f.iterrows():
        var='umb_rate' if r.measure=='20100' else 'umb_confidence'
        v=version('umb:'+r.source_request_name,dict(source=k,url=r.source_url,source_sha256=r.source_sha256,geographic_reference=r.source_geography_type,publication_date='2026-10-20',support='U',units={'umb_rate':'percent','umb_confidence':'percentage-point confidence margin'}))
        add(var,r.gss_code,int(r.reference_period_end[:4]),r.period_code,r.value,r.value_kind,v,r.source_urn,r.observation_status)
    for e in json.loads((OUT/'nomis-access-evidence.json').read_text()):
        p=BASE/'data/raw/geography-014-4'/e['name'];assert sha(p)==e['sha256'];fingerprints[p]=e['sha256']
        rows=list(csv.DictReader(p.read_text().splitlines()))
        assert all(r['ITEM']=='2' and r['MEASURES'] in ['20100','20701'] for r in rows)
        assert len({(r['DATE_CODE'],r['GEOGRAPHY'],r['MEASURES']) for r in rows})==len(rows)
        v=version('umb:'+e['name'],dict(source='Task 014.4 focused Nomis query',url=e['url'],source_sha256=e['sha256'],geographic_reference=rows[0]['GEOGRAPHY_TYPE'],publication_date='2026-10-20',retrieved_at=e['retrieved_at'],support='U',sample='December annual windows 2015-2025 and June 2026 only, not full quarterly history'))
        for r in rows:add('umb_rate' if r['MEASURES']=='20100' else 'umb_confidence',r['GEOGRAPHY_CODE'],int(r['DATE_CODE'][:4]),r['DATE_CODE'],float(r['OBS_VALUE']) if r['OBS_VALUE'] else None,'numeric' if r['OBS_STATUS']=='A' and r['OBS_VALUE'] else r['OBS_STATUS'],v,r['URN'],r['OBS_STATUS_NAME'])

    # Population, density and all six migration components on each published geographic version.
    p,m,k=snapshot('ons_population','snapshot=2026-11-22-task010')
    f=read(p,m,k,'observations.parquet');schema=read(p,m,k,'schema.parquet')
    notes['population']=[{c:value(r[c]) for c in ['edition_id','source_sheet','title','source_geography_vintage','publication_evidence_json','geography_evidence_json','source_url']} for _,r in schema.iterrows()]
    f=f.loc[f.source_code.isin(inspect)&f.reference_year.isin(YEARS)&(f.measure!='land_area')]
    for _,r in f.iterrows():
        var='density' if r.measure=='published_density' else r.measure
        # Declared geography must be independently supported by source notes, not just a GSS identifier.
        s=schema.loc[(schema.edition_id==r.edition_id)&(schema.source_sheet==r.source_sheet)].iloc[0]
        support='C' if str(r.source_geography_vintage)=='2023' else 'U'
        v=version('population:'+r.edition_id+':'+r.source_sheet,dict(source=k,url=r.source_url,source_sha256=r.source_sha256,
                  geographic_reference=str(r.source_geography_vintage),publication_date={
                      'detail2025':'2026-07-29','summary2025':'2026-07-29',
                      'detail2024':'2025-07-30','summary2024':'2025-07-30',
                      'detail2023':'2024-07-15','summary2023':'2024-07-15'}.get(r.edition_id),
                  publication_evidence=s.publication_evidence_json,geography_evidence=s.geography_evidence_json,
                  support=support,support_scope='declared source geography compatible with the 11 documented successor footprints; not a polygon audit or approval for other LAs',unit=r.unit))
        add(var,r.source_code,r.reference_year,r.period_end or r.reference_date,r.value,r.value_kind,v,r.source_sheet+'!'+r.source_cell,r.flags_json)

    # Approved Table 123 flows, separate Table 122 audit, Table 125 stock unrounded; no ratios or sums.
    p,m,k=snapshot('mhclg_housing','snapshot=2026-11-22-task011')
    f=read(p,m,k,'observations.parquet');nf=read(p,m,k,'notes.parquet')
    relevant=['net_additional_dwellings','new_build_completions','net_conversions','net_change_of_use','net_other_gains_and_losses','demolitions','dwelling_stock_unrounded']
    notes['housing']=[{c:value(r[c]) for c in ['edition_id','source_sheet','source_row','text']} for _,r in nf.loc[nf.text.str.contains('geograph|boundar|reorgan',case=False,regex=True)].iterrows()]
    f=f.loc[f.source_code.isin(inspect)&f.reference_year.isin(YEARS)&f.measure.isin(relevant)]
    for _,r in f.iterrows():
        v=version('housing:'+r.edition_id+':'+r.source_sheet,dict(source=k,url=r.source_url,source_sha256=r.source_sha256,
                  geographic_reference='native LA reporting basis; cover/notes name reorganisations and end former basis',publication_date='2026-05-21' if r.edition_id=='table125' else '2025-11-20',
                  support='housing_post_reorganisation',unit=r.unit,audit_only=r.edition_id=='table122'))
        var='stock' if r.measure=='dwelling_stock_unrounded' else r.measure
        add(var,r.source_code,r.reference_year,r.period or r.reference_date,r.value,r.value_kind,v,r.source_sheet+'!R'+str(r.source_row)+'C'+str(r.source_column),str(r.flags_json)+'; publisher_imputation='+str(value(r.publisher_imputation_flag)))

    # Planning application counts: keep full histories and selected fields, never dwelling-unit substitutions.
    p,m,k=snapshot('mhclg_planning','snapshot=2026-11-22-task012')
    fields={'ps1_full_values.parquet':{'Applications received':'planning_received'},
            'ps2_full_values.parquet':{'Total granted; major dwellings (all)':'planning_major_granted','Total granted; minor dwellings (all)':'planning_minor_granted'}}
    for file,mapping in fields.items():
        columns=['LPACD','LPANM','Quarter','source_record','source_url','source_sha256','source_authority_period_collision']+list(mapping)
        f=read(p,m,k,file,columns);f=f.loc[f.LPACD.isin(inspect)]
        for _,r in f.iterrows():
            v=version('planning:'+file,dict(source=k,url=r.source_url,source_sha256=r.source_sha256,
                      geographic_reference='LPA responsibilities; not certified whole-LAD footprint',publication_date='2026-09-24',support='U',unit='applications/decisions, not dwelling units'))
            for col,var in mapping.items():add(var,r.LPACD,int(r.Quarter[:4]),r.Quarter,r[col],'numeric' if pd.notna(r[col]) else 'source_missing',v,'CSV record '+str(r.source_record),str(r.source_authority_period_collision))

    # Two complete existing HPI vintages. Monthly prices/indices stay distinct.
    for snap in ['snapshot=2026-11-21-task008','snapshot=2026-11-21-task008-hpi-2026-08']:
        p,m,k=snapshot('uk_hpi',snap);f=read(p,m,k,'observations.parquet');f=f.loc[f.area_code.isin(inspect)]
        for _,r in f.iterrows():
            v=version('hpi:'+snap,dict(source=k,url=m['source_contract']['urls']['full'],source_sha256=r.source_sha256,geographic_reference='published source codes; full retrospective footprint unverified',publication_date=r.source_release_date,support='U',index_base=r.index_base_month))
            for col,var in [('average_price_gbp','hpi_price'),('house_price_index','hpi_index')]:add(var,r.area_code,int(r.observation_month[:4]),r.observation_month,r[col],'numeric' if pd.notna(r[col]) else 'source_missing',v,r.observation_month+':'+r.area_code)
    # PIPR target, each approved bedroom category separately.
    p,m,k=snapshot('ons_pipr','release=2026-10-21')
    f=read(p,m,k,'rent_observations.parquet');assert sha(p/'rent_observations.parquet')==m['processed_parquet_sha256']
    f=f.loc[f.local_authority_code.isin(inspect)]
    v=version('pipr:2026-10-21',dict(source=k,url=m['source_url'],source_sha256=m['raw_sha256'],geographic_reference='target-code matches verified; per-year boundary vintage not documented in retained workbook',publication_date=m['source_release_date'],support='U',unit='GBP/month'))
    for _,r in f.iterrows():add('pipr_'+str(r.bedroom_count),r.local_authority_code,r.observation_month.year,r.observation_month.strftime('%Y-%m'),r.average_monthly_rent_gbp,'numeric' if pd.notna(r.average_monthly_rent_gbp) else 'source_missing',v,r.local_authority_code+':'+r.observation_month.strftime('%Y-%m')+':'+str(r.bedroom_count))

    groups=defaultdict(list)
    for r in records:groups[(r['variable'],r['code'],r['year'])].append(r)
    variables=sorted({r['variable'] for r in records}|{'planning_dwelling_units_granted'})
    matrix=[]; details=[]
    for var in variables:
        for a in roster:
            for year in YEARS:
                direct=groups.get((var,a['code'],year),[])
                pred=a.get('before_2019',a['predecessors']) if year<2019 else a['predecessors']
                former=[r for c in pred for r in groups.get((var,c,year),[])]
                county=[r for r in groups.get((var,a.get('county_comparator',''),year),[]) if r['state']=='numeric']
                numeric=[r for r in direct if r['state']=='numeric']; confirmed=[]
                for r in numeric:
                    support=versions[r['version']]['support']
                    if support=='C':confirmed.append(r)
                    if support=='housing_post_reorganisation' and year>int(a['reorganisation_date'][:4]):
                        # Stock notes do not explicitly cover the four 2023 reorganisations.
                        if var!='stock' or int(a['reorganisation_date'][:4])<2023:confirmed.append(r)
                former_numeric=[r for r in former if r['state']=='numeric']
                status='Confirmed' if confirmed else 'Unverified' if numeric or county else 'Predecessor-only' if former_numeric else 'Missing' if direct or year>2025 else 'Evidence gap'
                if var=='planning_dwelling_units_granted':status='Evidence gap'
                byversion=defaultdict(list)
                for r in direct:byversion[r['version']].append(r)
                ids=[]
                for v,rs in sorted(byversion.items()):
                    nums=[r for r in rs if r['state']=='numeric'];key=f'{var}|{a["code"]}|{year}|{v}';ids.append(key)
                    sample=(nums or rs)[0]
                    detail=dict(id=key,variable=var,authority=a['code'],year=year,version=v,
                                        original_code=a['code'],native_periods=sorted({r['period'] for r in rs}),
                                        numeric_periods=sorted({r['period'] for r in nums}),markers=dict(Counter(r['state'] for r in rs if r['state']!='numeric')),
                                        sample=dict(period=sample['period'],value=sample['value'],state=sample['state'],locator=sample['locator']),
                                        flags_in_source_rows=sorted({r['flags'] for r in rs if r['flags']}),
                                        available_for_historical_forecast=(
                                            'postdates_observation_year'
                                            if versions[v].get('publication_date') and versions[v]['publication_date']>str(year)+'-12-31'
                                            else 'cutoff_and_availability_unverified'))
                    if detail['native_periods']==detail['numeric_periods']:
                        detail.pop('numeric_periods');detail['all_native_periods_numeric']=True
                    details.append(detail)
                matrix.append(dict(variable=var,authority=a['code'],name=a['name'],year=year,status=status,
                                   direct_numeric_versions=sorted({r['version'] for r in numeric}),confirmed_versions=sorted({r['version'] for r in confirmed}),
                                   detail_ids=ids,predecessor_roster_key=a['code']+'|'+str(year),
                                   predecessor_numeric_codes=sorted({r['code'] for r in former_numeric}),
                                   predecessor_row_markers=dict(Counter(r['state'] for r in former if r['state']!='numeric')),
                                   county_candidates=[dict(code=c['code'],version=c['version'],period=c['period'],value=c['value'],locator=c['locator']) for c in county],
                                   ))
    assert all(sha(p)==digest for p,digest in fingerprints.items())
    evidence=dict(scope_years=YEARS,authorities=[dict(code=a['code'],name=a['name'],reorganisation_date=a['reorganisation_date']) for a in roster],
                  membership_reference={'url':'https://github.com/chanmlh026/rental-forecasting/blob/7d2ddf2b2efe1af27e4182348e41e150aae3b683/reports/data_audits/014.3/predecessors.json','sha256':sha(membership),'review_status':'PR #15 unmerged at task start; research evidence, not an approved mapping'},
                  sources=sources,versions=versions,official_retained_notes=notes,variables=variables,
                  classification_scope='Any numeric period/version in year; not full-period completeness, a selected vintage or feature eligibility. Confirmed supports documented structural footprints of these 11, not polygon certification or other authorities.',
                  availability_legend={'postdates_observation_year':'This source vintage was not available by end of observation year. Year-end is a diagnostic, not an approved forecast cutoff.',
                                       'cutoff_and_availability_unverified':'Requires actual forecast cutoff and release/availability verification; no availability inferred.'},
                  predecessor_rosters={a['code']+'|'+str(y):(a.get('before_2019',a['predecessors']) if y<2019 else a['predecessors']) for a in roster for y in YEARS},
                  matrix=matrix,authority_year_source_details=details)
    # Standard JSON with one compact row per detailed record keeps the review artifact bounded.
    parts=[]
    for key,data in evidence.items():
        if key in ['matrix','authority_year_source_details']:
            body='[\n'+',\n'.join('    '+json.dumps(row,ensure_ascii=False,separators=(',',':')) for row in data)+'\n  ]'
        else:body=json.dumps(data,ensure_ascii=False,indent=2)
        parts.append('  '+json.dumps(key)+': '+body)
    (OUT/'coverage-evidence.json').write_text('{\n'+',\n'.join(parts)+'\n}\n',encoding='utf-8')
    # Table is a status index; detailed source version/periods and values remain in JSON.
    lookup={(r['variable'],r['authority'],r['year']):r for r in matrix}
    lines=['# Authority-variable-year coverage index','',
           'C Confirmed; U Unverified; P Predecessor-only; M Missing in investigated sources; E Evidence gap.',
           'Any numeric period/version qualifies for a yearly status; inspect JSON for partial years, suppression, original source and publication vintage.',
           'No statistical values are reconstructed. Confidence is separate from the rate. Fiscal years use ending year; UMB uses rolling-period ending year.','']
    for var in variables:
        lines+=['## '+var,'','| Authority | '+' | '.join(map(str,YEARS))+' |','|---|'+'---|'*len(YEARS)]
        for a in roster:lines.append('| '+a['name']+' | '+' | '.join({'Confirmed':'C','Unverified':'U','Predecessor-only':'P','Missing':'M','Evidence gap':'E'}[lookup[var,a['code'],y]['status']] for y in YEARS)+' |')
        lines.append('')
    (OUT/'coverage-by-year.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
    validation=dict(status='pass',authorities=len(roster),variables=len(variables),years=len(YEARS),matrix_rows=len(matrix),
                    source_versions=len(versions),authority_year_version_records=len(details),native_source_rows_inspected=len(records),
                    source_files_hash_verified_and_unchanged=len(fingerprints),classification_counts=dict(Counter(r['status'] for r in matrix)),
                    no_statistical_values_reconstructed=True,no_production_outputs=True)
    (OUT/'validation-evidence.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation,indent=2))


if __name__=='__main__':main()
