"""Cross-publication precision differences are reported, never silently fixed."""

import importlib.util
from pathlib import Path
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    "mhclg_independent_audit", Path("reports/data_audits/011/validate_ingestion.py")
)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_integer_and_fractional_source_totals_reported_without_rounding():
    first = pd.DataFrame(
        [
            dict(
                source_code="E06000055",
                period="2012-2013",
                value=688.0,
                source_display_text="688",
            )
        ]
    )
    second = pd.DataFrame(
        [
            dict(
                source_code="E06000055",
                period="2012-2013",
                value=687.5,
                source_display_text="688",
            )
        ]
    )
    before_first = first.copy(deep=True)
    before_second = second.copy(deep=True)
    with pytest.raises(AssertionError):
        assert first.value.iloc[0] == second.value.iloc[0]
    result = audit.assess_net_additions(first, second)
    assert result["numeric_pairs"] == 1 and result["exact_value_differences"] == 1
    assert (
        result["max_observed_absolute_difference"] == 0.5
        and result["displayed_value_differences"] == 0
    )
    pd.testing.assert_frame_equal(first, before_first)
    pd.testing.assert_frame_equal(second, before_second)
    assert result["examples"][0]["value_123"] == 687.5


def test_distinct_periods_geographies_and_source_missingness_not_conflated():
    first = pd.DataFrame(
        [
            dict(source_code="E06000001", period="2024-2025", value=10.0),
            dict(source_code="E06000002", period="2024-2025", value=None),
        ]
    )
    second = pd.DataFrame(
        [
            dict(source_code="E06000001", period="2023-2024", value=10.0),
            dict(source_code="E06000002", period="2024-2025", value=0.0),
        ]
    )
    result = audit.assess_net_additions(first, second)
    assert (
        result["numeric_pairs"] == 0
        and result["missing_or_marker_pairs"] == 1
        and result["exact_value_differences"] == 0
    )
