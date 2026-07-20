# Claude Code — Verified frontmatter/config facts (2026-07-18)

Research target: installed Claude Code CLI **2.1.204**. Goal: know exactly
which frontmatter fields are real before writing 7 subagent `.md` files and
11 skill `SKILL.md` files for the Digital Crown scientific/clinical
governance layer (pharmacology, diagnosis, cephalometry, radiology).

All facts below come from live fetches of `code.claude.com/docs/en` on
2026-07-18 (WebSearch + WebFetch tools), not from training-data memory.
Quotes are verbatim from the fetched Markdown source of each page.

---

## Q1 — Subagent frontmatter fields (`.claude/agents/*.md`)

**Queries run:**
- `site:code.claude.com/docs/en sub-agents supported frontmatter fields`
- `site:code.claude.com/docs/en subagents tools model permissionMode`

**Sources opened (2026-07-18):**
- https://code.claude.com/docs/en/sub-agents.md — fetched in full (1195 lines)

**What I found**

The doc states explicitly: *"The following fields can be used in the YAML
frontmatter. Only `name` and `description` are required."*

Verbatim field table (`#### Supported frontmatter fields`):

| Field | Required | Description (verbatim, condensed) |
|---|---|---|
| `name` | Yes | "Unique identifier using lowercase letters and hyphens. Hooks receive this value as `agent_type`. The filename doesn't have to match" |
| `description` | Yes | "When Claude should delegate to this subagent" |
| `tools` | No | "Tools the subagent can use. Inherits all tools if omitted. If no entry in the list resolves to a tool, the subagent fails to launch with an error naming the entries. To preload Skills into context, use the `skills` field rather than listing `Skill` here" |
| `disallowedTools` | No | "Tools to deny, removed from inherited or specified list" |
| `model` | No | "Model to use: `sonnet`, `opus`, `haiku`, `fable`, a full model ID (for example, `claude-opus-4-8`), or `inherit`. Defaults to `inherit`" |
| `permissionMode` | No | "Permission mode: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, or (as of v2.1.200) `manual` as an alias for `default`. Ignored for plugin subagents" |
| `maxTurns` | No | "Maximum number of agentic turns before the subagent stops" |
| `skills` | No | "Skills to preload into the subagent's context at startup. The full skill content is injected, not only the description. Subagents can still invoke unlisted project, user, and plugin skills through the Skill tool" |
| `mcpServers` | No | "MCP servers available to this subagent... Ignored for plugin subagents" |
| `hooks` | No | "Lifecycle hooks scoped to this subagent. Ignored for plugin subagents" |
| `memory` | No | "Persistent memory scope: `user`, `project`, or `local`. Enables cross-session learning" |
| `background` | No | "Set to `true` to always run this subagent as a background task... as of v2.1.198 it runs subagents in the background by default" |
| `effort` | No | "Effort level when this subagent is active... Options: `low`, `medium`, `high`, `xhigh`, `max`; available levels depend on the model" |
| `isolation` | No | "Set to `worktree` to run the subagent in a temporary git worktree... automatically cleaned up if the subagent makes no changes" |
| `color` | No | "Display color... Accepts `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, or `cyan`" |
| `initialPrompt` | No | "Auto-submitted as the first user turn when this agent runs as the main session agent (via `--agent` or the `agent` setting)... Prepended to any user-provided prompt" |

Confirmed the same set (plus `prompt` for CLI use, `disallowedTools`) via the
`--agents` CLI flag section: *"The `--agents` flag accepts JSON with the
same frontmatter fields as file-based subagents: `description`, `prompt`,
`tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`,
`hooks`, `maxTurns`, `skills`, `initialPrompt`, `memory`, `effort`,
`background`, `isolation`, and `color`."*

**`model` — exact accepted values** (from `### Choose a model`):
- Model alias: `sonnet`, `opus`, `haiku`, or `fable`
- Full model ID, e.g. `claude-opus-4-8` or `claude-sonnet-5` (same values as `--model`)
- `inherit` — uses the main conversation's model
- Omitted → defaults to `inherit`

