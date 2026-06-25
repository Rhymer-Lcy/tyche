# tyche Knowledge-Base Ingestion Spec (type-C readings -> RAG chunks)

> Companion to [architecture.md](architecture.md) §8/§9/§10. This file is the **single spec** for
> OCR -> clean -> structure; both the extraction-agent workflow and human review follow it.

## 0. Guiding principle: content triage (see architecture §10)

| Type | Content | Destination | Ingestion handling |
|---|---|---|---|
| **A deterministic rules** | derivation formulas, 纳音 tables, 十神 definitions, 神煞 derivation, 刑冲合害, 十二长生 | already in code | tag `rule_type=A`, used only for **citation** (original attached at retrieval), **not as a judgment source** |
| **B semi-structured judgments** | 格局 conditions, 用神 selection, 旺衰 standards, 化气 success/failure | rule engine (incremental) | tag `rule_type=B`; may sit in RAG until ruled |
| **C broad readings / discourse** | rhapsodies, cases, philosophy, readings like "a strong day master with vigorous 财官 brings wealth" | **the RAG body** | tag `rule_type=C`, full metadata |

**Principle: structure (does it hit / hold) = code; meaning (auspicious/ominous, character, events) = RAG.** A RAG chunk carries only "meaning", never "algorithm".

## 1. Chunk field spec

Each chunk is one JSON record. Minimum viable = `id / source / rule_type / text / school / at least one filter key / OCR provenance fields`.

```json
{
  "id": "minglijinghua-论妻财-001",        // {book-slug}-{section-slug}-{seq}, globally unique
  "rule_type": "C",                         // A | B | C (see §0)
  "source": {
    "book": "彭康民命理精华",                // see the §3 book table
    "section": "第三节 论妻财",              // the source chapter (as read)
    "page": 6                               // page in the source book / PDF
  },
  "text": "男以财为妻……财星得位则妻贤;财星无气、比劫夺财则克妻或妻不得力。",  // cleaned reading text (for RAG retrieval / feeding the LLM)
  "source_quote": "男以財為妻……",          // verbatim original (for fidelity check / citation, keeping the original glyphs)
  "school": "ziping",                       // §2.1
  "topic": ["婚姻感情"],                     // §2.2, may be multiple
  "shen": ["正财", "偏财", "比肩", "劫财"],   // §2.3, the 十神 involved
  "gewu": [],                               // §2.4, the 格局 involved
  "shensha": [],                            // §2.5, the 神煞 involved
  "relations": [],                          // §2.6, the 刑冲合害 involved
  "palace": ["日支(妻宫)"],                  // §2.7, the palace involved
  "strength_applies": [],                   // §2.8, applicable 旺衰 levels (empty = any)
  "confidence": "medium",                   // high | medium | low (extraction confidence)
  "needs_review": true,                     // whether human review of the original is needed
  "ocr_method": "mineru",                   // glyph source: mineru (primary for modern horizontal) / paddleocr-vl (hard-page glyph anchor)
  "raw_image_ref": "minglijinghua/p6",      // traceable source page (book-slug/page)
  "notes": ""                               // variant / uncertain glyphs, caveats
}
```

### Field rules
- **Keep `text` and `source_quote` separate**: `text` is the retrieval body after cleaning (to Simplified, restored punctuation, OCR noise removed); `source_quote` keeps the verbatim original. **Any reading cited as classical must trace back to source_quote + raw_image_ref for verification.**
- **Metadata values may only come from the controlled vocabulary (§2)**: they must be **byte-for-byte identical** to the output of the code's `analyze()`, or "computed feature -> filtered recall" cannot match. Leave empty if unsure; do not invent terms.
- **Uncertain extraction -> tag `confidence:low` + `needs_review:true` + note which glyph is in doubt in `notes`**; **never treat a suspected glyph as certain** (better blank than wrong).

## 2. Controlled vocabulary (must align with code output)

### 2.1 school
`ziping` (子平) | `luming` (禄命) | `xingming` (星命) | `mixed` (a synthesis, e.g. 三命通会)

### 2.2 topic (subject, multi-select)
`性格气质` `事业官运` `财运` `婚姻感情` `六亲-父母` `六亲-兄弟` `六亲-子女` `健康疾厄`
`学业功名` `寿元` `大运流年` `格局总论` `用神喜忌` `旺衰强弱` `神煞论断` `刑冲合害论` `其他`

