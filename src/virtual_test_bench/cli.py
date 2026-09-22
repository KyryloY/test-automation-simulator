import argparse
from pathlib import Path

from .reporting import write_reports
from .runner import load_plan, run_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the hardware-free virtual RF test bench.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--profile", choices=["nominal", "power_low", "meter_timeout", "malformed_reply", "meter_offset", "warmup", "load_mismatch"], default="nominal")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)
    result = run_plan(load_plan(Path(args.plan)), args.seed, args.profile)
    json_path, markdown_path = write_reports(result, args.output)
    print(f"Reports: {json_path}, {markdown_path}")
    for item in result.measurements: print(f"{item.quantity}: {item.verdict} ({item.reason})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
