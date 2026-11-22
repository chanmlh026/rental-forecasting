"""Regression coverage for ISS-021 using retained official research evidence."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "umb_independent_audit", Path("reports/data_audits/009.4/validate_ingestion.py")
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


@pytest.fixture
def observations():
    evidence = json.loads(
        Path("reports/data_audits/009.3/validation-evidence.json").read_text()
    )
    representatives = evidence["latest_hartlepool_official_records"]
    primary = deepcopy([r for r in representatives if r["ITEM"] == "2"])
    for offset, row in enumerate(primary):
        row.update(
            DATE_SORTORDER="6",
            ITEM_SORTORDER="0",
            RECORD_COUNT="4144",
            RECORD_OFFSET=str(3552 + offset),
        )
    return primary, deepcopy(representatives)


def test_original_mixed_item_and_request_metadata_failure(observations):
    primary, representatives = observations
    # Both items share date/geography/measure; the former key could not distinguish them.
    wrong_key = lambda r: (r["DATE"], r["GEOGRAPHY"], r["MEASURES"])
    assert len({wrong_key(r) for r in representatives}) == 2
    assert len(audit.observation_index(representatives)) == 4
    with pytest.raises(AssertionError):
        assert primary[0] == representatives[0]
    result = audit.compare_representatives(primary, representatives)
    assert result["count_rows_excluded"] == 2
    assert {r["key"][2] for r in result["compared"]} == {"2"}
    assert {r["key"][3] for r in result["compared"]} == {"20100", "20701"}
    assert all(
        "RECORD_OFFSET" in r["request_fields_differing"] for r in result["compared"]
    )


@pytest.mark.parametrize("field", sorted(audit.REQUEST_FIELDS))
def test_request_local_fields_are_excluded_only_from_equivalence(observations, field):
    primary, representatives = observations
    for row in primary:
        row[field] = "request-local-change"
    assert len(audit.compare_representatives(primary, representatives)["compared"]) == 2


@pytest.mark.parametrize(
    "field",
    [
        "OBS_VALUE",
        "OBS_STATUS",
        "OBS_CONF",
        "URN",
        "GEOGRAPHY_CODE",
        "GEOGRAPHY_NAME",
        "GEOGRAPHY_TYPECODE",
        "DATE_NAME",
        "DATE_CODE",
        "DATE",
        "GEOGRAPHY",
        "ITEM",
        "MEASURES",
    ],
)
def test_substantive_changes_are_never_ignored(observations, field):
    primary, representatives = observations
    primary[0][field] = "different"
    with pytest.raises(AssertionError):
        audit.compare_representatives(primary, representatives)


def test_missing_confidence_and_duplicate_observations_fail(observations):
    primary, representatives = observations
    with pytest.raises(AssertionError, match="Missing representative"):
        audit.compare_representatives(
            primary, [r for r in representatives if r["MEASURES"] == "20100"]
        )
    with pytest.raises(AssertionError, match="Duplicate"):
        audit.compare_representatives(primary + [primary[0]], representatives)


@pytest.fixture
def request_records(observations):
    primary, _ = observations
    for offset, row in enumerate(primary):
        row.update(RECORD_OFFSET=str(offset), RECORD_COUNT=str(len(primary)))
    url = (
        "https://www.nomisweb.co.uk/api/v01/dataset/NM_127_1.data.csv?"
        "geography=2092957699TYPE424&date=2026-06&item=2&measures=20100,20701"
    )
    return primary, url


def test_request_provenance_is_checked_separately(request_records):
    records, url = request_records
    assert audit.validate_request_records(records, url)["pagination_validated"]
    records[0]["RECORD_COUNT"] = "9999"
    with pytest.raises(AssertionError, match="record count"):
        audit.validate_request_records(records, url)


def test_offset_and_wrong_dataset_provenance_fail(request_records):
    records, url = request_records
    with pytest.raises(AssertionError):
        audit.validate_request_records(records, url.replace("NM_127_1", "NM_17_5"))
    records[0]["RECORD_OFFSET"] = "77"
    with pytest.raises(AssertionError, match="record offset"):
        audit.validate_request_records(records, url)
