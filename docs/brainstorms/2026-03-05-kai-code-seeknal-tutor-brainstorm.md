# Kai-Code as Seeknal AI Tutor

**Date**: 2026-03-05
**Status**: Draft
**Context**: Brainstorming session for incorporating kai-code AI agent as a tutorial companion for students learning data pipeline development with Seeknal.

---

## What We're Building

An enhanced kai-code SeeknalAgent that serves as an **AI tutor** for students working through the 8-module Seeknal getting-started tutorial. The agent will:

1. **Answer any Seeknal question** accurately using on-demand documentation search via `seeknal docs --json`
2. **Guide students through all 8 tutorial modules** with awareness of learning objectives, expected outputs, and common mistakes per module
3. **Debug student pipeline issues** by reading their project files, understanding errors in the context of what they're learning, and explaining fixes

The agent acts as a knowledgeable tutor -- it explains concepts and helps debug, but does not write code for students.

## Why This Approach

### Current Gap

The existing SeeknalAgent in kai-code has:
- A system prompt (`kai-seeknal.md`) focused on the **Python API** (FeatureGroupDuckDB, Flow, FlowInput) -- but the tutorial teaches the **CLI/YAML pipeline** approach
- 20 programmatic tools (project, flow, feature store, entity, version, validation) but **no documentation search tool**
- **No tutorial awareness** -- no knowledge of the 8 modules, their objectives, or common student mistakes
- **No Seeknal skills** (only dbt and brainstorming skills exist)

### Chosen Approach: Docs Tool + Tutorial Skill + Prompt Rewrite

Three complementary changes in the kai-code repo:

1. **New `docs_tools.py`** -- LangChain tools wrapping `seeknal docs --json` for on-demand documentation search
2. **New `seeknal-tutorial/SKILL.md`** -- Loadable skill with module-by-module tutorial knowledge
3. **Updated `kai-seeknal.md`** -- System prompt rewritten to cover CLI/YAML pipeline concepts alongside existing Python API knowledge

This balances always-available base knowledge (prompt), on-demand deep documentation (docs tool), and tutorial-specific context (skill).

### Alternatives Considered

- **Comprehensive prompt only**: Baking everything into the system prompt. Rejected because the prompt would be ~500+ lines and consume tokens on every request even when not needed.
- **Multiple targeted skills**: Creating 4+ separate skills (basics, tutorial, feature-store, debugging). Rejected as over-engineered -- students would need to manually load the right skills.

## Key Decisions

### 1. Agent Role: AI Tutor (not co-pilot or autonomous builder)
Students ask kai-code questions as they work through modules. It explains concepts, answers "why", helps debug errors. It does **not** write code for them.

### 2. Knowledge Strategy: Hybrid (docs tool + skill + prompt)
- **System prompt**: Core Seeknal concepts (CLI workflow, YAML schema, Python API, DAG, ref())
- **Docs tool**: On-demand `seeknal docs --json` search for any CLI command or concept
- **Tutorial skill**: Module-by-module learning objectives, expected outputs, common mistakes, verification queries

### 3. Tutorial Awareness: Baked into the tutorial skill
The skill knows about all 8 modules:
- Module 1: Introduction & Setup (sources, REPL, data discovery)
- Module 2: Data Transformation (SQL transforms, ref(), DAG)
- Module 3: Data Quality & Testing (rules, profiles, severity)
- Module 4: Advanced Sources & CDC (multi-format, UNION ALL dedup)
- Module 5: DRY Config & Python API (common config, @source, @transform, ctx)
- Module 6: Feature Engineering for ML (@feature_group, entities, point-in-time joins, @second_order_aggregation)
- Module 7: Semantic Layer & Metrics (semantic models, measures, metrics, exposures)
- Module 8: Production Patterns (environments, lineage, cross-referencing, best practices)

### 4. Work Location: kai-code repo only
All changes go into `~/project/mta/kai-code`. The tutorial repo stays as-is. kai-code reads tutorial files at runtime from the student's project directory using its existing file tools.

### 5. Success Criteria
- A student can ask about any Seeknal concept and get an accurate, tutorial-appropriate answer
- A student can say "I'm on Module 3" and kai-code knows the context, can explain what they're doing, verify their work, and help with module-specific errors
- When a pipeline fails, kai-code can read the student's project files, understand the error, and explain the fix

## Scope of Changes

### New Files (in kai-code repo)

```
src/kai_code/agents/seeknal/tools/docs_tools.py
  - seeknal_search_docs(query: str) -> str
    Wraps `seeknal docs --json "<query>"`. Returns structured documentation results.
  - seeknal_list_doc_topics() -> str
    Wraps `seeknal docs --json --list`. Returns available documentation topics.

src/kai_code/skills/seeknal-tutorial/SKILL.md
  - Module 1-8 learning objectives and what students build
  - Expected terminal output per module
  - Common mistakes per module (from the tutorial's "Common Mistakes" sections)
  - REPL verification queries per module
  - The e-commerce domain context (orders, products, sales_events, transactions, etc.)
  - The progressive learning structure (YAML-first -> Python, simple -> complex)
```

### Modified Files (in kai-code repo)

```
src/kai_code/prompts/kai-seeknal.md
  - Section 1: Keep core role but expand to CLI/YAML pipeline expertise
  - Section 2: Add CLI workflow (init -> draft -> dry-run -> apply -> run)
  - Section 3: Add YAML pipeline concepts (kind, name, inputs, ref())
  - Section 4: Add node types (source, transform, rule, profile, feature_group, etc.)
  - Section 5: Keep Python API but add @source, @transform, @feature_group decorators
  - Section 6: Add `seeknal docs` tool usage guidance
  - Section 7: Update communication style for tutor role

src/kai_code/agents/seeknal/agent.py
  - Import and register docs_tools in get_seeknal_tools()
```

### Unchanged
- Existing 6 tool modules (project, flow, feature store, entity, version, validation)
- Agent architecture (SeeknalAgent extends KaiAgent pattern)
- CLI entry point structure

## Resolved Questions

1. **Should the tutorial skill auto-load?** **Yes.** When kai-code detects a `seeknal_project.yml` with `name: ecommerce-pipeline`, it auto-loads the tutorial skill. Zero friction for students.

2. **Should the docs tool search scope be expanded?** **No.** Keep it simple -- use `seeknal docs --json` as-is (searches CLI docs only). For deeper documentation, the agent can use its existing file-reading tools to read documentation files directly from the Seeknal source.

3. **Should the system prompt reference the tutorial modules?** **No.** System prompt stays generic for any Seeknal project. Tutorial awareness is 100% in the skill. This keeps the SeeknalAgent reusable for non-tutorial projects.

4. **CLI entry point**: **Yes, register it.** Add `kai-seeknal = "kai_code.agents.seeknal.cli:cli_main"` to `pyproject.toml [project.scripts]`. Students can run `kai-seeknal` directly from the terminal.

## Open Questions

None -- all questions resolved.
