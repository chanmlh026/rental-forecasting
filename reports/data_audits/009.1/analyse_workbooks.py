"""Audit the approved annual/median/All field; no production dataset output.

Run with temporary pinned openpyxl/xlrd readers documented in the report.
Raw extracts stay ignored; Git receives aggregates, exceptions and field proof.
"""

import collections
import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from pathlib import Path

import openpyxl
import xlrd

from ingestion.boe import sha, verify_bundle
from investigate_ashe import ROOT

OUT = Path("reports/data_audits/009.1")


class Workbook:
    def __init__(self, name, body):
        self.modern = name.lower().endswith(".xlsx")
        if self.modern:
            self.book = openpyxl.load_workbook(io.BytesIO(body), data_only=False)
            self.names = self.book.sheetnames
        else:
            self.book = xlrd.open_workbook(file_contents=body, formatting_info=True)
            self.names = self.book.sheet_names()

    def rows(self, sheet):
        if self.modern:
            return [[cell.value for cell in row] for row in self.book[sheet].iter_rows()]
        return [self.book.sheet_by_name(sheet).row_values(i) for i in range(self.book.sheet_by_name(sheet).nrows)]

    def style(self, sheet, row, column):
        if self.modern:
            cell = self.book[sheet].cell(row, column)
            color = cell.fill.fgColor
            return dict(style_id=cell.style_id, pattern=cell.fill.patternType,
                color_type=color.type, color=color.rgb if color.type == "rgb" else color.index,
                number_format=cell.number_format)
        cell = self.book.sheet_by_name(sheet).cell(row-1, column-1)
        xf = self.book.xf_list[cell.xf_index]
        background = xf.background
        return dict(style_id=cell.xf_index, pattern=background.fill_pattern,
            palette_index=background.pattern_colour_index,
            palette_rgb=self.book.colour_map.get(background.pattern_colour_index),
            number_format=self.book.format_map[xf.format_key].format_str)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def source_code(value):
    return "" if value is None else str(value).strip().lstrip("'")