**`permissionMode` — exact accepted values** (table under `#### Permission modes`):
`default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`
(+ `manual` as an alias of `default`, v2.1.200+).

**File location convention confirmed**: `.claude/agents/*.md` (project
scope, priority 3) and `~/.claude/agents/*.md` (user scope, priority 4), in
addition to managed settings (priority 1), `--agents` CLI flag (priority
2), and plugin `agents/` directories (priority 5, lowest). Exact quote:
*"Project subagents (`.claude/agents/`) are ideal for subagents specific to
a codebase... User subagents (`~/.claude/agents/`) are personal subagents
available in all your projects."* — confirms both project and user levels
exist, matching what's already used in this repo
(`C:\Users\lenovo\Documents\Cabinet\DigitalCrown\.claude\agents\pdf-smoke-tester.md`,
which uses only `name`, `description`, `tools`, `model` — all four are
real, verified fields).

**Rejected / not used in our template**: `mcpServers`, `hooks`, `color`,
`initialPrompt`, `background`, `isolation`, `effort` — all real fields, but
not needed for Digital Crown's governance subagents unless a specific use
case demands them (e.g. `isolation: worktree` could matter for a subagent
that runs destructive DB checks, `memory` could matter for an agent that
should accumulate clinical-code review patterns over time — worth
revisiting per-agent).

**Remaining uncertainty**: none for this question — the field list and
every value enum came from a single authoritative, fully-fetched page with
verbatim tables.

---

## Q2 — SKILL.md format (`.claude/skills/<name>/SKILL.md`)

**Queries run:**
- `site:code.claude.com/docs/en skills SKILL.md`
- `site:code.claude.com/docs/en skills SKILL.md context fork agent`

**Sources opened (2026-07-18):**
- https://code.claude.com/docs/en/skills.md — fetched in full (888 lines)
- https://code.claude.com/docs/en/sub-agents.md (cross-referenced for the `skills` agent field, see Q1)

**What I found — frontmatter fields**

Verbatim from `### Frontmatter reference`: *"All fields are optional. Only
`description` is recommended so Claude knows when to use the skill."*

| Field | Required | Description (verbatim, condensed) |
|---|---|---|
| `name` | No | "Display name shown in skill listings. Defaults to the directory name" |
| `description` | Recommended | "What the skill does and when to use it... combined `description` and `when_to_use` text is truncated at 1,536 characters" |
| `when_to_use` | No | "Additional context for when Claude should invoke the skill, such as trigger phrases" |
| `argument-hint` | No | "Hint shown during autocomplete... Example: `[issue-number]`" |
| `arguments` | No | "Named positional arguments for `$name` substitution... space-separated string or a YAML list" |
| `disable-model-invocation` | No | "Set to `true` to prevent Claude from automatically loading this skill... prevents the skill from being preloaded into subagents... Default: `false`" |
| `user-invocable` | No | "Set to `false` to hide from the `/` menu... Default: `true`" |
| `allowed-tools` | No | "Tools Claude can use without asking permission during the turn that invokes this skill. The grant clears when you send your next message" |
| `disallowed-tools` | No | "Tools removed from Claude's available pool while this skill is active" |
| `model` | No | "Model to use when this skill is active... Accepts the same values as `/model`, or `inherit`" |
| `effort` | No | "Effort level when this skill is active... Options: `low`, `medium`, `high`, `xhigh`, `max`" |
| `context` | No | "Set to `fork` to run in a forked subagent context" |
| `agent` | No | "Which subagent type to use when `context: fork` is set" |
| `hooks` | No | "Hooks scoped to this skill's lifecycle" |
| `paths` | No | "Glob patterns that limit when this skill is activated... Uses the same format as path-specific rules" |
| `shell` | No | "Shell to use for inline shell commands in this skill. Accepts `bash` (default) or `powershell`" |

**`context: fork` and `agent: <name>` — CONFIRMED, exact syntax:**

```yaml
---
name: deploy
description: Deploy the application to production
context: fork
disable-model-invocation: true
---
```

