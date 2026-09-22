from pathlib import Path

from virtual_test_bench.cli import main


def test_cli_creates_json_and_markdown_reports(tmp_path: Path):
    assert (
        main(
            [
                "--plan",
                "plans/nominal.json",
                "--profile",
                "nominal",
                "--seed",
                "42",
                "--output",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert (tmp_path / "result.json").exists()
    assert (tmp_path / "summary.md").exists()
