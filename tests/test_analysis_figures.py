from pathlib import Path

from kisti.analysis import figures
from kisti.analysis.report import compute
from kisti.analysis.style import setup


def test_every_figure_is_written(tmp_path: Path):
    setup()
    files = figures.all_figures(compute(), tmp_path)
    assert len(files) == 9
    for name in files.values():
        assert (tmp_path / name).stat().st_size > 5_000, name
