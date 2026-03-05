---
title: "feat: Integrate kai-code as Seeknal AI Tutor"
type: feat
status: completed
date: 2026-03-05
origin: docs/brainstorms/2026-03-05-kai-code-seeknal-tutor-brainstorm.md
---

# feat: Integrate kai-code as Seeknal AI Tutor

## Overview

Enhance the kai-code SeeknalAgent to serve as an AI tutor for students working through the 8-module Seeknal getting-started tutorial. Three complementary changes in the kai-code repo (`~/project/mta/kai-code`):

1. **New `docs_tools.py`** -- LangChain tools wrapping `seeknal docs --json` for on-demand documentation search
2. **New `seeknal-tutorial/SKILL.md`** -- Loadable skill with module-by-module tutorial knowledge
3. **Rewritten `kai-seeknal.md`** -- System prompt covering CLI/YAML pipeline concepts (current prompt only covers Python API)
4. **Register `kai-seeknal` CLI entry point** in `pyproject.toml`
5. **Auto-detect tutorial project** and auto-load the tutorial skill

(see brainstorm: docs/brainstorms/2026-03-05-kai-code-seeknal-tutor-brainstorm.md)

## Problem Statement / Motivation

The existing SeeknalAgent has a knowledge gap:

- **System prompt** (`kai-seeknal.md`) focuses on the **Python API** (`FeatureGroupDuckDB`, `Flow`, `FlowInput`) but students learn the **CLI/YAML pipeline** approach (`seeknal init`, `seeknal run`, YAML `kind: source/transform/rule`)
- **No documentation search tool** -- the agent can't look up Seeknal CLI docs even though `seeknal docs --json` was purpose-built for AI agents
- **No tutorial awareness** -- doesn't know about the 8 modules, their learning objectives, expected outputs, or common student mistakes
- **No CLI entry point** -- `kai-seeknal` is not registered in `pyproject.toml`

Students working through the tutorial have no AI-powered assistance that understands both Seeknal and the tutorial context.

## Proposed Solution

### Task 1: Create `docs_tools.py` -- Documentation Search Tools

**File:** `src/kai_code/agents/seeknal/tools/docs_tools.py`

Two tools wrapping the `seeknal docs` CLI:

```python
def create_docs_tools(seeknal_path: Path) -> list:

    @tool("seeknal_search_docs")
    def seeknal_search_docs(query: str, max_results: int = 10) -> str:
        """Search Seeknal CLI documentation for a topic or keyword.

        Use this to look up how Seeknal CLI commands work, their flags,
        and usage patterns. Supports exact topic match (e.g., "init", "run")
        or full-text search (e.g., "feature group", "materialization").

        Args:
            query: Search query or exact topic name.
            max_results: Maximum number of search results (default: 10).

        Returns:
            JSON with documentation content or search results.
        """
        # subprocess.run(["seeknal", "docs", "--json", "--max-results", str(max_results), query])
        # Parse stdout as JSON, return it
        # Handle exit codes: 0=success, 1=no results, 3=rg missing, 4=error

    @tool("seeknal_list_doc_topics")
    def seeknal_list_doc_topics() -> str:
        """List all available Seeknal documentation topics.

        Returns a list of topic names with summaries. Use this to discover
        what documentation is available before searching.

        Returns:
            JSON with topic names, summaries, and file paths.
        """
        # subprocess.run(["seeknal", "docs", "--json", "--list"])

    return [seeknal_search_docs, seeknal_list_doc_topics]
```

**Implementation details:**
- Follow the factory pattern from `project_tools.py`: closure over `seeknal_path`, `@tool` decorator, JSON return with `indent=2`
- Run `seeknal docs` via `subprocess.run` with `cwd=seeknal_path` to ensure it finds the docs directory
- Handle the three JSON output formats: topic list, exact match (full content), search results (snippets)
- On error, return `{"status": "error", "message": "..."}` JSON
- Default `max_results=10` (not 50) to keep responses concise for the LLM

**Registration:** Add to `get_seeknal_tools()` in `agent.py`:
```python
from kai_code.agents.seeknal.tools.docs_tools import create_docs_tools
tools.extend(create_docs_tools(self._seeknal_path))
```

Update `tools/__init__.py` to export `create_docs_tools`.

### Task 2: Create `seeknal-tutorial/SKILL.md` -- Tutorial Awareness Skill

**File:** `src/kai_code/skills/seeknal-tutorial/SKILL.md`

A loadable skill containing module-by-module tutorial knowledge. Structure:

```markdown
---
name: seeknal-tutorial
description: Tutorial guide for the 8-module Seeknal getting-started course. Provides module objectives, expected outputs, common mistakes, and verification queries for e-commerce pipeline tutorial.
tags: [seeknal, tutorial, education]
---

# Seeknal Getting Started Tutorial Guide

## Your Role
You are tutoring a student through the Seeknal getting-started tutorial...

## Tutorial Overview
8 progressive modules building an e-commerce analytics pipeline...

## Module 1: Introduction & Setup
### Learning Objectives
### What Students Build
### Expected Output
### Common Mistakes
### Verification Queries (REPL)

## Module 2: Data Transformation
...

## Module 8: Production Patterns
...

## Debugging Guide
Common errors and how to explain fixes in tutorial context...
```

