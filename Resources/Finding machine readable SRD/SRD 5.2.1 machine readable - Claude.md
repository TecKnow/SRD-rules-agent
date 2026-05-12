# D&D SRD 5.2 for a RAG Pipeline: Datasets, Tooling, and Chunking Strategy

**Bottom line:** For a capstone RAG agent answering rules questions against the official 2024 ruleset, start with **`downfallx/dnd-5e-srd-markdown`** (CC-BY-4.0, complete SRD 5.2.1 in clean Markdown) as your primary corpus, supplement structured stat-block/spell metadata from **Open5e API v2** (filtered to `document__key=srd-2024`), and keep the official **`SRD_CC_v5.2.pdf`** in reserve as ground truth for spot-fixing parsing errors. There is no fully complete, structured JSON dataset of SRD 5.2 yet (community efforts are ~80–95% there as of mid-2026), so a Markdown-first ingestion path with structure-aware chunking is the most pragmatic option.

---

## TL;DR

- **Official source:** WotC publishes SRD 5.2.1 only as a 361-page PDF at `https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.pdf` (or the current `.../SRD_CC_v5.2.1.pdf`) under CC-BY-4.0; landing page is `https://www.dndbeyond.com/srd`. There is no official HTML, JSON, YAML, or Markdown release. SRD 5.1 (2014 rules) is a separate, also-CC-BY-4.0 document — make sure you grab 5.2/5.2.1, not 5.1.
- **Best ready-made starting point for RAG:** `github.com/downfallx/dnd-5e-srd-markdown` (full SRD 5.2.1 in Markdown, CC-BY-4.0, ~360 pages, ~500 spells, ~400 monsters, all 12 classes). Backup/cross-check options: `github.com/springbov/dndsrd5.2_markdown` (single-file MD, marker-generated, "largely done" but inconsistently formatted), `github.com/your5e/5e-srd-markdown` (cleaned MD + Obsidian vault, structured pipeline), and the `dmdocs.vercel.app` site with structured MDX + frontmatter.
- **Structured (JSON) datasets are still incomplete for 2024:** Open5e exposes `srd-2024` content via `https://api.open5e.com/v2/` (filter `?document__key__in=srd-2024`) — actively maintained, but with known data bugs being cleaned up through 2025–2026. The `5e-bits/5e-database` (`dnd5eapi.co`) repo has a `/api/2014` endpoint live and `/api/2024` partially populated (subclasses, magic items, subspecies landed in releases v4.5–v4.6). Neither is yet 1:1 complete with SRD 5.2.1 — plan to fill gaps from Markdown.

---

## Key Findings

### 1. Official source material

| Item | Detail |
|---|---|
| Current version | **SRD 5.2.1** (released May 1, 2025; SRD 5.2 itself dropped April 22, 2025) |
| Format | **PDF only** (built in MS Word, exported to PDF; bookmarks but no HTML/JSON release) |
| Pages | 361 pages, ~5.68 MB |
| Direct download | `https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.pdf` (and updated `SRD_CC_v5.2.1.pdf` per the D&D Beyond SRD page) |
| Landing page | `https://www.dndbeyond.com/srd` |
| Mirror (verified CC-BY-4.0) | `https://commons.wikimedia.org/wiki/File:Dungeons_%26_Dragons_System_Reference_Document_v5.2_(2025).pdf` |
| License | **CC-BY-4.0** (irrevocable). Required attribution string: *"This work includes material from the System Reference Document 5.2 ('SRD 5.2') by Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2 is licensed under the Creative Commons Attribution 4.0 International License, available at https://creativecommons.org/licenses/by/4.0/legalcode."* — bake this into a `LICENSE`/`ATTRIBUTION.md` in your repo and into any UI footer your agent emits. |
| Conversion guide | WotC publishes a "Converting to System Reference Document 5.2.1" guide tagging `[New Rule]`, `[Revised Rule]`, `[New Name]` — useful if you want to generate a 2014→2024 diff index. |

