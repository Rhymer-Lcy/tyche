# tyche

AI 命理 / divination engine. Named after Τύχη (Tyche), the Greek goddess of fortune.

## Status

The deterministic charting layer and the 七政四余 astronomy layer are implemented and tested (76 tests). The RAG knowledge base and some advanced rules await a 命理师 (practitioner) review before they proceed. Design rationale is in [docs/architecture.md](docs/architecture.md); completion status is in the [roadmap](#roadmap).

**Methodology: deterministic charting engine + classical-text RAG + LLM for wording + OCR at ingestion. No self-trained "fortune-telling" neural network.**

Two paradigms are routed by a single top-level switch `reference_pillar: day | year`: 子平 (day as 太极点) and 禄命星命 (year as 太极点).

## Dependencies & selection (see docs/architecture.md)

- Charting core: lunar-python (MIT, dependency)
- RAG: **LlamaIndex (MIT) + self-hosted Qdrant** (Dify is not used as the base; see docs §8)
- Classical text: **MinerU** (PDF→md/json) / **pandoc** (docx→md). MinerU does the glyph-level OCR; the LLM only does A/B/C triage + metadata, never character recognition (see docs/kb-ingestion-spec.md §6)
- embedding / rerank: SiliconFlow bge-m3 / bge-reranker-v2-m3 (online)
- Reasoning LLM: DeepSeek / Qwen for the base tier, Claude for the premium tier (see docs §7/§9)
- HTTP service: **FastAPI** (optional `.[api]`; thin wrapper over `cast()`)
- Astronomy: **skyfield** (optional `.[astro]`, MIT; avoids AGPL pyswisseph) + JPL de421 ephemeris. The 四余 are pure-formula and need neither.

## Layout

```
src/tyche/
  elements.py              # 干支/五行/阴阳/生克/藏干 truth tables
  calendar/
    true_solar_time.py     # true solar time correction (longitude offset + Meeus equation of time, ~0.01 min, zero-dep)
  chart/
    config.py              # ChartConfig — the 太极点 switch reference_pillar: day|year
    pillars.py             # four-pillar charting (wraps lunar-python) + Chart/Pillar (incl. 命宫/身宫/胎元)
    ten_gods.py            # 十神 (own implementation, 太极点-configurable)
    luck.py                # 大运/童限小运/流年/流月; all carry 太极点 十神 (stem + hidden), 流年/流月 also carry 旬空
  rules/                   # L3 rule engine (tyche's core differentiator)
    relations.py           # 刑冲合害会破 + 天干五合/相冲
    shensha.py             # 神煞 engine (空亡 algorithm + 太极点 routing)
    data/shensha.yaml      # 神煞 tables (external; each entry tagged anchor/reference)
    changsheng.py          # 十二长生
    strength.py            # day-master 旺衰 (子平 fuyi scoring, transparent and testable)
    pattern.py             # month-command 取格 (比劫 forms no pattern; config.pattern_school 子平/古法)
    __init__.py            # analyze(chart) -> {relations, shensha, strength, pattern}
  report.py                # cast(dt, config) -> ChartReport (single orchestration / public entry point)
  reading.py               # build_reading_prompt(report, question) -> {system, user}
  render.py                # render_chart(report) -> str (human-readable chart card)
  api.py                   # FastAPI service: /v1/chart /v1/reading /v1/fleeting /health
  __main__.py              # CLI: python -m tyche <chart|reading|fleeting|celestial>
  kb/
    blocks.py              # Block — the shared text unit for both loaders
    mineru_loader.py       # MinerU JSON -> blocks (PDF; restores split-page numbering)
    pandoc_loader.py       # pandoc md -> blocks (docx; restores pNN page markers)
    __init__.py            # load_book(slug) dispatches mineru/pandoc by directory
  celestial/               # 七政四余 astronomy layer (M4)
    zodiac.py              # ecliptic longitude -> 黄道十二宫 + 果老 branch palace (tropical, of-date)
    four_residues.py       # 四余 罗睺/计都/月孛 (Meeus mean-element formulas, zero-dep)
    seven_governors.py     # 七政 sun/moon/5 planets (skyfield geocentric apparent longitude + retrograde; needs .[astro])
    ephemeris.py           # JPL ephemeris loader (de421; configurable dir / env var)
scripts/                   # legacy demo.py / reading.py kept as thin wrappers over python -m tyche
tests/                     # 76 tests; tests/golden/cases.yaml is the golden chart set
```

## Quick start

```bash
python -m venv .venv
# Activate: Windows -> .venv\Scripts\activate ; macOS/Linux -> source .venv/bin/activate
pip install -e ".[dev]"
pytest                                              # 76 tests

# Chart (structured JSON; add --text for the human-readable card):
python -m tyche chart --datetime "1990-06-15 14:30" --gender male --lon 116.40 --ref day --text
# Reading prompt (feed to any reasoning LLM):
python -m tyche reading --datetime "1990-06-15 14:30" --gender male --question 事业财运
# 流年 (year 干支 + 太极点 十神 + enclosing 大运/小运/旬空; --end-year for a range; --months for the 12 流月):
python -m tyche fleeting --datetime "1990-06-15 14:30" --gender male --year 2025 --months
# --ref year switches to the 禄命星命 太极点; --pattern-school gufa_dangling switches 取格 to the 古法 variant
```

HTTP service (needs `pip install -e ".[api]"`):

```bash
python -m uvicorn tyche.api:app --reload            # interactive API docs at /docs
#   POST /v1/chart     {"datetime":"1990-06-15 14:30","gender":"male","longitude":116.4}
#   POST /v1/reading   above + {"question":"事业财运"}
#   POST /v1/fleeting  above + {"year":2025[,"end_year":2027][,"with_months":true]}
```

七政四余 (needs `pip install -e ".[astro]"`; the seven governors download the de421 ephemeris on first run):

```bash
python -m tyche celestial --datetime "1990-06-15 14:30"
```

## Roadmap

Done (deterministic layer, covered by 76 tests):

- [x] **M1 charting core (dual 太极点)**: four pillars / 十神 / 纳音 / 藏干 + 命宫/身宫/胎元 + true solar time + the 太极点 switch + golden tests (female chart / 立春 / 子时 boundaries)
- [x] **Charting completion**: 大运 (direction) / 童限小运 / 流年 / 流月 (五虎遁, fallback sequence cross-checked against the core), all carrying 太极点 十神 (stem + hidden), 流年/流月 carrying 旬空
- [x] **True-solar-time accuracy review**: the equation of time now uses the Meeus closed form (checked against authoritative tables, ~0.01 min error; the old Spencer approximation peaked at ~1.5 min and was dropped) + cross-midnight and cross-立春 boundary integration tests
- [x] **L3 rule engine**: 刑冲合害会破 + 神煞 (YAML / 太极点 routing / 空亡) + 十二长生 + 旺衰 (fuyi scoring) + month-command 取格 (比劫 forms no pattern; school switch)
- [x] **Public entry point**: cast() / ChartReport + `python -m tyche` CLI (incl. chart --text card) + FastAPI service (/v1/chart, /v1/reading, /v1/fleeting)
- [x] **Knowledge-base loaders**: MinerU (PDF) + pandoc (docx) into one unified Block; `load_book(slug)` dispatches by directory (all 4 books loadable)
- [x] **M4 七政四余 astronomy layer**: seven governors' geocentric apparent longitude + retrograde (skyfield / de421); 四余 罗睺/计都/月孛 (Meeus mean-element, zero-dep); 黄道十二宫 placement; checked against ephemeris and authoritative values

Pending a 命理师 review:

- [ ] **L3 advanced rules** (rules documented in docs/rules-L3-spec.md): 空亡 dialectics (three-pillar void turning to nobility, varies by 太极点), latent-branch layer (夹拱 / 飞天 / 倒冲 + 邀合 off by default with strong guards), 用神 preferences
- [ ] **M2 RAG knowledge base** (MinerU/pandoc → A/B/C triage → chunk → LlamaIndex + Qdrant): the 玉井奥诀 chunking pilot produced 187 chunks (zero controlled-vocabulary violations), pending a 命理师 spot-check before the full run; the OCR method was fixed to MinerU after a 10-page double-read comparison (see docs/kb-ingestion-spec.md)
- [ ] **七政四余 interpretation**: 庙旺 / 分野 / 宿度 (sidereal zodiac), 罗/计 node assignment, 紫炁 epoch are all school-dependent judgments
- [ ] **M3 禄命 paradigm**: 纳音 strength / 纳音 luck + base=year 神煞; 紫微斗数

## Known limitations

Honest notes on the work-in-progress, recorded here (by the author) rather than as GitHub issues:

- **取格 edge-case defect**: in a 杂气 month (辰/戌/丑/未), when the month-command 本气 is a 比劫 and no other 十神 is exposed in the stems, `pattern.py` falls back to the 本气 and mislabels it as a 比肩/劫财 pattern, which contradicts the engine's own "比劫 forms no pattern" rule. The correct handling (treat as 建禄/月劫, or no named pattern) is a school-dependent judgment, pending a 命理师 decision.
- **旺衰 is a single heuristic**: `strength.py` is a 子平 fuyi score (v1) with explicit, testable weights and thresholds. It belongs to a loosely-defined layer with school disagreement; it is a transparent reference, not a 命理师-endorsed verdict.
- **No interpretation yet**: 吉凶 / character / life-event readings depend on RAG and classical sources (see the roadmap's "pending review" items). The engine currently emits deterministic structure only, no readings.
- **Inputs required**: 大运 direction needs gender; true-solar-time correction needs the birth longitude. Without them, the pillars / 十神 / 旺衰 / 取格 / 神煞 / 刑冲合害 still compute; 大运 / 流年 and true solar time need the corresponding inputs.
