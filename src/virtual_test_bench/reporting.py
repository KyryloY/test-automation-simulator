import json
from dataclasses import asdict
from pathlib import Path

from .runner import RunResult


def write_reports(result: RunResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"plan": asdict(result.plan), "seed": result.seed, "profile": result.profile,
               "started_at": result.started_at, "simulation": result.simulation,
               "measurements": [asdict(item) for item in result.measurements]}
    json_path = output_dir / "result.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    rows = ["# Virtual test-bench report", "", f"Profile: `{result.profile}`; seed: `{result.seed}`", "", "| Quantity | Mean | Verdict | Reason |", "| --- | ---: | --- | --- |"]
    rows += [f"| {item.quantity} ({item.unit}) | {item.mean if item.mean is not None else '—'} | {item.verdict} | {item.reason} |" for item in result.measurements]
    markdown_path = output_dir / "summary.md"
    markdown_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return json_path, markdown_path