**SRD 5.1 vs 5.2 — get the right one.** SRD 5.1 covers the 2014 rules; SRD 5.2 covers the 2024 rules ("5.5e" on D&D Beyond). 5.2 added: weapon mastery properties, Bastions/crafting tweaks, 3 backgrounds (Criminal, Sage, Soldier), 2 species (additions), ~16 feats, all 12 classes (one subclass each, e.g., Champion Fighter, Life Cleric), expanded glossary, exploration rules, ~325 stat blocks reflecting the 2025 Monster Manual, plus renamings to avoid trademarks (Deck of Many Things → "Mysterious Deck"; Orb of Dragonkind → "Dragon Orb"). 5.2 explicitly **excludes** Artificer, Aasimar, Beholder, Mind Flayer, Strahd/Orcus/Tiamat references, and Planes-of-Existence/Great Wheel cosmology. Both 5.1 and 5.2 remain available under CC-BY-4.0 — many 2014 rules questions still resolve only via 5.1, but for a 2024-rules agent, build on 5.2.1.

### 2. Ready-made machine-readable datasets

I evaluated the major candidates. Below they are ordered roughly by usefulness for a 2024-rules RAG project.

#### A. `downfallx/dnd-5e-srd-markdown` — **recommended primary corpus**
- **URL:** `https://github.com/downfallx/dnd-5e-srd-markdown`
- **Maintainer:** downfallx
- **License:** CC-BY-4.0 (correctly inherits SRD license; `LICENSE` in repo)
- **Format:** Markdown (GitHub-flavored), broken into logical files (e.g., `classes.md`, `spells.md`, `monsters-A-Z.md`)
- **Coverage:** Full SRD 5.2.1 — all 12 classes, "500+ spells, 400+ monsters," all gameplay/equipment/magic-item rules. README explicitly claims "complete D&D 5e (2024) System Reference Document 5.2.1."
- **Edition:** **SRD 5.2.1 (2024)**
- **Activity:** Recently created and live; community-maintained Markdown conversion (the README warns this is an "independent conversion" and may have minor errors).
- **Quality:** Clean, GitHub-flavored Markdown tables, useful headings, designed for grep-style queries. Quality has not been independently audited at scale, but the file structure (one logical concept per heading) is the best out-of-the-box for RAG ingestion.
- **RAG fit:** ★★★★☆ — chunkable on `##`/`###` headings out of the box; spells/monsters/items are already contiguous blocks under named headings; minimal cleaning needed.