and, combined with `agent:`:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---
```

Verbatim: *"Add `context: fork` to your frontmatter when you want a skill
to run in isolation. The skill content becomes the prompt that drives the
subagent... The `agent` field specifies which subagent configuration to
use. Options include built-in agents (`Explore`, `Plan`,
`general-purpose`) or any custom subagent from `.claude/agents/`. If
omitted, uses `general-purpose`."* This directly answers the "bind a skill
to running as a specific subagent" question: **yes, this is a real,
documented mechanism**, not something I need to invent.

**Preloading skills into an agent — CONFIRMED, this is the inverse direction:**

The `skills:` field lives in the **agent** frontmatter (see Q1 table), not
in SKILL.md. Verbatim from sub-agents.md: *"Use the `skills` field to
inject skill content into a subagent's context at startup... The full
content of each listed skill is injected into the subagent's context at
startup."* Example:

```yaml
---
name: api-developer
description: Implement API endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---
```

The docs explicitly frame these two mechanisms as inverses of each other
(quote from skills.md): *"This is the inverse of running a skill in a
subagent. With `skills` in a subagent, the subagent controls the system
prompt and loads skill content. With `context: fork` in a skill, the skill
content is injected into the agent you specify. Both use the same
underlying system."*

Important constraint: a skill with `disable-model-invocation: true` **cannot**
be preloaded via an agent's `skills:` field — verbatim: *"You can't preload
skills that set `disable-model-invocation: true`, since preloading draws
from the same set of skills Claude can invoke."*

**Locations**: `.claude/skills/<name>/SKILL.md` (project, this project
only) and `~/.claude/skills/<name>/SKILL.md` (personal, all projects),
plus enterprise/managed and plugin scopes. Precedence when names collide:
enterprise > personal > project > bundled skill of the same name.

**Rejected / not used**: `argument-hint`, `arguments`, `when_to_use`,
`shell` — real fields, not needed unless a specific Digital Crown skill
takes CLI arguments or runs PowerShell blocks.

**Remaining uncertainty**: none — single authoritative page, fully fetched,
frontmatter table quoted verbatim.

---

## Q3 — `.claude/rules/` path-scoped format

**Queries run:**
- `site:code.claude.com/docs/en memory path-specific rules paths` (folded into direct fetch below — WebSearch for this exact phrase was not separately run because the `memory.md` page was fetched directly and contains the full, authoritative section)

**Sources opened (2026-07-18):**
- https://code.claude.com/docs/en/memory.md — fetched in full

**What I found**

`.claude/rules/` is a real, documented directory. Verbatim: *"Place
markdown files in your project's `.claude/rules/` directory. Each file
should cover one topic, with a descriptive filename like `testing.md` or
`api-design.md`. All `.md` files are discovered recursively."*

**`paths:` frontmatter — CONFIRMED, exact syntax** (`#### Path-specific rules`):

Verbatim: *"Rules can be scoped to specific files using YAML frontmatter
with the `paths` field. These conditional rules only apply when Claude is
working with files matching the specified patterns."*

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
- Include OpenAPI documentation comments
```

Multiple patterns + brace expansion also confirmed:

```markdown
---
paths:
  - "src/**/*.{ts,tsx}"
  - "lib/**/*.ts"
  - "tests/**/*.test.ts"
