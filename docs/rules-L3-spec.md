# L3 Advanced-Rules Spec: 暗神 layer / 空亡 dialectics / 取格

> Source: multi-agent research + adversarial verification (2026-06), from the docs_local corpus
> (三命通会/玉井奥诀/星命抉古录/命理精华) cross-checked with 子平真诠. Evidence levels:
> **A strong, default ON / B school switch / C weak, default OFF or label-only**.
> These are school-sensitive rules; this spec marks each one's evidence strength and school as the
> implementation contract.

## 0. Principle: never mix the virtual/real directions (the root cause of a bug)
A 虚邀格's "虚神" **must not be filled in and must not be 空亡** (filling/空亡 = broken pattern, negative);
whereas an ordinary 忌神 **turns auspicious when 逢空** (positive) — the two directions are opposite.
**They must be distinguished by a context tag** (`virtual_pattern` vs `normal_branch`); **a single
shared void boolean must not** drive the scoring.

## 1. The 暗神 (latent-branch) layer (new `src/tyche/rules/latent.py`)
`LatentBranch{zhi, mechanism, source_pillars, confidence, filled, guard_ok, hidden_gans}`.
Once a 虚神 is produced, **reuse** the existing relations/shensha/ten_gods tables on it to get
暗天乙 / 暗禄 / 暗十神 / 虚神 relations (corpus: a 虚拱 noble qi "generates/controls/punishes/combines
the self, no different from a real one", 三命通会 p149-295; 玉井奥诀 L669).

| Mechanism | Trigger | Guard | Level |
|---|---|---|---|
| **夹拱 (拱禄拱贵)** | day and hour **same stem**, branches one apart enclosing the middle, the middle = the DM's 禄/贵 | the middle must not be filled, 空亡, or 冲/刑 | A, default ON |
| **飞天禄马** | day pillar in {庚子,壬子,辛亥,癸亥}, the branch in force 冲 its opposite (子冲午 / 亥冲巳) to take the opposite-palace 官 | no overt 财官 in the pillars, dislikes an exposed 官, needs one character to combine-hold the 禄马, dislikes filling/entanglement | A, default ON (medium weight) |
| **倒冲禄** | day pillar in {丙午,丁巳}, 午冲子 for the 癸 inside / 巳冲亥 for the 壬 inside; **the hour is not considered** | as above; 丙午 fears a 未 tie, 丁巳 fears a 申/辰 tie | A, default ON |
| **邀合 (子遥巳 / 丑遥巳 / 六合邀)** | present branches in force -> invite their combine-partner | **strong guard** (below) | **C, default OFF** (`latent_yaohe_enabled=False`) |
| 暗合 (遥合) table | the two branches' 本气 hidden stems 五合 | 申卯 / 子巳 / 午亥 (hard corpus evidence) | A; the extended pairs 寅丑 / 子戌 are C (OFF) |

**邀合 strong guard (all must pass)**: G1 no overt 财官 in the pillars; G2 the 虚神 must be the DM's
**正官 / 正禄 / a real 天乙** (checked via `ten_god(ref, 虚神 本气)`; **七杀 and 偏 gods do not count as
暗贵/暗禄**); G3 present and candidate must not be 三刑/相刑 to each other (寅巳申 / 丑戌未 / 子卯);
G4 the 虚神 must not be filled or 冲/tied; G5 present is in force (same branch ≥ 2).

> **Sample-chart verdict (壬午戊申壬申戊申)**: the three 申 "inviting 巳" -> **G2 fails** (巳 hides 戊 = 壬's
> 七杀, not 正官) **and G3 fails** (申 is in the 寅巳申 无恩之刑, a combine carrying a 刑) -> **does not hold**.
> So "暗贵/暗禄" does not stand classically. (What the three 申 truly point to is 飞财 — 申 冲 the 甲/丙
> inside 寅 as 财, the 飞财 pattern of 三命通会 — not inviting 巳.)

## 2. The 空亡 dialectics layer (`void_dialectic()`, a second pass after detect_shensha)
It does not rewrite "hits"; it only outputs `{branch, pillar, context, net_direction in 吉/凶/中,
target_role in 吉神/忌神/普通, reverts[]}`. First decide whether the branch carries a **吉神
(禄马财官贵用) or a 忌神/凶煞**, then stack the reversal conditions:

| Condition | Logic | Level |
|---|---|---|
| C1 冲 resolves the void | 空亡 met by 冲 -> turns from buried to active (**same-kind 冲 does not move it**, e.g. an empty 壬寅 met by 壬申) | ON |
| C2 met by 合 | a 吉神 空 + 合 -> not empty, add; a 凶神 空 + 合 -> evil revived, subtract (**opposite directions**) | ON |
| C3 生旺 | sitting on 长生/临官/帝旺 -> turns auspicious; 死绝墓 -> ominous force retained | ON |
| C4 filled | a virtual_pattern filled = broken (ominous); a normal 忌神 filled = void resolved (auspicious) — **needs context** | ON |
| C5 忌神 met by void | a 忌神 / something I control met by void -> turns auspicious ("天中肥殃") | ON |
| C6 true void | true void = empty & not 冲 & not 合 & not 刑 | ON |
| C7 五行 imagery | 金空 rings, 火空 shines, 水空 is clear (lean auspicious); 木空 breaks, 土空 collapses (lean ominous) | ON |
| C9 ominous stacking | a 凶神 met by void + 咸池/六害 present -> more ominous | ON |
| C10 吉神 force scatters | a 吉神 met by void scatters force ×0.5: 天乙 empty -> empty fame/talent; 禄 empty -> empty fame; 马 empty -> irregular 偏财 | ON |

### Three pillars all void turn to great nobility [B, `void_three_great_noble='gufa'`, **varies by 太极点**]
Triggers **only if**: (1) the month/day/hour branches are **all 旬空**; (2) each branch is **self-prosperous
and useful** (十二长生 旺相, or 五行 金/火/水); (3) **true void** (C6); (4) the chart has a **noble qi**
to rest on (禄/马/贵/官印). Only two pillars void -> "has office but not great", no trigger.
> Sample chart, **year 太极点**: 旬空 = 申酉, the month/day/hour 申 are all void, 申 = 壬's 长生 + 金空 rings
> -> **triggers great nobility**; **day 太极点 (子平)**: 旬空 = 戌亥, the 申 are not void -> no trigger.
> **This bonus must follow the 太极点 switch.**
> Source: 三命通会 "论空亡", "when the month/day/hour are all 空亡, it is not a harm but a great noble; if
> only two, there is office but not great", plus the strong preconditions (self-prosperous-and-useful /
> 金空 rings / true void) in the same passage. 子平真诠 / the 盲派 are the counter-schools (hence
> configurable, default on only for 古法 / year 太极点).

