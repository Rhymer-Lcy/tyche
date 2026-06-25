"""tyche CLI: `python -m tyche <chart|reading|fleeting|celestial> ...`

  python -m tyche chart     --datetime "1990-06-15 14:30" --gender male --lon 116.40 --ref day
  python -m tyche reading   --datetime "1990-06-15 14:30" --gender male --lon 116.40 --question 事业财运
  python -m tyche fleeting  --datetime "1990-06-15 14:30" --gender male --year 2025 [--end-year 2027]
  python -m tyche celestial --datetime "1990-06-15 14:30"   # 七政四余 (seven governors need .[astro])
Add --out path.json to export UTF-8 JSON (useful when the terminal garbles Chinese).
"""

import argparse
import json
import os
from datetime import datetime

from .chart.config import ChartConfig
from .chart.luck import fleeting_year, fleeting_years, fleeting_months
from .report import cast
from .reading import build_reading_prompt
from .render import render_chart


def _emit(data, out: str | None):
    text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"written: {out}")
    else:
        print(text)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tyche", description="tyche 命理 charting engine CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("chart", "reading", "fleeting", "celestial"):
        p = sub.add_parser(name)
        p.add_argument("--datetime", required=True, help='"YYYY-MM-DD HH:MM"')
        p.add_argument("--gender", choices=["male", "female"], default="male")
        p.add_argument("--lon", type=float, default=None, help="birth longitude, east positive")
        p.add_argument("--ref", choices=["day", "year"], default="day",
                       help="太极点: day=子平 (day as the self) / year=禄命星命 (year as the root)")
        p.add_argument("--pattern-school", choices=["ziping", "gufa_dangling"], default="ziping",
                       help="取格 school: ziping=子平真诠 / gufa_dangling=古法当令")
        p.add_argument("--out", default=None)
        if name == "chart":
            p.add_argument("--text", action="store_true", help="output the human-readable chart card (not JSON)")
        if name == "reading":
            p.add_argument("--question", default="综合命理")
        if name == "fleeting":
            p.add_argument("--year", type=int, required=True, help="start Gregorian year")
            p.add_argument("--end-year", type=int, default=None, help="if given, output the whole year range")
            p.add_argument("--months", action="store_true", help="for a single year, also include the 12 流月")

    args = ap.parse_args(argv)
    dt = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")

    if args.cmd == "celestial":
        from .celestial import four_residues
        data = {"four_residues": four_residues(dt)}
        try:
            from .celestial.seven_governors import seven_governors
            data["seven_governors"] = seven_governors(dt)
        except ImportError:
            data["seven_governors"] = None
            data["note"] = '七政 needs skyfield: pip install -e ".[astro]"'
        _emit(data, args.out)
        return

    cfg = ChartConfig(reference_pillar=args.ref, gender=args.gender,
                      longitude=args.lon, pattern_school=args.pattern_school)
    report = cast(dt, cfg)

    if args.cmd == "chart":
        _emit(render_chart(report) if args.text else report.to_dict(), args.out)
    elif args.cmd == "reading":
        _emit(build_reading_prompt(report, args.question), args.out)
    else:  # fleeting
        if args.end_year is not None:
            _emit({"years": fleeting_years(report.chart, args.year, args.end_year)}, args.out)
        else:
            out = {"year": fleeting_year(report.chart, args.year)}
            if args.months:
                out["months"] = fleeting_months(report.chart, args.year)
            _emit(out, args.out)


if __name__ == "__main__":
    main()