### 2.3 shen — 十神 (aligned with `ten_god` output)
`比肩` `劫财` `食神` `伤官` `正财` `偏财` `正官` `七杀` `正印` `偏印`
(note: `日元/年元` mark the self and are not used in a chunk)

### 2.4 gewu — 格局 (aligned with `pattern.py` output)
`正官格` `七杀格` `正财格` `偏财格` `正印格` `偏印格` `食神格` `伤官格` `建禄格` `月刃格`

### 2.5 shensha — 神煞 (aligned with `data/shensha.yaml`)
`天乙贵人` `文昌贵人` `禄神` `羊刃` `驿马` `桃花` `华盖` `将星` `孤辰` `寡宿` `空亡`
(add a new 神煞 to shensha.yaml first; this list then extends)

### 2.6 relations (aligned with `relations.py` type)
`地支六合` `地支六冲` `地支六害` `地支六破` `三合局` `半合` `三会方` `三刑` `相刑` `自刑`
`天干五合` `天干相冲`

### 2.7 palace
`年柱(祖上/早年)` `月柱(父母兄弟/事业宫)` `日支(妻宫/配偶)` `时柱(子女/晚年)` `命宫` `胎元` `身宫`

### 2.8 strength_applies — 旺衰 (aligned with `strength.py` level)
`强` `偏强` `中和` `偏弱` `弱` (empty array = any 旺衰)

## 3. Book table (slug = chunk-id prefix / `source.book` registry key)

Physical archive at `docs_local/{slug}/` (source/ + mineru/); the index is `docs_local/README.md`.

slug = folder name = chunk-id prefix (full pinyin of the title; no author, no abbreviation).

| slug | source.book (Chinese) | author | default school | pages | text source |
|---|---|---|---|---|---|
| `minglijinghua` | 命理精华 | 彭康民 | ziping (modern, with 星命 flavor) | 50 | MinerU (modern horizontal, good quality) |
| `yujingaojue` | 玉井奥诀 | attrib. 张果 | ziping (classical 格局/用神) | 24 | MinerU (literary formulas; not "accurate", needs human review) |
| `sanmingtonghui` | 三命通会 | 万民英 | mixed (school per chapter: ziping/luming) | 295 | MinerU, split p001-148/p149-295, **vertical archaic glyphs need heavy human review** |
| `xingmingjueguilu` | 星命抉古录 | 止止居士 | luming/xingming (神煞 as the frame) | ~54 | pandoc (docx -> gfm md, already clean traditional Chinese) |

> Physical archive at `docs_local/{slug}/`: PDF sources in `mineru/` (MinerU), docx sources in `pandoc/` (pandoc).

> **三命通会 split paging**: the second part `p149-295` has MinerU `page_idx` starting at 0, so at ingestion `source.page = page_idx + 1 + 148` restores the source page number.

### Consuming MinerU JSON (the pipeline reads `docs_local/{slug}/mineru/*.json` accordingly)
Top-level dict -> `pdf_info[]` (one element per page): use `page_idx` (page), `para_blocks[]` (body blocks: `type` title/text/table, `index` reading order, `bbox` for traceability, `lines[].spans[].content` for text); `discarded_blocks` are headers/footers, skipped. Glyphs are guaranteed by MinerU; we only do triage + metadata + chunking.

## 4. Chunking granularity
- **One reading / one independent point = one chunk**; do not glue a whole section into one block, nor shatter it to half-sentences.
- A case (e.g. "丙戊 乙未 庚戌 乙酉") goes with its reading into the same chunk's `notes`, or becomes its own `rule_type=C` case block.
- Target: 50–300 characters per chunk, semantically self-contained (still understandable when retrieved out of context).

## 5. Downstream safeguard (for the reading LLM)
A retrieved chunk is only for "interpretation + citation". The reading prompt must state: **"the chart facts are computed by the program, do not recompute; the classical passages below are for interpretation only, cite the source"** — to stop the LLM from recomputing a chart that contradicts the code out of the formulas in a passage.

## 6. Ingestion flow (finalized after a 10-page double-read adversarial pilot, 2026-06)

> **Final conclusion**: the pilot showed that "letting an LLM read glyphs straight from images (glyph OCR)" is unsafe, so it is fixed as: **glyphs are guaranteed by MinerU (hard pages via PaddleOCR-VL); the LLM only does triage / cleaning / metadata / re-reading on the MinerU text**. The LLM extraction and QC details in §6.1–6.5 below apply to "triage and tagging over MinerU text", with the LLM no longer reading glyphs.