## 3. 取格 (`pattern.py`, implemented + tested)
- **比劫 form no pattern** (always dropped, folded into 建禄/月刃); if the 本气 is not exposed -> `config.pattern_school`:
  `ziping` (default; take the exposed other 十神, per 子平真诠 "the prefect not in the prefecture, the deputy acts") / `gufa_dangling` (the in-command 本气 first, exposed gods as 兼).
- Sample chart: **七杀格** (ziping) / **偏印格 with 七杀 as 兼** (gufa). Fixes the old "比肩格" bug.
- Verification caveat: 七杀 vs 偏印 is a school split (and "does 申 really hide 戊" is a hidden-stem dispute); **比肩格 is uniformly excluded by all schools.**

## 4. Level summary
- **A strong, default ON**: the three 暗合 pairs (申卯/子巳/午亥), 夹拱, 飞天/倒冲, 空亡 C1–C10, dropping 比劫 from 取格.
- **B school switch**: `pattern_school` (七杀/偏印), `void_three_great_noble` (varies by 太极点), `reference_pillar` (already present, affects 旬空 and 天乙 derivation), `transmit_priority`.
- **C weak, default OFF / label-only**: 邀合 (strong guard), the extended 暗合 pairs (寅丑/子戌), 天干 三奇 暗合, the 飞财 pattern, the "申 hides 戊" dispute (label a note, do not change the existing elements `[庚,壬,戊]`).

## 5. Golden tests (sample chart 壬午/戊申/壬申/戊申, reference_pillar='year')
- [x] 取格 = 七杀格 (ge_gan=戊), not 比肩格 (regression); gufa_dangling -> 偏印格 with 七杀 as 兼.
- [ ] 旬空 = {申,酉}; month/day/hour 申 all void -> three-pillars-void great nobility **triggers (year 太极点) / no trigger (day 太极点)**.
- [ ] inviting-巳 verdict = does not hold (reasons include 申 刑 巳 + 巳 hides 戊 as 七杀 not 正官); produces no 暗天乙/暗禄.
- [ ] 暗神: no `LatentBranch(zhi='巳', mechanism='邀合', guard_ok=True)` exists.

## Suggested implementation order
1. pattern.py 取格 fix (done).
2. the 空亡 dialectics layer `void_dialectic()` + three-pillars-void great nobility (varies by 太极点) — strong evidence and directly serving the sample chart.
3. `latent.py`: 夹拱/飞天/倒冲 first (A, default ON), 邀合 last (C, default OFF + strong guard), so the sample chart judges "inviting 巳 does not hold".
4. Golden tests for all of the above (§5).