#### B. `springbov/dndsrd5.2_markdown` — useful cross-check / fallback
- **URL:** `https://github.com/springbov/dndsrd5.2_markdown` (38 stars, 12 forks, 49 commits, 1 PR open)
- **License:** CC-BY-4.0
- **Format:** Markdown — single big file `DND-SRD-5.2-CC.md` plus split files in `src/`. Custom extension: tables prefixed by `Table: <caption>`.
- **Coverage:** Full SRD 5.2 (says project is "roughly complete and currently should be widely useable"); monster section was the roughest output and was patched in part with Mike Shea's Lazy GM Tools statblocks.
- **Edition:** SRD 5.2 (the original release; not yet updated to 5.2.1's 15-magic-item correction in all places).
- **Process:** Maintainer used **`marker`** (the Vik Paruchuri PDF→MD tool) for the base extraction, then hand-cleaned. Author explicitly states "I likely won't accept any [PRs] as the project is largely done" — so don't expect ongoing maintenance.
- **Quality concerns (per EN World thread):** "Dragons missing proficiency bonuses, Initiatives wrong, missing magic items, Small creatures that are (now?) actually Tiny… plus the formatting" was inconsistent (8–9 different Word styles in the underlying conversion). Treat as a usable starting point that **needs auditing** — not authoritative.
- **RAG fit:** ★★★☆☆ — viable, but plan to spot-check stat blocks against the source PDF.

#### C. `your5e/5e-srd-markdown` — strongest cleaning *pipeline*
- **URL:** `https://github.com/your5e/5e-srd-markdown`
- **License:** CC-BY-4.0
- **Format:** Markdown plus a packaged Obsidian vault (with cross-links) and "broken into sections" variant. Provides both 5.1 and 5.2.1.
- **Coverage:** SRD 5.1 fully; SRD 5.2.1 conversion in progress with documented patches and fixes (e.g., fixed numbering of D20 test steps from "4–6" to "1–3"; reformatted monster ability tables to score/modifier/save layout; broke multi-header tables apart).
- **Process:** Uses `marker` for base PDF→MD, then layered Python filters (`clean_srd.py`, `update_vault.py`) with per-filter test suites and integration tests. Patches kept separate from content so regression tests still compare the cleaned MD to the original.
- **RAG fit:** ★★★★☆ — if you want to do your *own* conversion with high fidelity, fork this scaffolding rather than rolling from scratch. Excellent reproducibility/test discipline.

#### D. `oldmanumby/DND.SRD.Wiki` and the `sycarion/5e-2024-SRD` fork
- **URL:** `https://github.com/OldManUmby/DND.SRD.Wiki` (the 5.1 gold standard) and `https://github.com/sycarion/5e-2024-SRD` (a fork updating to 5.2.1)
- **License:** CC-BY-4.0
- **Format:** Markdown (.md), Word (.docx), Adobe ICML, with Obsidian-friendly variants and Obsidian wikilinks for spell lists.
- **Edition:** Old Man Umby's repo is **SRD 5.1** (line-by-line painstaking conversion plus 2018 errata) — the most polished community 5.1 markdown, but **not yet 5.2.1**. The `sycarion/5e-2024-SRD` fork is targeting 5.2.1 and is "in progress."
- **RAG fit for 5.2:** ☆☆☆☆☆ today (only 5.1 complete); ★★★★☆ if/when sycarion finishes — keep it on a watch list.

#### E. `dmdocs.vercel.app` + its hidden GitHub repo
- **Site:** `https://dmdocs.vercel.app/docs` — "LLM-optimized D&D 5th Edition System Reference Document," covers SRD 5.2.1.
- **What's in the repo (per author on EN World, late 2025):** "Structured Markdown for all 360 pages of SRD 5.2.1; spells, monster stat blocks, and magic items as **MDX files with clean metadata / frontmatter**; scripts for verifying content against the SRD." Roadmap mentions adding JSON/YAML/TOML exports and an `llms.txt`.
- **Caveat:** The dmdocs site is live, but as of my searches I could not verify the public GitHub URL/license — **check before using**. The EN World poster implied the source is on GitHub but did not link it in the snippets I found.
- **License:** SRD 5.2.1 content is CC-BY-4.0 with attribution; site footer confirms this. Repo license must be confirmed.
- **RAG fit:** ★★★★★ structurally (MDX frontmatter is *exactly* what you want for vector-DB metadata), but only if the repo is public and licensed compatibly.

#### F. Open5e (`open5e/open5e-api` + `https://api.open5e.com`)
- **URLs:** `https://github.com/open5e/open5e-api`, `https://github.com/open5e/open5e`, live API at `https://api.open5e.com/v2/`.
- **License:** Code is open-source (MIT-style, see repo); SRD content carries CC-BY-4.0; non-SRD additions (Tome of Beasts, etc.) are OGL/CC mixed — filter strictly by `document__key__in=srd-2024` to stay clean.
- **Format:** REST/JSON via Django REST Framework; v2 endpoints for `/creatures`, `/spells`, `/magicitems`, `/classes`, `/backgrounds`, `/feats`, `/conditions`, `/rulesets`, `/items`, etc. Each entry has structured fields (CR, type, level, school) plus a Markdown `desc`.
- **Coverage (SRD 5.2 / `srd-2024`):** Actively populated through 2025–2026. Release notes show steady ingestion: Backgrounds added (PR #832), magic items endpoint (PR #835), Character Creation rules from `srd-2024` (PR #878), Fighter Two Extra Attacks (PR #895), Adult Green Dragon spellcasting (PR #891), spell markdown bug fixes (PRs #857, #859, #870), CR field consolidation (PR #910), Goliath markdown fixes (PR #909). The pattern is clearly "ship, then iterate fixes" — coverage is broad but you should expect data bugs in long-tail content.
- **Quality:** Best-in-class for *structured* querying (filters: spell level, school, monster type/CR, environment) but I could not retrieve live entry counts via direct API fetches in this report. Recommend a one-time crawl with a filter audit against the SRD 5.2.1 PDF table of contents to find gaps.
- **RAG fit:** ★★★★★ for metadata; ★★★☆☆ for narrative/rule prose, since longform rule chapters (Combat, Spellcasting, Equipment) are not all exposed as discrete endpoints — those still come from `/rulesets/`.

#### G. `5e-bits/5e-database` and `5e-bits/5e-srd-api` (`dnd5eapi.co`)
- **URLs:** `https://github.com/5e-bits/5e-database` (868 stars, 414 forks, 19 open issues, MIT license; data is OGL 1.0a) and `https://github.com/5e-bits/5e-srd-api`.
- **Edition status:** API is currently versioned at `/api/2014`. **`/api/2024` is "next" but not live as of the latest README.** The database repo *is* shipping 2024 data in releases — v4.5.x added 2024 Dragonborn/Goliath subspecies, v4.6.0 added 2024 Magic Items and an initial Subclass pass, latest tagged release is **v4.4.0 (Mar 14, 2026)** for the parent project. So the JSON files exist in the repo but the public REST endpoint hasn't switched on the 2024 namespace yet.
- **License flag:** Repo README says "underlying material is released using the Open Gaming License Version 1.0a." That's fine for SRD 5.1 content but **2024 SRD content is CC-BY-4.0, not OGL** — if you're pulling 2024 data from this repo, treat the underlying SRD material as CC-BY-4.0 and attribute WotC accordingly.
- **RAG fit (for 2024):** ★★☆☆☆ today — coverage is partial and the hosted API doesn't expose 2024 yet. Re-evaluate if/when `/api/2024` ships.

#### H. `vorpalhex/srd_spells`, `BTMorton/dnd-5e-srd`, `soryy708/dnd5-srd`, the `tkfu` monster gist
- All are **SRD 5.1 / 5.0** only (BTMorton's `LICENSE` is OGL 1.0a covering "SRD 5.0"). Useful for comparison or 2014-rules support but **not** suitable for a 2024-only agent.

#### I. Hugging Face datasets
- **`datapizza-ai-lab/dnd5e-srd-qa`** — **highly relevant.** A Q&A dataset built explicitly from "20 Markdown documents parsed from the D&D 5e SRD PDF," version SRD 5.2.1, 56 question-answer pairs across Easy/Medium tiers, designed to **evaluate RAG systems**. Each item carries `document_path`, `start_char`, `end_char` for the source passage. CC-BY-4.0. Use this as your evaluation set, not training corpus.
- `jason-oneal/dnd-5e-dataset` — Alpaca-format instruction tuning dataset, edition unspecified, suitable only for fine-tuning experiments.
- `0xJustin/Dungeons-and-Diffusion`, `microsoft/crd3` (Critical Role transcripts), `zhudotexe/FIREBALL` — not relevant to SRD rules QA.

#### J. VTT compendium exports
- **Foundry VTT `dnd5e` system** (`github.com/foundryvtt/dnd5e`) — official-ish support; release notes (v5.2.0, v5.3.x) explicitly cite SRD 5.1 *and* SRD 5.2 attribution. JSON-derived compendium packs are bundled. License is mixed (system code MIT-style, SRD content CC-BY-4.0). Caveat: data is shaped for Foundry, not generic ingestion — you'd need to write a small extractor against the LevelDB pack format.
- The various `5e-complete-*` Foundry forks pull in non-SRD WotC content; **avoid for any commercially licensed pipeline.**
- **5etools** had its source DMCA'd by WotC in **August 2024** (`github.com/github/dmca/blob/master/2024/08/2024-08-07-wizards-of-the-coast.md`) precisely because it included full text of WotC books beyond the SRD. **Do not use 5etools data** in your project; it is not licensed for redistribution and using it puts your bootcamp project at legal risk.
- Roll20 has a JSON compendium endpoint (e.g., `https://app.roll20.net/compendium/dnd5e/Fireball.json`), and Roll20's pages explain SRD 5.2 publishing rules, but bulk scraping is against their ToS; don't build on it.

### 3. DIY parsing tooling — if you want to roll your own from the PDF

The SRD PDF is a 2-column, table-heavy, sidebar-rich, stat-block-heavy 361-page document built in Word. This is a worst-case layout for naive PDF text extraction. Rough tradeoffs from 2025–2026 benchmarks:

| Tool | Best for | Watch-outs for SRD 5.2 |
|---|---|---|
| **Marker** (`VikParuchuri/marker`) | Default first pass — this is what `springbov` and `your5e` both used. Open-source, runs locally on GPU/CPU, outputs Markdown with tables. | Generated output needs hand-cleanup, especially monster/animal stat blocks; line-break artifacts are common. |
| **PyMuPDF / `pymupdf4llm`** | Multi-column detection (`column_boxes`), `to_markdown()` for LLM/RAG ingestion. Fast, deterministic, no API. | Table extraction is hit-or-miss on tables without gridlines (which SRD has *plenty* of); plan to write per-table fixes. |
| **pdfplumber** | Surgical table extraction with explicit `vertical_strategy`/`horizontal_strategy` controls. | Slower, more code per table; better for one-off table rescues than full-doc passes. |
| **Docling** (IBM) | Strong structural preservation; outputs Markdown with element types (title/para/list/table/caption); good local option. 2025 benchmarks rate ~94%+ on numerical tables. | Heavier dependency footprint; struggles with currency-style notation and footnotes (less relevant for D&D). |
| **LlamaParse** (LlamaCloud) | Highest accuracy on complex tables in 2025 head-to-heads; ~17s on a doc that took Marker 6 minutes. | Cloud-only, paid beyond a free 10k-credit/month tier — check costs for 361 pages. Multi-column layout handling weaker than Marker/Docling per Firecrawl's 2026 review. |
| **Unstructured.io** | Element-based partitioning out of the box (good for structure-aware chunking). | 2025 benchmarks (Reducto, Procycons, Medium reviews) show quality regressions and slow throughput (~51s for a single page on certain benchmarks); not the consensus first pick anymore. |
| **LLM-assisted (Claude/GPT/Gemini Vision)** | Final-mile cleanup — feed page images plus the marker/PyMuPDF text and ask for a structured JSON record per stat block. | Cost scales with pages; non-deterministic — pin temperature to 0 and cache results. Excellent for the ~325 stat blocks where layout matters most. |

**Pragmatic recipe** if you DIY: run **PyMuPDF/`pymupdf4llm`** for the prose chapters (Playing the Game, Combat, Spellcasting, Equipment, Magic), use **Marker** for spells (which are list-like) and magic items, and use **LlamaParse** (or an LLM pass with the page rendered to image) for the **monster stat blocks**, since that's where every other tool is weakest. Total estimated effort: **20–40 hours** to get to 95% fidelity, plus another 10–20 to round out edge cases (e.g., spell tables with multi-row headers, the class progression tables with their stacked "Spell Slots Per Level" header that springbov flagged, sidebar callouts, and the rules glossary's nested definitions).

### 4. Chunking strategy implications per dataset option

The 2024 RAG-chunking literature (Firecrawl 2026, Weaviate, Glukhov, arXiv 2504.19754, arXiv 2601.14123) converges on three points relevant here: (1) **structure-aware (element-based) chunking beats fixed-size** when documents have strong heading hierarchy — which the SRD does; (2) **semantic peaks around ~500 tokens for explanation-style queries and ~2.5k tokens for factoid recall** ("BERTScore peaks at small contexts; EM peaks at larger"); (3) **overlap provides little measurable benefit** on well-structured corpora and increases cost. Apply this to each dataset:

| Dataset | Natural chunk boundary | Recommended chunking | Filterable metadata to extract | Prep needed |
|---|---|---|---|---|
| `downfallx/dnd-5e-srd-markdown` | `##`/`###` headings, plus one-spell-per-`####`, one-monster-per-`###` | **Heading-based recursive splitter** (LangChain `MarkdownHeaderTextSplitter` or LlamaIndex equivalent), max ~1.5–2k tokens per chunk, no overlap. | `section`, `subsection`, `entity_type` (spell/monster/item/rule/class), `name`, `class` (for class features), `level`/`spell_level`, `school`, `cr`, `source_page` if you keep page anchors | Strip HTML/markdown tables that don't fit your embedding window into a separate `tables` collection. Add a frontmatter step: parse stat blocks with regex (e.g., `^Armor Class \d+`, `^Hit Points \d+`, `Challenge \d+`) to extract typed fields. |
| `springbov/dndsrd5.2_markdown` | Single big file plus split files; custom `Table: <caption>` markers | Same as above, but **audit stat blocks against the PDF first** — known bugs in dragons/initiatives/sizes. | Same. | Heavier cleaning; treat as a 70%-baseline. |
| `your5e/5e-srd-markdown` | Pre-broken-into-sections variant; Obsidian vault has explicit cross-links | The "broken-into-sections" Markdown is **already chunked** along useful semantic boundaries. | Vault wikilinks become a free knowledge graph (e.g., spell→class→school edges). | Minor — convert wikilinks to slugs. |
| dmdocs MDX (if repo public) | One MDX per spell/monster/item with **YAML frontmatter** | **One file = one chunk** for spells/items/monsters; fall back to heading-split for rules pages. | Frontmatter fields are your metadata schema directly — `level`, `school`, `casting_time`, `cr`, `type`, `rarity`, etc. | Minimal — frontmatter ingests straight into vector-DB metadata. |
| Open5e API v2 JSON | One JSON object per resource | **One JSON object = one chunk**, with the prose `desc` field embedded and the structured fields stored as metadata. | All structured fields are first-class: `cr`, `type`, `size`, `alignment`, `level`, `school`, `range`, `components`, `duration`, `concentration`, `ritual`, `source_document_key=srd-2024`. | Filter at ingestion to `document__key__in=srd-2024`. Flatten nested objects (e.g., creature actions) into separate child chunks linked by parent name. |
| 5e-bits 5e-database JSON files | One JSON file per resource | Same as Open5e. | Same metadata vocabulary as the 5eAPI schema (well-documented). | More effort to filter to *only* SRD 5.2 (vs. 5.1) given the API hasn't switched on `/api/2024` yet. |
| Raw PDF (DIY) | None until you parse it | Parse first (see Section 3), then apply structure-aware splitting. | Whatever your parser preserves. | Highest engineering cost; not worth it given community markdowns exist. |

**Dual-collection pattern is highly recommended**: store one collection of *narrative* chunks (rules prose, spell descriptions, monster lore) embedded for semantic search, and a parallel *structured* collection of fielded objects (spells/monsters/items/feats/conditions) used for metadata-filtered lookup before semantic rerank. Most production D&D RAGs end up there because "what's the AC of an Adult Red Dragon" should be a metadata lookup, while "explain the difference between cover and concealment" is semantic.

### 5. Evaluation — use the existing benchmark

`datapizza-ai-lab/dnd5e-srd-qa` on Hugging Face is purpose-built for this exact task. Wire it into your evaluation harness on day one — it will tell you whether your chunking/embedding choices are working before you over-invest in a bad path. Two tiers (Easy auto-generated, Medium with optional hints) and explicit `start_char`/`end_char` passages in the source MD let you compute retrieval recall@k against ground-truth passages.

---

## Recommendations

**Stage 1 — get a baseline running this week:**
1. Clone `https://github.com/downfallx/dnd-5e-srd-markdown`. License-compatible (CC-BY-4.0); ship the SRD attribution string in your repo and UI.
2. Use a `MarkdownHeaderTextSplitter` to split on `H1/H2/H3` (and `H4` for spells), with a 1500-token cap and **no overlap**.
3. Embed (e.g., `text-embedding-3-large` or `bge-large-en-v1.5`) into pgvector / Qdrant / Chroma. Attach metadata: `section`, `entity_type`, `name`, plus regex-extracted fields for stat-block-shaped chunks.
4. Run the `datapizza-ai-lab/dnd5e-srd-qa` Easy tier through your retriever; target recall@5 ≥ 0.85.

**Stage 2 — add structured filtering (week 2):**
5. Crawl Open5e `https://api.open5e.com/v2/` filtered to `document__key__in=srd-2024` for `creatures`, `spells`, `magicitems`, `feats`, `backgrounds`, `conditions`, `classes`, `rulesets`. Persist as JSONL.
6. Store these as a parallel "structured" vector collection, with a small adapter that lets the agent route queries like "list all 3rd-level evocation spells" to a SQL-style metadata filter rather than vector search.
7. Spot-audit Open5e against the SRD PDF for any entries missing or known-buggy (track the open5e-api release notes for `srd-2024` fixes).

**Stage 3 — close gaps (week 3+):**
8. Diff your Open5e crawl against the SRD 5.2.1 PDF table of contents. For anything Open5e is missing, fall back to the markdown chunks. If anything in Open5e disagrees with the official PDF, defer to the PDF and file an issue upstream.
9. Add the `springbov` or `your5e` markdown as a *secondary* corpus only if you find specific gaps; don't dual-ingest by default (it'll just create duplicate retrieval hits).

**Decision thresholds — when to switch strategies:**
- If recall@5 on the Datapizza Medium tier stays below 0.7 with `downfallx` markdown alone, **add `your5e/5e-srd-markdown`** sectioned variant — its Obsidian-vault cross-links carry implicit relevance signal.
- If structured-query accuracy (e.g., "spells of level X for class Y") is poor, **escalate Open5e from a fallback to a primary path** with a query router.
- If you find systematic stat-block errors in `downfallx`, **switch primary corpus to `your5e/5e-srd-markdown`** (its test-driven cleaning pipeline is the most rigorous).
- **DIY parse only as a last resort** (estimated 30–50 engineering hours) — and only if `dmdocs`'s repo turns out to be unavailable and you find ≥ 5% of stat blocks broken in all three community markdowns.

**Fallback plan if no ready-made dataset proves usable:** Fork `your5e/5e-srd-markdown`'s pipeline (it's the best-engineered conversion harness publicly available), run **Marker** on `SRD_CC_v5.2.1.pdf` for the prose, **LlamaParse** (or Claude-with-image) on the monster stat blocks (pages roughly devoted to "Monsters A–Z"), and converge in your repo. Total time: ~1 week part-time given the user's Python background.