### 6.0 Key pilot findings (they decide the whole pipeline)
- Independent re-read judgment on 124 chunks: **accurate 65% / minor 11% / wrong 23%**. Nearly a quarter are meaning-altering errors — **a raw LLM glyph-OCR ingestion is unacceptable**.
- **An LLM is not OCR; it is "recognize + understand + rewrite at will"**. It has a fatal flaw a dedicated OCR lacks: on **clearly legible** glyphs it "corrects on assumption / fabricates / rewrites whole sentences" (e.g. 彭振军->彭振华, 本象配本->配木, a whole fabricated quote on a clear image).
- **Self-reported confidence is untrustworthy**: 17 `confidence=high` entries were in fact wrong. **The pass criterion must be "independent re-read fidelity", not the model's self-reported confidence.**
- **The bottleneck is hallucination, not resolution**: all errors were on high-res images; 300 dpi is enough, 600 dpi does not help.
- **Text type determines the error rate**: modern vernacular (彭康民) wrong 11%; literary formulas / self-referential terms (玉井) wrong 37%. The older and terser, the more hallucination.
- Metadata alignment is a plus for the LLM (almost no invented terms), but "field cross-use (神煞 leaking into shen) / over-inferred tags" need rule interception.
- Limitation: both books in this batch are **modern horizontal reprints**; true vertical / handwritten / variant glyphs are not covered and need separate testing.

### 6.1 A three-layer pipeline (extraction output is never ingested directly)
```
MinerU layout parse to text (glyphs guaranteed by MinerU; hard handwritten/vertical pages via PaddleOCR-VL glyph anchor)
  -> (1) LLM triage: A/B/C split + type-C cleaning + metadata on the MinerU text (the LLM's strength: understanding + chunking + tagging, not glyph reading)
  -> (2) LLM independent re-read check (full, in a fresh session not seeing (1)): verify source_quote against the MinerU text + field attribution
  -> (3) rule-triggered human review (only what needs it)
  -> ingest: LlamaIndex chunk -> SiliconFlow bge-m3 embed -> Qdrant (dense+sparse hybrid + payload filtering)
```

### 6.2 Pass criterion (not self-reported confidence)
- only `re-read fidelity = accurate` and no field violation -> auto-ingest;
- `minor_error` -> light-review queue;
- `wrong / not_found` -> mandatory re-extraction + human review.

### 6.3 Hard human-review triggers (any one triggers review)
- re-read fidelity in {wrong, minor_error};
- the chunk contains a **name / place / 八字 干支 / quotation** (regex hit) — one wrong character is an error with no contextual safety net;
- `source_quote` length < 30 chars (short literary blocks are low-redundancy, high-hallucination);
- a metadata **field-vocabulary attribution conflict** (e.g. a 神煞 name in the 十神 field);
- inconsistent `school` tagging within one piece;
- extraction `confidence=low` or `needs_review=true`;
- **character-level diff between the extraction and re-read source_quote exceeds a threshold** (strongly recommended: alert beyond "punctuation normalization only" to auto-catch dropped characters / whole-block hallucination).

### 6.4 Required engineering validators (machine, zero-cost)
- **Field-attribution validator**: each metadata field's values must belong to its §2 vocabulary (no 神煞 in shen, etc.);
- **source_quote<->text diff limit**: allow only punctuation normalization, alert beyond a character-level threshold;
- **Extraction-prompt hard constraint**: state explicitly "**copy rare or unusual glyphs from the source verbatim; never correct / normalize / complete them by common sense**" — directly suppressing the most dangerous "rewrite on assumption".

### 6.5 Per-book strategy
- **Modern vernacular (彭康民 and similar)**: dual-LLM (extract + re-read) auto-check; human review covers only "non-accurate + a 5% random sample" (~1-3 per page), close to production-ready.
- **Literary / classical (玉井 and similar)**: a high wrong rate makes auto-pass meaningless. Default to **per-item human review of every non-accurate + 100% review of short literary blocks (≤30 chars)**; for now treat it as a "draft generator with metadata".
- **A stronger option**: for classical/vertical, bring in a dedicated OCR (e.g. PaddleOCR-VL) only as a **glyph anchor** and diff it against the LLM's source_quote — using the deterministic OCR's "obvious errors" to catch the LLM's "errors that look right". The LLM still handles chunking + understanding + metadata.
