# tyche Architecture & Open-Source Selection

> AI 命理 system. Named after the Greek goddess of fortune, Τύχη.
> This file is the design rationale for the tech selection and architecture (2026-06, from corpus
> and framework research) — it records *why* things were chosen.
> For each milestone, **the actual status is the README roadmap**; this file is not updated line by line.

---

## 0. Core judgment (TL;DR)

**tyche = a deterministic charting engine + classical-text RAG + an LLM for wording + OCR at ingestion. No self-trained "fortune-telling" neural network.**

命理 is two deterministic problems stacked together, neither suited to end-to-end deep learning:

- Charting = a **closed-form deterministic computation** in calendar astronomy (table lookups + an astronomical ephemeris); fitting it with a neural net only adds error and loses interpretability.
- Readings = discrete symbolic knowledge, i.e. "retrieval + rule reasoning", not a continuous function suited to gradient descent.
- Chart-to-life-event has **no verifiable ground truth**; a self-trained predictor is unfalsifiable, i.e. fake precision.

Deep learning is used in only three peripheral spots, all via **off-the-shelf pretrained models**: OCR, RAG embedding/rerank, and optional LoRA styling.

---

## 1. Corpus paradigms: two schools + the 太极点 switch

| Corpus | School | 太极点 | Ingestion status |
|---|---|---|---|
| 彭康民命理精华 | modern 子平 (with 七政四余/星命 flavor) | day | scan, needs OCR |
| 玉井奥诀 | classical 子平 (格局/用神/旺衰 by command) | day | scan, needs OCR |
| 星命抉古录 | 禄命/星命 (神煞 as the frame, 纳音 as the root) | year | converted to text (traditional Chinese) |
| 三命通会 | a synthesis (古法 禄命 + 子平 together) | both | near-scan bad glyphs; needs OCR + an orthography dictionary |

**子平 (day):** the day stem is the self; the other pillars take 十神 relative to it; the core is day-master 旺衰, 用神 preferences, and 十神 格局; 神煞 is auxiliary and can be turned off.
**禄命/星命 (year):** the year pillar's 纳音 is the root; 神煞 anchors mostly on the year branch / year 纳音; 命宫/胎元/小运 follow the 古法.

---

## 2. Layered architecture

```
L6 interface/UI       FastAPI thin wrapper (api.py, wraps cast()); frontend TBD
L5 LLM reading layer  LiteLLM router -> DeepSeek/Qwen (base tier) / Claude (premium tier)
L4 knowledge base/RAG LlamaIndex + SiliconFlow bge-m3 + bge-reranker-v2-m3 (online) + self-hosted Qdrant
   ^ OCR ingestion    MinerU layout parse -> clean -> orthography mapping -> chunk; hard-page glyph anchor via PaddleOCR-VL
L3 神煞/格局 rules     tyche's own (pluggable rules, each 神煞 tagged base=year|day)  <- core differentiator
L2 charting (dual)    lunar-python (dependency) + tyche's 太极点 extension layer
L1 calendar/astronomy lunar-python (primary) / sxtwl (precision fallback)
   七政四余 branch     skyfield (MIT; closed-source/SaaS avoids swisseph's AGPL)
```

> Deployment follows §7 and §8: at query time (embedding/rerank/reading LLM) everything goes
> through online APIs, with the vector store (Qdrant) self-hosted; OCR is a one-off offline
> ingestion. This diagram is only the logical layering.

---

## 3. The configurable 太极点 design

The top-level switch runs through 5 computation branches; the shared base is unchanged, the
difference is only the strategy-dispatch layer of "whose data we read".

```python
class ChartConfig:
    reference_pillar: Literal["day", "year"]      # 子平=day / 禄命星命=year
    school: Literal["ziping", "luming", "xingming"]
    overlays: list[str]                           # ["minggong","taiyuan","qizheng"]
```