---

## Caveats

- **Coverage figures for Open5e and the 5e-bits 2024 endpoint are inferred from release notes, not from a live API audit.** I was unable to fetch live entry counts during this research; before committing, do a quick audit (`curl 'https://api.open5e.com/v2/creatures/?document__key__in=srd-2024&limit=1'` and read the `count` field, repeated per endpoint) and compare against the SRD 5.2.1 table of contents (~325 stat blocks, 12 classes, 16+ feats, 3 backgrounds, 500+ spells, hundreds of magic items including the 15 restored in 5.2.1).
- **The dmdocs project repo URL was not directly verifiable from the search snippets I retrieved** — only the deployed site at `dmdocs.vercel.app/docs` and the author's EN World post. If the repo is public and CC-BY-4.0, it is likely the single best structured starting point; if not, default to the recommendation above.
- **`springbov/dndsrd5.2_markdown` is explicitly closed to PRs** and the author acknowledges quality issues. Don't depend on it as your only source.
- **`5e-bits/5e-database` README states OGL 1.0a** for the underlying material — that licensing string predates the 2024 SRD's CC-BY-4.0 release and is *probably* stale for the 2024 data files. Until the maintainers update the LICENSE, treat the 2024 content you pull from there as CC-BY-4.0 SRD 5.2 material and attribute WotC accordingly. If you publish your project, pin the commit you used and document the attribution chain.
- **Avoid 5etools and the `5e-complete-*` Foundry compendium forks** — these were/are non-SRD content and are the subject of a 2024-08-07 WotC DMCA on GitHub. Using them in a published bootcamp capstone is a real legal risk and will almost certainly cause your repo to be taken down.
- **Localization:** WotC has announced French/Italian/German/Spanish SRD 5.2 versions for "later in 2025." If your agent needs multilingual support, those should land soon; track the official D&D Beyond SRD page for updates.
- **Versioning hygiene:** WotC explicitly numbers SRD revisions (5.2 → 5.2.1 → future 5.2.2 / 5.3). Always pin your corpus to a specific SRD version string, store it as a chunk-level metadata field (`srd_version: "5.2.1"`), and re-ingest on each new version drop — the conversion guide tags `[New Rule]`, `[Revised Rule]`, `[New Name]` and is itself a reasonable diff source.
- **One claim above is sourced from secondhand reporting** I could not independently verify: the EN World forum's enumeration of dmdocs' frontmatter scheme and the springbov stat-block error list both come from a single thread (`enworld.org/threads/editable-5-2-1-srd.716978/`). Treat as plausible but spot-check against the actual files before relying on either claim.