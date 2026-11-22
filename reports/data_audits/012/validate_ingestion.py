"""Independent pandas CSV reconciliation; immutable offline replay and preservation."""

import csv
import hashlib
import io
import json
from pathlib import Path
import pandas as pd
from ingestion.mhclg_planning import ingest
from ingestion.boe import verify_bundle

ROOT = Path("data")
OUT = Path("reports/data_audits/012")
SNAPSHOT = "2026-11-22-task012"
PRODUCT = ROOT / "processed" / "mhclg_planning" / ("snapshot=" + SNAPSHOT)
RAW = ROOT / "raw" / "mhclg_planning" / ("snapshot=" + SNAPSHOT)


def hashes():
    return {
        p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in ROOT.rglob("*")
        if p.is_file()
    }


def reference_codes(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return {
            r["gss_code"] for r in csv.DictReader(f) if r["target_eligible"] == "true"
        }


def main():
    inventory = json.loads(
        Path("configs/mhclg_planning_sources.json").read_text(encoding="utf-8")
    )
    cohort = reference_codes(Path("configs/ons_lad_apr2025_v2.csv"))
    manifest = verify_bundle(PRODUCT)
    coverage = pd.read_parquet(PRODUCT / "coverage.parquet")
    reports = []
    all_coverage = []
    native = {}
    for s in inventory["sources"]:
        key = s["edition_id"]
        bundle = RAW / key
        meta = verify_bundle(bundle)
        body = (bundle / "response.bin").read_bytes()
        assert hashlib.sha256(body).hexdigest() == s["source_sha256"]
        # Independent engine and header discovery, not the production csv parser.
        lines = body.decode("cp1252").splitlines()
        header = next(
            i
            for i, l in enumerate(lines)
            if l.startswith("Region,LPANM,LPACD,Quarter,")
        )
        original = pd.read_csv(
            io.BytesIO(body),
            encoding="cp1252",
            skiprows=header,
            dtype=str,
            keep_default_na=False,
            skip_blank_lines=False,
        )
        raw = pd.read_parquet(PRODUCT / (key + "_source.parquet"))
        values = pd.read_parquet(PRODUCT / (key + "_values.parquet"))
        assert list(original.columns) == s["columns"]
        pd.testing.assert_frame_equal(original, raw[s["columns"]], check_dtype=False)
        numeric = [c for c in original.columns[4:] if c != "F_Year"]
        for c in numeric:
            expected = pd.to_numeric(
                original[c].replace({"..": None, "": None})
            ).astype(float)
            pd.testing.assert_series_equal(expected, values[c], check_names=False)
        assert raw.source_record.tolist() == list(
            range(header + 2, header + 2 + len(raw))
        )
        assert raw.source_sha256.eq(s["source_sha256"]).all()
        assert raw.source_url.eq(s["url"]).all()
        assert raw.source_retrieved_at.eq(meta["retrieval"]["retrieved_at"]).all()
        assert (
            raw.exact_cohort_code_match.tolist() == original.LPACD.isin(cohort).tolist()
        )
        assert (
            raw.source_duplicate_payload.tolist()
            == original.duplicated(keep=False).tolist()
        )
        assert (
            raw.source_authority_period_collision.tolist()
            == original.duplicated(["LPACD", "Quarter"], keep=False).tolist()
        )
        periods = pd.PeriodIndex(original.Quarter.str.replace(" ", ""), freq="Q")
        assert (
            raw.period_start.tolist()
            == periods.start_time.strftime("%Y-%m-%d").tolist()
        )
        assert raw.period_end.tolist() == periods.end_time.strftime("%Y-%m-%d").tolist()
        assert values.F_Year.tolist() == original.F_Year.tolist()
        summary = dict(
            edition_id=key,
            source_rows=len(raw),
            native_fields=len(original.columns),
            count_fields=len(numeric),
            exact_source_fields=int(original.size),
            count_cells=len(raw) * len(numeric),
            numeric_cells=int(values[numeric].notna().sum().sum()),
            missing_markers=int(original[numeric].eq("..").sum().sum()),
            quarters=original.Quarter.nunique(),
            first_period=min(original.Quarter),
            last_period=max(original.Quarter),
            authority_period_collision_rows=int(
                raw.source_authority_period_collision.sum()
            ),
            exact_duplicate_payload_rows=int(raw.source_duplicate_payload.sum()),
            missing_gss_code_rows=int((~original.LPACD.str.match(r"E[0-9]{8}$")).sum()),
        )
        for quarter, g in original.groupby("Quarter"):
            matched = g[g.LPACD.isin(cohort)]
            codes = set(g.LPACD)
            cov = coverage[
                (coverage.edition_id == key) & (coverage.period == quarter)
            ].iloc[0]
            assert (
                cov.source_rows == len(g)
                and cov.exact_cohort_matches == matched.LPACD.nunique()
            )
            assert json.loads(cov.unmatched_target_codes_json) == sorted(cohort - codes)
            for label, col in [
                ("major_residential_granted", "Total granted; major dwellings (all)"),
                ("minor_residential_granted", "Total granted; minor dwellings (all)"),
                ("applications_decided", "Applications decided"),
            ]:
                if col in numeric:
                    n = matched.loc[
                        matched[col].str.match(r"-?[0-9]+$"), "LPACD"
                    ].nunique()
                    assert cov[label + "_numeric_cohort"] == n
            all_coverage.append(cov.to_dict())
        expected_validation = manifest["validation"][key]
        assert summary["source_rows"] == expected_validation["authority_quarter_rows"]
        reports.append(summary)
        native[key] = original
        print("RECONCILED", key, summary["exact_source_fields"], "fields", flush=True)
    overlaps = []
    for table in ["ps1", "ps2"]:
        full = native[table + "_full"]
        recent = native[table + "_recent"]
        # Full/recent are distinct source assets, not assumed identical vintages.
        subset = full[full.Quarter.isin(recent.Quarter)]
        assert not subset.duplicated(["LPACD", "Quarter"]).any()
        a = subset.set_index(["LPACD", "Quarter"]).sort_index()
        b = recent.set_index(["LPACD", "Quarter"]).sort_index()
        assert a.index.equals(b.index)
        mismatches = a.ne(b)
        overlaps.append(
            dict(
                table=table,
                comparable_rows=len(a),
                comparable_fields=int(a.size),
                different_fields=int(mismatches.sum().sum()),
            )
        )
    for name in manifest["checksums"]:
        pd.testing.assert_frame_equal(
            pd.read_parquet(PRODUCT / name),
            pd.read_parquet(
                ROOT / "validated" / "mhclg_planning" / ("snapshot=" + SNAPSHOT) / name
            ),
        )
    before = hashes()

    def offline(_):
        raise AssertionError("Offline audit attempted acquisition")

    ingest(ROOT, SNAPSHOT, downloader=offline)
    assert before == hashes(), "Offline replay altered source/output evidence"
    prior = json.loads((OUT / "preservation-before.json").read_text())["files"]
    assert all(
        hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in prior.items()
    )
    documents = pd.read_parquet(PRODUCT / "documents.parquet")
    documents = documents.astype(object).where(pd.notna(documents), None)
    report = dict(
        status="PASS WITH CONDITIONS",
        sources=reports,
        full_recent_comparison=overlaps,
        coverage_rows=len(all_coverage),
        all_tables_agree=len(manifest["checksums"]),
        offline_unchanged_data_files=len(before),
        prior_data_files_preserved=len(prior) - 2,
        phase2_journal_and_reference_unchanged=True,
        publication_metadata=documents[
            ["source", "first_published_at", "public_updated_at", "internal_updated_at"]
        ].to_dict("records"),
        code_hashes={
            p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in [
                "src/ingestion/mhclg_planning.py",
                "configs/mhclg_planning_sources.json",
            ]
        },
        limitations=[
            "No model-ready or historical PIT claim",
            "Original historical duplicate/missing-code rows retained and flagged",
            "Publisher imputation/category changes retained; no cell-level un-imputed guarantee",
            "LA-wide total dwelling-unit permissions source and extract rights unresolved; no substituted counts",
        ],
    )
    (OUT / "validation-evidence.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    quarterly = pd.DataFrame(all_coverage).astype(object)
    quarterly = quarterly.where(pd.notna(quarterly), None)
    (OUT / "quarterly-coverage.json").write_text(
        json.dumps(quarterly.to_dict("records"), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