**Content sources** (from the tutorial repo research):
- Learning objectives: extracted from each module's "What You'll Learn" section
- What students build: from "What You'll Build" sections + file lists
- Expected outputs: from the expected terminal output blocks in each module
- Common mistakes: from each module's "Common Mistakes" section
- Verification queries: from each module's REPL sections
- The e-commerce domain context (orders, products, sales_events, transactions datasets)
- The progressive structure: YAML-first (Modules 1-3) → Python (Modules 4-5) → ML/Analytics (6-7) → Production (8)

**Size target:** Keep under 300 lines. Focus on what the agent needs to *tutor*, not reproduce the full tutorial content. Students have the tutorial docs -- the skill provides meta-knowledge about the tutorial.

### Task 3: Rewrite `kai-seeknal.md` -- System Prompt

**File:** `src/kai_code/prompts/kai-seeknal.md`

Rewrite to cover CLI/YAML pipeline concepts alongside existing Python API knowledge. The prompt stays **generic** (not tutorial-specific -- that's in the skill).

**New section structure:**

```markdown
# Kai Seeknal System Prompt

# INHERIT: kai-code

You are Kai Seeknal, a specialized AI agent for data engineering
using the Seeknal platform...

---

## Section 1: Seeknal Platform Overview
- All-in-one data + AI/ML engineering platform
- Multi-engine: DuckDB (<100M rows) and Spark (big data)
- CLI-driven workflow with YAML and Python authoring

## Section 2: CLI Workflow
- seeknal init → draft → dry-run → apply → run
- Key commands: init, run, repl, list, show, lineage, docs
- Environment management: seeknal env plan/apply/promote

## Section 3: YAML Pipeline Concepts
- Node types: source, transform, rule, profile, feature_group,
  second_order_aggregation, semantic_model, exposure
- YAML structure: kind, name, inputs, ref(), sql
- Common config templates ({{ }} syntax in seeknal/common/)
- DAG-based execution with topological ordering

## Section 4: Python Pipeline API
- Decorators: @source, @transform, @feature_group,
  @second_order_aggregation, @materialize
- PipelineContext (ctx): ctx.ref(), ctx.duckdb.sql(), .df()
- When to use Python vs YAML

## Section 5: Feature Store
- Entities and join keys
- Feature groups with auto-versioning
- Point-in-time joins (data leakage prevention)
- Offline/online materialization
- Second-order aggregations

## Section 6: Data Quality
- Rules: not_null, range_check, custom SQL
- Profiles: statistical summaries
- Severity levels: error, warn, info

## Section 7: Tool Usage
- Use seeknal_search_docs to look up CLI documentation
- Use seeknal_list_doc_topics to discover available docs
- Use file tools to read student project files for debugging
- Use execute to run seeknal commands in the student's project

## Section 8: Communication Style
- Explain concepts at undergraduate level
- Use concrete examples from data engineering
- When debugging, explain the WHY not just the fix
- Reference the seeknal docs tool for detailed command usage
```

**Key changes from current prompt:**
- Adds Sections 2-3 (CLI workflow + YAML concepts) -- completely missing today
- Section 4 updates the Python API to use the decorator/pipeline API (current prompt uses the older FeatureGroupDuckDB/Flow API)
- Section 6 adds data quality (rules, profiles) -- not in current prompt
- Section 7 adds guidance for the new docs tools
- Removes outdated guidance (e.g., "Don't use Seeknal for simple ETL")
- Removes security-focused content that's more relevant to Seeknal contributors than users

### Task 4: Auto-Detect Tutorial Project

**File:** `src/kai_code/agents/seeknal/agent.py` (modify)

Follow the `find_dbt_project()` pattern from `agents/dbt/config.py`:

```python
def _detect_tutorial_project(self) -> bool:
    """Check if the current project is the Seeknal tutorial."""
    project_file = Path(self._root_dir) / "seeknal_project.yml"
    if project_file.exists():
        import yaml
        with open(project_file) as f:
            config = yaml.safe_load(f)
        return config.get("name") == "ecommerce-pipeline"
    return False
```

Then in the agent initialization or `_build_graph()`, if detected, auto-load the seeknal-tutorial skill:

```python
# In _build_graph() or a post-init hook
if self._detect_tutorial_project():
    # Auto-load the tutorial skill
    self._memory_manager.load_skill("seeknal-tutorial")
```

**Note:** Need to check the exact mechanism for programmatic skill loading -- the current system uses `load_skill` as an LLM tool, not a programmatic API. May need to either:
- (a) Add a programmatic `load_skill(name)` method to the skills system, or
- (b) Inject the skill content directly into the system prompt during `_build_graph()`, or
- (c) Add a startup message that tells the agent to load the skill

Option (b) is simplest -- read the SKILL.md content and append it to the system prompt when the tutorial project is detected.

### Task 5: Register CLI Entry Point

**File:** `pyproject.toml` (modify)

Add to `[project.scripts]`:

```toml
kai-seeknal = "kai_code.agents.seeknal.cli:cli_main"
```

This allows students to run `kai-seeknal` directly from the terminal.

## Acceptance Criteria

### Functional Requirements

- [x] `seeknal_search_docs("init")` returns the full init documentation as JSON
- [x] `seeknal_search_docs("feature group")` returns search results with file paths and snippets
- [x] `seeknal_list_doc_topics()` returns all 32 topics with names and summaries
- [x] Docs tools handle errors gracefully (ripgrep missing, no results, seeknal not installed)
- [x] The seeknal-tutorial skill contains accurate content for all 8 modules
- [x] The system prompt covers CLI workflow, YAML concepts, Python decorators, and data quality
- [x] When run from a directory with `seeknal_project.yml` (name: ecommerce-pipeline), the tutorial skill auto-loads
- [x] `kai-seeknal` CLI command works after `pip install -e .`

### Tutor Behavior Verification

- [ ] Agent can answer "What is a transform in Seeknal?" accurately using base prompt knowledge
- [ ] Agent can answer "How do I use seeknal run?" by searching docs with the docs tool
- [ ] Agent can respond to "I'm on Module 3" with relevant context about data quality rules
- [ ] When a student's pipeline fails, agent can read their YAML files and explain the error

## Dependencies & Risks

**Dependencies:**
- `seeknal` CLI must be installed and on PATH for docs tools to work
- `ripgrep` (`rg`) must be installed for full-text search (exact topic match works without it)
- Tutorial content in `seeknal-getting-started` repo must be stable (skill references specific module content)

**Risks:**
- **Seeknal docs scope**: Currently only searches `docs/cli/` (33 files). Broader documentation (YAML schema reference, concepts) is not searchable via `seeknal docs`. Mitigated by: agent can use file-reading tools to read broader docs directly from the Seeknal source.
- **Skill size**: The tutorial skill must stay concise enough to not bloat the context window. Target <300 lines.
- **Auto-detection**: The `name: ecommerce-pipeline` detection is fragile if students rename the project. Acceptable for the tutorial use case.

## Implementation Order

1. **Task 1: docs_tools.py** -- standalone, no dependencies on other tasks
2. **Task 3: kai-seeknal.md rewrite** -- can be done in parallel with Task 1
3. **Task 2: seeknal-tutorial/SKILL.md** -- needs understanding of the prompt to avoid duplication
4. **Task 4: Auto-detect + agent.py changes** -- depends on Task 1 (tool registration) and Task 2 (skill to load)
5. **Task 5: pyproject.toml** -- trivial, do last

Tasks 1 and 3 can run in parallel. Tasks 2, 4, 5 are sequential after that.

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-03-05-kai-code-seeknal-tutor-brainstorm.md](docs/brainstorms/2026-03-05-kai-code-seeknal-tutor-brainstorm.md) -- Key decisions: AI Tutor role (not co-pilot), hybrid knowledge strategy (docs tool + skill + prompt), tutorial awareness via auto-loaded skill, CLI docs scope only, register kai-seeknal entry point.