| Branch | day (子平) | year (禄命/星命) |
|---|---|---|
| (1) reference | self = day stem; other pillars take 十神 | self = year 纳音 / year stem; referenced to the year-命 纳音 |
| (2) 旺衰 origin | 十二长生 starts from the day stem's 五行 | starts from the year pillar's **纳音 五行** (different granularity) |
| (3) 神煞 base | base=day, mostly queried from day branch / month command | base=year, mostly from year branch / year 纳音 |
| (4) luck cycles | 大运 by the month pillar's direction, read by 十神 | 小运 + 纳音/年命 luck (古法) |
| (5) 命宫/胎元 | 子平 convention, auxiliary | 果老 system, sign by 节气, high weight |

Implementation: strategy pattern / registry. Each 神煞 rule carries a `base` field; the engine
routes lookups by `reference_pillar`. The shared base (干支 calendar, 节气-based month, true solar
time, the 六十甲子 纳音 table, 刑冲合害, the 十二长生 table) is reused by both schools.

> `reference_pillar` has **no effect on the astronomy layer**: planetary longitudes are always
> computed from the birth instant; the year 太极点 only changes the upper 禄命 luck/神煞 usage.
> **True solar time** is needed by both schools: lunar-python does no longitude correction, so the
> input must be corrected ("longitude offset + equation of time") before constructing the Solar.

---

## 4. Dependency / selection list (priority order)