---
```

Behavior notes (verbatim): *"Rules without a `paths` field are loaded
unconditionally and apply to all files. Path-scoped rules trigger when
Claude reads files matching the pattern, not on every tool use."* And a
glob-syntax caveat: a pattern containing an unescaped `[` that isn't a
valid bracket expression matches nothing (as of v2.1.207) rather than
breaking the whole rule file; escape a literal `[` as `\[`.

Also relevant for governance: `.claude/rules/` supports **symlinks** (to
share a rule set across multiple repos) and a **user-level**
`~/.claude/rules/` location (loaded before project rules, so project rules
win on conflict). `SKILL.md`'s own `paths:` field (Q2 table) explicitly
reuses this same format: *"Uses the same format as path-specific rules."*

**Rejected**: nothing to reject — this is a small, single-purpose field
and the syntax is unambiguous.

**Remaining uncertainty**: none.

---

## Q4 — Exact built-in tool names (for `tools:` frontmatter)

**Source opened (2026-07-18):**
- https://code.claude.com/docs/en/tools-reference.md — fetched in full (394 lines)

**What I found**

Verbatim framing: *"The tool names are the exact strings you use in
permission rules, subagent tool lists, and hook matchers."*

Full verified list of built-in tool names (exact capitalization, as they'd
appear comma-separated in a `tools:` line):

`Agent`, `Artifact`, `AskUserQuestion`, `Bash`, `CronCreate`,
`CronDelete`, `CronList`, `Edit`, `EnterPlanMode`, `EnterWorktree`,
`ExitPlanMode`, `ExitWorktree`, `Glob`, `Grep`, `ListMcpResourcesTool`,
`LSP`, `Monitor`, `NotebookEdit`, `PowerShell`, `PushNotification`,
`Read`, `ReadMcpResourceTool`, `RemoteTrigger`, `ReportFindings`,
`ScheduleWakeup`, `SendMessage`, `SendUserFile`, `ShareOnboardingGuide`,
`Skill`, `TaskCreate`, `TaskGet`, `TaskList`, `TaskOutput` (deprecated,
"in favor of `Read` on the task's output file path"), `TaskStop`,
`TaskUpdate`, `TodoWrite` (disabled by default as of v2.1.142, in favor of
the `Task*` tools), `ToolSearch`, `WaitForMcpServers`, `WebFetch`,
`WebSearch`, `Workflow`, `Write`.

Confirmed `TaskCreate` (mentioned in the user's prompt as something to
verify) is real and distinct from the deprecated `TodoWrite`.

Note on subagent-availability exceptions (from sub-agents.md, cross-
referenced): four of the tools above are **not actually usable inside a
subagent** even if listed in `tools:`, because they depend on
main-conversation UI/session state: `AskUserQuestion`, `EnterPlanMode`,
`ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`,
`WaitForMcpServers`. This matters for our 7 subagents: none of them should
list these expecting them to function.

MCP-server tools use the `mcp__<server>` / `mcp__<server>__*` pattern in
`tools`/`disallowedTools`, not a fixed name — not relevant to Digital
Crown's clinical subagents unless we wire in an MCP server later.

**Rejected**: none — this is an exhaustive table from a single
authoritative reference page.

**Remaining uncertainty**: none for the name list itself. One open
practical question for us: which subset of ~40 tools each of the 7
clinical subagents actually needs is a design decision, not a
documentation gap.

---

## Q5 — Hook events

**Source opened (2026-07-18):**
- https://code.claude.com/docs/en/hooks.md — fetched (WebFetch summarized; not re-verified line-by-line against raw source, see caveat below)

**What I found**

30 documented hook event names, with a one-line description each (as
extracted by the fetch tool from the live page, so treat exact wording as
paraphrase-level accurate rather than character-for-character verbatim —
see caveat):

`SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`,
`PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`,
`PostToolUseFailure`, `PostToolBatch`, `Notification`, `MessageDisplay`,
`SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `Stop`,
`StopFailure`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`,
`CwdChanged`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`,
`PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`,
`SessionEnd`.

The most relevant ones for a Digital Crown governance rule file to
reference (cross-confirmed against sub-agents.md, which was fetched raw
and does quote these verbatim):
- **`PreToolUse`** — "Before a tool call executes. Can block it" — this is
  the one sub-agents.md uses in its own worked example (a `db-reader`
  subagent that blocks non-`SELECT` SQL via a `PreToolUse` hook on `Bash`).
- **`PostToolUse`** — "After a tool call succeeds"
- **`SubagentStart`** / **`SubagentStop`** — fire in `settings.json` when a
  subagent begins/completes; matcher = subagent's `name` field.
- **`Stop`** in a subagent's own frontmatter hooks is automatically
  converted to `SubagentStop` at runtime when that agent runs as a
  subagent (verbatim from sub-agents.md: *"When the agent is invoked as a
  subagent, `Stop` hooks in frontmatter are automatically converted to
  `SubagentStop` events"*).
- **`InstructionsLoaded`** — "When a CLAUDE.md or `.claude/rules/*.md` file
  is loaded into context" — directly useful for debugging whether our
  path-scoped `.claude/rules/` governance files actually loaded.

**Caveat / remaining uncertainty**: the hooks.md fetch was processed
through the WebFetch summarization model rather than read as raw source
text (unlike the other four pages, which I read in full via the Read tool
on the persisted raw fetch output). The event **names** are reliable
(they're also independently corroborated by exact quotes inside
sub-agents.md, e.g. `PreToolUse`, `PostToolUse`, `SubagentStart`,
`SubagentStop`, `Stop`), but the one-line descriptions above should be
treated as paraphrase, not verbatim doc text. If exact hook payload
schemas are needed later (e.g. to write a `PreToolUse` validation script
for a clinical-code guardrail), re-fetch `hooks.md` with the Read tool
against the raw persisted output rather than relying on this summary.

---

## Recommandations pratiques

Based only on verified fields above, here is the safe minimal template for
each artifact type. Every field used below is confirmed real and
correctly spelled/cased.

### Template — subagent (`.claude/agents/<name>.md`)

```markdown
---
name: <lowercase-hyphenated-name>
description: <when Claude should delegate to this subagent — be specific>
tools: Read, Grep, Glob, Bash
model: sonnet
---

<system prompt / role / method / expected report, in the style already
used by pdf-smoke-tester.md>
```

Add only if actually needed, never speculatively:
- `disallowedTools: <...>` instead of `tools:` when you want "everything
  except X" rather than an allowlist.
- `permissionMode: plan` for a pure-analysis clinical-review agent that
  must never write.
- `memory: project` if the agent should accumulate durable, git-shared
  knowledge (e.g. a cephalometry-review agent learning known landmark
  edge cases over time) — this is a strong candidate for at least one of
  the 7 agents.
- `skills: [<skill-name>, ...]` to preload one of the 11 skills' full
  content into an agent at startup (not just its description) — use this
  instead of hoping the agent discovers the skill on its own, when the
  skill is core domain knowledge the agent always needs (e.g. a
  pharmacology-interaction agent preloading a drug-interaction reference
  skill).
- Never use `context`/`agent` here — those are SKILL.md fields, not agent
  fields (the two systems are inverses; see Q2).

### Template — skill (`.claude/skills/<name>/SKILL.md`)

Reference/knowledge skill (loads inline, no isolation):

```markdown
---
name: <name>
description: <what it does and when to use it — put the key trigger first>
---

<domain knowledge / conventions the model should apply inline>
```

Task/action skill that should run isolated as a specific subagent (this is
the mechanism that answers "bind a skill to a subagent"):

```markdown
---
name: <name>
description: <what it does>
context: fork
agent: <custom-subagent-name-or-Explore-or-Plan-or-general-purpose>
disable-model-invocation: true   # if it should only run via explicit /name, e.g. destructive actions
---

<explicit task instructions — context: fork skills need an actionable
task, not just guidelines, or the forked subagent returns nothing useful>
```

Add only if needed:
- `paths: ["backend/services/generators/cephalo_*.py", ...]` to
  auto-scope a skill to only load when Claude is touching matching files
  — good fit for skills tied to one clinical module (cephalometry,
  radiology) rather than the whole repo.
- `allowed-tools: Bash(pytest *)` etc. to pre-approve specific commands
  for the turn that invokes the skill.

### Template — path-scoped rule (`.claude/rules/<topic>.md`)

```markdown
---
paths:
  - "backend/services/generators/cephalo_*.py"
  - "backend/routers/cephalometry*.py"
---

# <Topic> rules

- <concrete, verifiable rule>
- <concrete, verifiable rule>
```

Omit `paths:` entirely for rules that should always load (equivalent
priority to `.claude/CLAUDE.md`).

### Fields confirmed real but deliberately NOT used above (out of scope for now)

`mcpServers`, `hooks` (agent-scoped), `color`, `initialPrompt`,
`background`, `isolation`, `effort`, `model` override on skills,
`when_to_use`, `arguments`, `argument-hint`, `shell` — all verified in Q1/Q2
tables; revisit per-agent/per-skill only if a concrete need arises (e.g.
`isolation: worktree` for an agent that must not touch the live repo
during a schema-check dry run).
