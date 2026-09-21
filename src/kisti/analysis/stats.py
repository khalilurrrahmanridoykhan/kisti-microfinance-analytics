"""Small, separately tested statistics used across the analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd


def top_share(values: pd.Series, k: int) -> float:
    """Share of the total held by the k largest values."""
    ordered = values.dropna().sort_values(ascending=False)
    return float(ordered.head(k).sum() / ordered.sum())


def hhi(values: pd.Series) -> float:
    """Herfindahl-Hirschman index on a 0 to 10,000 scale (sum of squared percent shares)."""
    shares = values.dropna() / values.dropna().sum()
    return float((shares**2).sum() * 10_000)


def gini(values: pd.Series) -> float:
    """Gini coefficient: 0 when every institution is the same size, close to 1 when one holds everything."""
    ordered = np.sort(values.dropna().to_numpy(dtype=float))
    n = len(ordered)
    cumulative = np.cumsum(ordered)
    return float((n + 1 - 2 * cumulative.sum() / cumulative[-1]) / n)


def lorenz(values: pd.Series) -> pd.DataFrame:
    """Lorenz curve points: cumulative share of institutions against cumulative share of the total."""
    ordered = np.sort(values.dropna().to_numpy(dtype=float))
    cumulative = np.concatenate([[0.0], np.cumsum(ordered) / ordered.sum()])
    return pd.DataFrame({"institutions": np.linspace(0, 1, len(cumulative)), "share": cumulative})


def spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    """Spearman rank correlation and the number of pairs it was computed on."""
    pair = pd.concat([x, y], axis=1).dropna()
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1], method="spearman")), len(pair)


def summarise(values: pd.Series) -> dict[str, float]:
    """n, quartiles and mean of the non-missing values."""
    clean = values.dropna()
    return {
        "n": int(len(clean)),
        "p25": float(clean.quantile(0.25)),
        "median": float(clean.median()),
        "p75": float(clean.quantile(0.75)),
        "mean": float(clean.mean()),
    }