| Priority | Repo | License | Mode | Role / notes |
|---|---|---|---|---|
| **P0** | [6tail/lunar-python](https://github.com/6tail/lunar-python) | MIT | **dependency** | calendar astronomy + charting core (四柱/十神/纳音/大运/流年/节气 to the second). tyche wraps it with Pillars/TenGods/LuckCycle + the 太极点 extension + input-side true-solar-time correction |
| **P1** | [run-llama/llama_index](https://github.com/run-llama/llama_index) | MIT | dependency | RAG orchestration; connects bge-m3 / Qdrant / the reading LLM |
| **P1** | [qdrant/qdrant](https://github.com/qdrant/qdrant) | Apache-2.0 | dependency (container) | vector store; native dense+sparse hybrid retrieval + RRF |
| **P1** | [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (VL) | Apache-2.0 | optional | glyph anchor for classical vertical / handwritten / variant glyphs; modern regular books go through MinerU. Pin the version for reproducibility |
| **P2** | [china-testing/bazi](https://github.com/china-testing/bazi) | **no LICENSE** | **read-only reference, no fork** | reference for 十神 scoring / 刑冲合会 / 神煞 conventions / corpus organization. Legal line: no LICENSE means all rights reserved — no whole-repo commercial use |
| **P2** | [cantian-ai/bazi-mcp](https://github.com/cantian-ai/bazi-mcp) | ISC | reference impl | the "charting as a tool" MCP idea |
| **P3** | [SylarLong/iztro](https://github.com/SylarLong/iztro) | MIT | dependency (optional) | 紫微斗数 charting + a ready star-chart UI (when 紫微 is taken on) |
| **P3** | [yuangu/sxtwl](https://github.com/yuangu/sxtwl_cpp) | BSD | optional dependency | high-precision 节气 validation backend |
| **P3** | skyfield | MIT | optional dependency | the 七政四余 astronomy layer. **Decided on skyfield over pyswisseph**: the project is closed-source/SaaS, the swisseph family is AGPL, and serving it would trigger full source disclosure. The cost is writing 过宫/nodes/四余 ourselves, but it avoids the license line |

> **Evaluated, not adopted**: [gaaiyun/FOR-BAZI](https://github.com/gaaiyun/FOR-BAZI) (MIT). The plan
> was to fork its React+FastAPI web skeleton; after evaluation we built a thin REST instead
> (`src/tyche/api.py`, wrapping `cast()`) and pulled in no frontend scaffolding; frontend TBD.

**Models (HuggingFace, not forked — weights pulled directly):**
- embedding: `BAAI/bge-m3` (MIT, dense + a **sparse lexical channel**, for exact hits on terms like 伤官/七杀/偏印)
- reranker: `BAAI/bge-reranker-v2-m3` (Apache, 0.6B, same family)
- classical-text preprocessing aid: `SikuBERT / GuwenBERT` (segmentation/punctuation/term mining, not the main retriever)
- hard-page OCR fallback: `Qwen3-VL` (cross-check; 命理 needs every character right, so the VLM only corrects, never stands alone)

**tyche's own, un-forked core assets:** the L3 神煞/格局 rule engine + the 太极点 extension layer + the OCR orthography dictionary + reading-prompt engineering. This is where the differentiated value is.

---

## 5. Roadmap (original plan)

> Below is the original selection-phase plan; **the actual status is the README roadmap** (the two
> already diverge — the OCR primary pipeline and the interface layer were adjusted to the implementation).

- **M1 子平 MVP (day 太极点)**: wrap lunar-python + true-solar-time correction + a self-built cast()/FastAPI thin wrapper + basic readings + **a golden chart test set** (regression baseline). Acceptance: birth time -> correct 四柱/十神/大运/流年 + a reading.
- **M2 RAG + rule engine**: an OCR pipeline (MinerU primary + hard-page PaddleOCR-VL/VLM fallback + orthography dictionary + human review) over 玉井/彭康民; LlamaIndex + bge-m3 (sparse on) + Qdrant + reranker, with readings citing classical sources; a first rule engine (神煞/刑冲合害/用神/化气, external YAML, tagged base).
- **M3 configurable 太极点 + 禄命 paradigm**: land the day|year switch across the 5 branches; ingest 星命抉古录 + 三命通会; 纳音 旺衰 / 纳音 luck (古法). Acceptance: one birth time can switch between the day and year charts.
- **M4 advanced**: the 七政四余 astronomy branch + the 四余 fictitious bodies + 果老 命宫/胎元 (own build); 紫微 (iztro); optional LoRA styling; MCP-ification.

---

## 6. Risks / pitfalls

1. **OCR quality on classics**: 三命通会 is WPS self-made bad glyphs (no text layer at all); zero misreads from any model is impossible, so a "variant/self-made glyph -> orthography" mapping dictionary + a human-review loop are **mandatory**. 星命抉古录 has doubly-garbled encoding and needs encoding detection + character remapping. Vertical text needs pre-rotation; modern regular books go through MinerU, while classical vertical / hard pages use PaddleOCR-VL as a glyph anchor, with the VLM only correcting, never standing alone.
2. **The swisseph license line (AGPL), decided**: the project is closed-source/SaaS, and pyswisseph/flatlib/kerykeion are all AGPL — serving them triggers full source disclosure — so **skyfield (MIT) + JPL public-domain .bsp** is fixed, avoiding it entirely. Cost: the 四余 (罗/计 derivable from the nodes; 月孛/紫炁 and other fictitious bodies built by us), 过宫 mapping, and 果老 命宫/胎元 must be written ourselves, but with no license risk.
3. **No ground truth in 命理 evaluation**: do not promise "prediction accuracy". Measurable targets are limited to charting correctness (compared against the golden set, with objective answers), RAG recall quality (term hits + traceable citations), and reading school-consistency.
4. **LLM hallucination / compliance**: readings must attach the **real sources** retrieved by RAG; the model must not invent classical text freely; charting is never handed to an LLM (only to deterministic tools); the product needs an **entertainment/cultural-use disclaimer**; the user's birth data is sensitive personal information, and self-hosting the vector-store query path helps privacy compliance (see §9).
5. **Legal pitfall**: china-testing/bazi has no LICENSE — all rights reserved — so no whole-repo fork for commercial use; only read the logic and rewrite.
6. **School conventions**: lunar-python's 神煞 conventions are one author's take; school differences in 子时 day change / year change must be handled explicitly in the wrapper; tyche's multi-school stance requires the conventions to be externalized as configurable YAML.

---

## 7. LLM selection & deployment strategy

**Core judgment: reading quality is what the user pays for, so this layer cannot be cut; but "saving cost" and "Claude vs self-hosted" are two separate questions. Abstract the LLM into a router and split by tier.**

### Cost reality (addressing the "Claude is too expensive" concern)

Per-reading token estimate: system + rules (cacheable, ~0.1× on hit) ~12k / charting ~2k / RAG recall ~5k / reading output ~3k.

| Model | price in/out (per 1M) | per-call cost | converted |
|---|---|---|---|
| Haiku 4.5 | $1 / $5 | ~$0.024 | ¥0.17 |
| Sonnet 4.6 | $3 / $15 | ~$0.07 | ¥0.5 |
| Opus 4.8 | $5 / $25 | ~$0.12 | ¥0.9 |

Even all-Opus is under ¥1 per call. **prompt caching** can compress the fixed 命理 rules / system prompt to ~0.1×; non-realtime batches can use the **Batch API** for another ~50% off. Conclusion: cost is not a barrier to using Claude.

### Decision: online APIs at query time, fixed from day one

The end state is SaaS, and query-time inevitably needs online APIs, so **build on online models from day one, rather than building half of a local/offline dependency that is destined to be torn out**. The key is to separate two kinds of dependency:

- **Query time (per request) = online APIs**: embedding + rerank + the reading LLM.
- **One-off ingestion (run over the whole corpus once, output is static text) = local/offline**: OCR. Standing up an online service for a one-off build is wasteful, hard pages need human review, and local is controllable; once OCR is done it is decoupled from offline compute.

**Online stack (directly reachable in China, or via a compatible gateway):**

| Layer | Choice | Notes |
|---|---|---|
| embedding (ingest + query) | **SiliconFlow `BAAI/bge-m3`** | dense+sparse (exact 命理-term hits); domestic / cheap / OpenAI-compatible. **Index built here once, never re-indexed** |
| rerank | **SiliconFlow `BAAI/bge-reranker-v2-m3`** | cross-encoder, same provider |
| reading, base tier | **DeepSeek / Qwen (SiliconFlow or direct)** | domestic, cheap, strong on classical Chinese |
| reading, premium tier | **Claude (Sonnet/Opus)** | the quality ceiling, a paid "master reading". Direct only from an overseas backend; see §9 on cross-border |
| retrieval framework | **LlamaIndex (MIT, library)** | see §8: non-standard retrieval, no visual platform |
| vector store | **self-hosted Qdrant** | supports payload filtering; the query and chart metadata are self-hosted (§9) |
| OCR | local one-off MinerU + hard-page PaddleOCR-VL + orthography dictionary + human review | not at runtime |

Still use **LiteLLM** as the reading router (base/premium/fallback switching). The retrieval stack is assembled from the LlamaIndex library (no Dify, see §8). Local/offline compute **does not enter the tyche runtime**; it is only a development convenience for the one-off OCR ingestion.

**Claude cannot be reached directly in China (a hard operational constraint)**: the premium tier needs Claude, so either (a) the backend reaches Anthropic from overseas (cross-border data, compliance applies), or (b) route through a third-party gateway (sensitive birth data passing a third party, a privacy concern). **For a China-first product, prefer DeepSeek/Qwen as the base + Claude for premium (via an overseas backend); for an overseas/bilingual product, Claude as the base.** Decide by target market.

> **Historical note (deprecated)**: an early idea was to self-host Qwen for readings on local/shared GPUs (privacy / sunk cost / Qwen's strong Chinese), since replaced by "online APIs at query time". Shared compute does not enter the tyche runtime; local compute is only for the one-off OCR ingestion and small-model debugging, not a production host.

---

## 8. RAG framework selection: build on the LlamaIndex library (no Dify as the base)

> From multi-agent research + adversarial verification (2026-06). **Conclusion revised**: an earlier lean toward Dify (to reuse a ready Dify pipeline) was changed to **LlamaIndex (MIT) + self-hosted Qdrant**.

**Why not Dify/FastGPT (a paradigm mismatch, not a license issue)**:
- tyche's query is a structured object computed by the core (四柱/十神/格局/神煞 + school); it is essentially **programmatic metadata filtering + dense/sparse hybrid recall + reranker**, not chat-with-docs. A visual platform's knowledge base is designed for "user types -> auto-extract filter conditions", which is the wrong paradigm.
- And Dify/FastGPT have **historical bugs in passing through `metadata_condition` for External knowledge bases** (dify #16276/#27136, ragflow #8301, broken `in` operator #30188) — so the most critical school filter cannot rely on the platform.
- **License clarification (verified)**: Dify's multi-tenant clause only forbids "reselling Dify itself as a multi-tenant platform (one tenant = one workspace)"; **using it as your own product's backend is explicitly allowed** (`backend service for other applications`, confirmed by maintainer discussion #6476); the logo-removal clause only constrains the frontend and does not apply to pure-API mode. So Dify is **not a license line**, just a poor paradigm fit.

**Selection (by perspective)**:

| Perspective | Choice | Notes |
|---|---|---|
| **Long-term product (recommended)** | **LlamaIndex (MIT) + self-hosted Qdrant** | push chart features down to `MetadataFilters`/`FilterOperator` over the Qdrant payload; clean hookup of SiliconFlow bge-m3 (dense+sparse) + reranker; MIT poses zero blockers for closed-source SaaS, PIPL-compatible when self-hosted. For multi-step reading consensus, add `LangGraph` (MIT) |
| MVP speed-up (optional) | Dify as a **thin orchestration shell** | three rules: (1) wrap the whole retrieval chain as an **External Knowledge API** kept in your own Python (sidestepping the passthrough bug + keeping control); (2) email-confirm that pure-backend use is not multi-tenant; (3) do not bury business logic in the visual graph. Retreat to LlamaIndex on hitting an abstraction ceiling |
| classical OCR | **RAGFlow DeepDoc, offline one-off only** | export chunk+metadata after a run, not bound to online retrieval (the OpenAI-compatible hookup of SiliconFlow bge-m3 has pitfalls #8233/#9645) |

**What is borrowed is the "process shape", not the "endpoints"**: an existing KB pipeline's "layout parse -> LLM clean -> ingest -> recall test" is an **engineering pattern worth borrowing**; but tyche's retrieval backend uses LlamaIndex+Qdrant, with the model provider pointing entirely at the §7 online stack. Internal/offline compute is only borrowed during prototyping to validate retrieval quality; the production index must be built on the online SiliconFlow bge-m3 (never re-indexed).

### Pitfalls

1. **embedding fixed once, index built once**: a vector index is bound to its embedding model; changing the model means a full re-index. Fix the online **SiliconFlow bge-m3** on day one, same model for ingest and query, **never re-indexed**. Do not build the production index with a local/offline embedding model. LlamaIndex's default in-memory vector store does not support metadata filtering — **Qdrant is required**.
2. **命理 OCR ≠ general modern-document OCR**: MinerU suits modern regular PDFs; 命理 is vertical + traditional + variant + WPS self-made glyphs, and vertical is a known MinerU weakness that cannot read self-made glyphs. MinerU does layout + easy pages; hard pages (三命通会) still need PaddleOCR-VL / a vision LLM + the orthography dictionary + human review (see §6 risk 1). MinerU is AGPL, but **offline batch processing producing text data** is not infectious, so it is safe to use.
3. **pandoc reads .docx, not legacy .doc**: 星命抉古录 was a binary .doc; convert to .docx first, then to Markdown via pandoc.
4. **hybrid retrieval**: bge-m3 has sparse built in, but Qdrant must be configured for dense+sparse hybrid retrieval (LlamaIndex hybrid retriever) for it to be used, so that 命理 terms (伤官/七杀/偏印) hit exactly; do not use pure semantic search.
5. **Claude not directly reachable in China**: the premium tier reaches Anthropic directly from an overseas backend (no relay); see §9 on cross-border compliance.

---

## 9. Data security & compliance (PIPL)

> From multi-agent research + adversarial verification (2026-06). Before launch, the DPA and cross-border filing materials must be reviewed by a practising lawyer.

**Overall judgment: an all-third-party-API design can be compliant, but tyche is the un-outsourceable "personal-information handler". Safety does not depend on "whether third parties are used", but on "what is sent + what is signed with whom + whether data crosses the border".**

### A natural de-identification gate: the charting core

The charting core does a **lossy, many-to-one** transform locally from "birth instant -> 八字" (one 八字 maps to many instants within a year, and carries no birthplace) — this is itself a de-identification gate. What goes to embedding/rerank/LLM is **only de-identified chart features**; the raw PII never leaves the backend.

### Never-send list (a hard constraint; never leaves our own backend)
- Raw birth info: Gregorian/lunar year-month-day-time (to the minute), birthplace name, lat/long
- Direct identifiers: real name, phone, openid, device id, payment account
- The PII-to-chartId mapping table (the reverse key)
- **The charting core itself** (lunar-python computation must be in-process; outsourcing it means sending the raw instant out)
- Binding sensitive assertions to a real identity (treated as SPI: encryption + access audit, never into any external log/observability)

**Sendable (after de-identification)**: chart-feature 干支/十神/藏干/格局/神煞, 五行 旺衰, 大运/流年 ranges, school labels, question-category enums, chartId (pseudonym), classical passages.

### Per-hop data flow
| Receiver | Sends | Does not send |
|---|---|---|
| SiliconFlow bge-m3 | chart-feature string (e.g. "日主 庚 金, 身弱, 正官格, 伤官见官, 带羊刃") + school | birth date/time/place/name |
| SiliconFlow reranker | query (same) + candidate classical passages | same |
| Qwen/DeepSeek/Claude reading | chart features + retrieved passages + question category | **the year pillar gives only the 干支 "庚午年", not the Gregorian year**; the exact 大运 start date; name; place |

### Four data-minimization patterns (stacked)
- **A. Allowlisted egress (mandatory)**: the charting core is a non-bypassable middle layer; the egress payload follows an allowlist schema permitting only chart-feature fields; the serialization point asserts against `19xx-xx-xx`/`xx:xx`/lat-long/Chinese names, **covered by a CI unit test**.
- **B. chartId pseudonymization** (encouraged by PIPL §51): a UUID primary key; the PII-to-chartId map is stored, encrypted, and access-controlled separately; LLM context and logs carry only chartId. Note: pseudonymization is not anonymization — it is still personal information if reversible — but the exposure surface shrinks greatly.
- **C. Field-level encryption + short retention**: birth info is KMS envelope-encrypted on ingest, in a table separate from features; users may delete the raw text and keep only the chartId.
- **D. Vector-store data-plane split**: classical-corpus vectors (no PII) may be hosted; **the query path + chart-feature metadata are self-hosted (Qdrant)**. embedding/rerank is already one external handler; the vector store should not add a second.

### Provider data terms (by "no-training + retention" strength)
| Provider | Role | No training | Zero retention | Trade-off |
|---|---|---|---|---|
| Aliyun Bailian Qwen | domestic reading mainstay | official "never trains" (strongest) | no (legal retention, but **plaintext destroyed after a Model API call**) | **first choice**; use the raw Model API, not Assistant/app mode |
| SiliconFlow bge/reranker | embedding/rerank | yes | yes (no interaction data stored by default) | usable; sign a DPA, verify no sub-processing (upstream aggregation) |
| Anthropic Claude | premium | yes (default) | yes (**ZDR is not self-serve; needs enterprise sales approval + a separate contract**) | premium use; flagged content may be retained up to 2 years even under ZDR |
| DeepSeek | (cautious) | **unclear** (consumer side defaults to opt-in; the API terms are silent on self-training) | no | **weakest of the four**; if used, an enterprise DPA must lock down "no training + shortest retention + no sub-delegation" |

### Cross-border (only Claude)
DeepSeek/Qwen/SiliconFlow are all domestic and do not cross the border. Claude falls under PIPL §38/§39 cross-border: it needs **separate notice + separate consent**, and 命理 data is treated as sensitive, **so the 2024 "<100k people, non-sensitive" exemption does not apply**; in practice it goes through a **standard-contract filing** for personal-information export. Routing through a third-party gateway **both loses Anthropic ZDR (third-party integrations are out of ZDR scope) and adds an uncontrolled overseas processor**. So for the premium tier, first assess whether domestic Qwen can substitute; if Claude is truly needed, **build a direct overseas backend + enterprise ZDR + a standard-contract filing, with no relay**, and enable it only for paying users who have explicitly authorized export.

### PIPL action list
- **SPI classification**: treat 命理 data conservatively as SPI (linked to religious belief / specific identity, readings touch health/wealth, may involve minors; the §28 "etc." catch-all).
- **Four separate consents (each independently ticked, not bundled with the master agreement)**: (1) processing SPI; (2) provision to third-party processors (list each receiver SiliconFlow/Qwen/DeepSeek/Claude with name/purpose/data type); (3) cross-border (Claude only); (4) the right to an explanation of automated decisions (§24/§73; a reading is an automated inference, so provide an explanation and a way to refuse purely automated processing).
- **Privacy policy**: disclose "raw birth info never leaves our servers, only de-identified chart features go out" as a **compliance selling point**; include the field list (marking SPI), third-party receivers + DPA, retention periods, user rights, minors (guardian consent under 14 + the whole record escalated to SPI), security measures, and the DPO / complaint channel.
- **Contracts**: sign a **DPA** separately with SiliconFlow/Aliyun/DeepSeek/Anthropic (no training + zero or shortest retention + no sub-delegation + security responsibility); Anthropic via an enterprise contract + ZDR + a cross-border standard-contract filing.
- **Run a PIA and keep it for at least 3 years**; consent withdrawal executes in one click and cascades to deleting the raw PII + exercising deletion/no-retention requests with the vendors.
- Classical corpus: OCR ingestion concerns publicly published works, so **copyright risk > privacy risk**; just confirm it contains no personal information.

---

## 10. Code vs RAG: triaging corpus content (the guiding principle for M2 ingestion)

**Core: do not dump the 3 PDFs + 1 doc into RAG wholesale. The content differs in nature, so it must be handled differently.**

| Type | Examples | Destination |
|---|---|---|
| **A. deterministic rules** | building the four pillars, 五虎遁/五鼠遁, 纳音, 十神 definitions, 神煞 derivation, 刑冲合害, 十二长生, starting 大运 | **code / data tables**, not a RAG judgment source |
| **B. semi-structured judgments** | 格局 conditions, 用神 selection, 旺衰 standards, 化气 success/failure | **rule engine (YAML/DSL)**, with RAG aiding the fuzzy/school parts |
| **C. broad readings / discourse** | rhapsodies, case commentary, philosophy, readings like "a strong day master with vigorous 财官 brings wealth and rank" | **the RAG body** |

Principle: **structure (does it hit / hold) = code; meaning (auspicious/ominous, character, events) = RAG**. For the same 神煞, the derivation (which pillar it hits) goes in code, the reading (what it means) goes in RAG.

**Why A does not go into RAG**: handing a deterministic computation to retrieval + LLM produces wrong answers / hallucinations; a code table lookup is always right and testable.

**Code "duplicating" the books is intentional design**: the book is the spec, the code is the verified impl. Rules are extracted from the books once (human-verified), encoded, and at runtime the code is authoritative — **RAG does not re-derive rules on each query**. The existing charting/十神/神煞/十二长生 code already turns the books' formulas/tables into deterministic code (each step hand-verified: 五虎遁, 五鼠遁, 临官=禄, 十神 generation/control).

**Key safeguard (against code and RAG fighting)**: chart facts are authoritative from the code; RAG passages are only for interpretation + citation. The reading prompt states "the chart below is already computed (do not recompute); the classical passages are for interpretation only", so the LLM does not recompute a contradictory chart from retrieved formulas.

**M2 ingestion flow (accordingly)**: OCR -> **split by A/B/C** ->
- type A (formulas/tables): mostly already in code; ingested and tagged "rule", used at retrieval mainly for **citation** (so a reading can quote the original), not as a judgment source;
- type C (readings/discourse): the RAG body, tagged with metadata (school/era/book/applicable 格局/involved 神煞/十神 combination);
- closing the loop with §8: **the 格局/神煞/旺衰 the code computes = the metadata filter keys for retrieval**, recalling the matching type-C readings. Code produces structure, RAG provides language, each to its own role.