def parse_table(name, body):
    book = Workbook(name, body)
    assert "All" in book.names, name
    rows = book.rows("All")
    header = next(i for i,row in enumerate(rows) if len(row)>3 and row[0]=="Description" and row[1]=="Code" and row[3]=="Median")
    title=" | ".join(str(v) for v in rows[0] if v not in (None,""))
    assert "annual pay" in title.lower() and "gross" in title.lower(), name
    assert "all employee jobs" in title.lower(), name
    data = []
    england = False
    for i,row in enumerate(rows[header+1:],header+2):
        if len(row)<4:
            continue
        label = str(row[0] or "")
        if label.strip()=="England":
            england = True
        elif label.strip() in {"Wales","Scotland","Northern Ireland","Not Classified"}:
            england = False
        raw_code, median = row[1], row[3]
        code = source_code(raw_code)
        if not code or not re.fullmatch(r"(?:[A-Z]\d{8}|[A-Z0-9]{1,9})",code):
            continue
        data.append(dict(row=i, name=label, raw_code=raw_code, code=code,
            median=median, jobs_thousand=row[2], english_section=england,
            style=book.style("All",i,4)))
    notes = [str(row[0]) for row in rows if row and isinstance(row[0],str) and
        (row[0].startswith("a ") or row[0].startswith("b ") or "colour coding" in row[0] or "coefficient" in row[0])]
    sheet_titles = {sheet:" | ".join(str(v) for v in book.rows(sheet)[0] if v not in (None,""))
        for sheet in book.names if sheet in {"All","Male","Female","Full-Time","Part-Time"}}
    extra_notes=[]
    for sheet in book.names:
        if "note" in sheet.lower():
            extra_notes.extend(" ".join(str(v) for v in row if v is not None) for row in book.rows(sheet))
    return data, dict(workbook=name, sha256=sha(body), sheets=book.names,
        title=title, selected_sheet="All", header_row=header+1,
        geography_name_column="A", source_code_column="B", jobs_column="C", median_column="D",
        header=rows[header][:7], sheet_titles=sheet_titles, notes=notes,
        relevant_notes=[n for n in extra_notes if re.search(r"tax year|adult|all employees|gross|coefficient|disclos|suppres|CV\s*[<>=]",n,re.I)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-edition")
    args=parser.parse_args()
    reference=list(csv.DictReader(Path("configs/ons_lad_apr2025_v2.csv").open(encoding="utf-8-sig")))
    cohort={r["gss_code"]:r["local_authority_name"] for r in reference if r["target_eligible"]=="true"}
    assert len(cohort)==294
    access=json.loads((OUT/"access-evidence.json").read_text(encoding="utf-8"))
    results, fields, missing_sets, observations = [], [], {}, []
    for record in access:
        url=record["url"]
        name=re.sub(r"[^a-zA-Z0-9_.-]","_",url.rsplit("/",1)[-1])
        target=ROOT/record.get("raw_directory",name)
        manifest=verify_bundle(target)
        if manifest.get("status")!=200:
            continue
        body=(target/"response.bin").read_bytes()
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            pay=[n for n in archive.namelist() if re.search(r"Annual pay.*Gross",n,re.I) and re.search(r"8\s*\.7a",n,re.I)]
            cv=[n for n in archive.namelist() if re.search(r"Annual pay.*Gross",n,re.I) and re.search(r"8\s*\.7b",n,re.I)]
            if args.inspect_edition:
                if args.inspect_edition not in url:
                    continue
                for member in pay+cv:
                    book=Workbook(member,archive.read(member))
                    print(member,book.names)
                    for sheet in [s for s in book.names if s in {"All","Male","Female","Full-Time","Part-Time"}]:
                        print(sheet,repr(book.rows(sheet)[:7]).encode('ascii','backslashreplace').decode())
                return
            if len(pay)!=1 or len(cv)!=1:
                results.append(dict(edition=record.get("edition"),url=url,field_error="Expected one annual 8.7a and 8.7b workbook",candidates=pay+cv))
                continue
            data, proof=parse_table(pay[0],archive.read(pay[0]))
            cvs, cv_proof=parse_table(cv[0],archive.read(cv[0]))
        years=re.findall(r"20\d{2}",proof["title"])
        year=int(years[-1] if years else re.findall(r"20\d{2}",pay[0])[-1])
        proof["year_evidence"]="workbook header" if years else "advertised edition and archive member filename; split header omits year"
        assert str(year) in record.get("edition", "")
        by_code=collections.defaultdict(list)
        for row in data:
            by_code[row["code"]].append(row)
        cv_by_code={r["code"]:r for r in cvs}
        matches=[r for r in data if r["code"] in cohort]
        missing=sorted(set(cohort)-{r["code"] for r in matches})
        set_id=hashlib.sha256(json.dumps(missing).encode()).hexdigest()[:12]
        missing_sets[set_id]=missing
        numeric=[r for r in matches if finite(r["median"])]
        markers=collections.Counter(str(r["median"]) for r in matches if not finite(r["median"]))
        cv_bands=collections.Counter()
        for row in numeric:
            v=cv_by_code.get(row["code"],{}).get("median")
            cv_bands["unavailable" if not finite(v) else "<=5" if v<=5 else "5-10" if v<=10 else "10-20" if v<=20 else ">20"]+=1
        anomalies=[dict(code=r["code"],source_name=r["name"],approved_name=cohort[r["code"]])
            for r in matches if r["name"].strip()!=cohort[r["code"]]]
        result=dict(year=year,edition=record.get("edition"),url=url,source_zip_sha256=manifest["checksums"]["response.bin"],
            pay_workbook=pay[0],cv_workbook=cv[0],source_coded_geography_rows=len(data),
            english_la_gss_rows=sum(bool(re.fullmatch(r"E0[6789]\d{6}",r["code"])) for r in data),
            english_coded_geography_rows_including_counties=sum(r["english_section"] for r in data),
            exact_cohort_matches=len(matches),numeric_cohort_medians=len(numeric),
            cohort_markers=dict(markers),missing_cohort_count=len(missing),missing_set_id=set_id,
            duplicate_source_codes={code:len(rs) for code,rs in by_code.items() if len(rs)>1},
            numeric_matched_cv_bands=dict(cv_bands),
            median_style_counts=dict(collections.Counter(json.dumps(r["style"],sort_keys=True) for r in matches)),
            name_differences=anomalies,
            non_gss_code_rows=sum(not bool(re.fullmatch(r"[A-Z]\d{8}",r["code"])) for r in data),
            source_markers_all_geographies=dict(collections.Counter(str(r["median"]) for r in data if not finite(r["median"]))),
            exceptions=[dict(code=r["code"],name=r["name"],row=r["row"],median=r["median"],cv=cv_by_code.get(r["code"],{}).get("median")) for r in matches if not finite(r["median"])],
            examples=[{**r,"median_cv":cv_by_code.get(r["code"],{}).get("median")} for r in matches[:2]])
        results.append(result)
        fields.append({"year":year,"edition":record.get("edition"),"pay":proof,"cv":cv_proof})
        observations.append(dict(year=year,edition=record.get("edition"),source=url,rows=data,cv_rows=cvs))
        print(year,record.get("edition"),len(matches),len(numeric),dict(markers),dict(cv_bands))
    (ROOT/"selected-field-extracts.json").write_text(json.dumps(observations,indent=2)+"\n",encoding="utf-8")
    (OUT/"coverage-quality-evidence.json").write_text(json.dumps(dict(
        purpose="Source field audit only; no geography mapping, imputation or model-input vintage selection",
        reader_versions={"openpyxl":openpyxl.__version__,"xlrd":xlrd.__version__},
        cohort_reference_sha256=sha(Path("configs/ons_lad_apr2025_v2.csv").read_bytes()),
        cohort_size=294,editions=results,missing_cohort_sets=missing_sets),indent=2)+"\n",encoding="utf-8")
    (OUT/"field-evidence.json").write_text(json.dumps(fields,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