### Internal References (kai-code repo)

- Tool authoring pattern: `src/kai_code/agents/seeknal/tools/project_tools.py`
- Skill format: `src/kai_code/skills/dbt/SKILL.md`, `src/kai_code/skills/brainstorming/SKILL.md`
- Prompt inheritance: `src/kai_code/prompts/__init__.py`
- Current seeknal prompt: `src/kai_code/prompts/kai-seeknal.md`
- Agent class: `src/kai_code/agents/seeknal/agent.py`
- CLI entry point: `src/kai_code/agents/seeknal/cli.py`
- Auto-detection pattern: `src/kai_code/agents/dbt/config.py` (`find_dbt_project()`)
- CLAUDE.md conventions: `CLAUDE.md`
- Tool registration: `pyproject.toml` `[project.scripts]`

### Internal References (seeknal repo)

- Docs CLI implementation: `src/seeknal/cli/docs.py`
- Docs directory: `docs/cli/` (32 topic files)
- JSON output formats: exact match, search results, topic list
- CLI flags: `--json`, `--list`, `--max-results`

### Internal References (tutorial repo)

- Tutorial modules: `docs/tutorial/01_introduction_and_setup.md` through `08_production_patterns.md`
- Project config: `seeknal_project.yml` (name: ecommerce-pipeline)
- Data files: `data/` (orders.csv, products.csv, sales_events.jsonl, etc.)
