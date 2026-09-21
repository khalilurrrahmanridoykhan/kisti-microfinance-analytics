import numpy as np
import pandas as pd
import pytest

from kisti.analysis.stats import gini, hhi, lorenz, spearman, summarise, top_share


def test_top_share_and_missing_values():
    values = pd.Series([50, 30, 10, 5, 5, np.nan])
    assert top_share(values, 1) == pytest.approx(0.5)
    assert top_share(values, 2) == pytest.approx(0.8)


def test_hhi_is_10000_for_a_monopoly_and_1_over_n_for_equal_shares():
    assert hhi(pd.Series([100.0, 0.0, 0.0])) == pytest.approx(10_000)
    assert hhi(pd.Series([25, 25, 25, 25])) == pytest.approx(2_500)


def test_gini_of_equal_sizes_is_zero_and_of_one_holder_is_near_one():
    assert gini(pd.Series([7, 7, 7, 7])) == pytest.approx(0.0)
    assert gini(pd.Series([0, 0, 0, 100])) == pytest.approx(0.75)  # (n - 1) / n for n = 4


def test_gini_matches_the_pairwise_definition():
    values = np.array([1.0, 3.0, 4.0, 10.0, 22.0])
    pairwise = np.abs(values[:, None] - values[None, :]).sum() / (2 * len(values) ** 2 * values.mean())
    assert gini(pd.Series(values)) == pytest.approx(pairwise)


def test_lorenz_starts_at_zero_ends_at_one_and_never_exceeds_equality():
    curve = lorenz(pd.Series([1, 2, 3, 4, 10]))
    assert curve.iloc[0].tolist() == [0.0, 0.0]
    assert curve.iloc[-1].tolist() == [1.0, 1.0]
    assert (curve["share"] <= curve["institutions"] + 1e-12).all()


def test_spearman_uses_only_complete_pairs():
    x = pd.Series([1, 2, 3, 4, np.nan])
    y = pd.Series([10, 20, 30, 40, 50])
    rho, n = spearman(x, y)
    assert (rho, n) == (pytest.approx(1.0), 4)


def test_summarise():
    result = summarise(pd.Series([1, 2, 3, 4, np.nan]))
    assert result["n"] == 4 and result["median"] == 2.5 and result["mean"] == 2.5
