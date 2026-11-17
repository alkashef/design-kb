---
name: sdd
description: The way into spec-driven development in this repo. Reads the state of docs/specs.md, docs/design.md and docs/plan.md and what the user asks, names the step of docs/workflow.md that comes next, and starts that one skill (/write-spec, /write-design, /write-plan, or a milestone with /write-tests). Use when the user asks for a new feature, a change, a fix of any size, the next step, to build or run milestones, or where the project stands, even if they do not name a skill. Runs one step, then stops.
---

# SDD

Route the request to one step of the loop in `docs/workflow.md`, start that step's skill, and stop.
Hold no rule of your own: `docs/workflow.md` and `CLAUDE.md` own the rules. Never pass an approval
gate for the user.

## 1. Read the state

Read the files, not memory:

- **Spec:** the `Status` in the version line at the top of `docs/specs.md` (`Draft` or `Approved`),
  and its table "Open Items".
- **Design:** the Status of each decision in `docs/design.md` (`Decided`, `Proposed` or
  `Superseded`), and its table "Open Design Questions". The design is approved when no decision is
  `Proposed` and no question is open. Compare the date of the last commit of each file
  (`git log -1 --format=%cs -- docs/specs.md`, then the same for `docs/design.md`). A spec commit
  newer than the last design commit means the design may be stale.
- **Plan:** the rows of "Milestones at a glance" in `docs/plan.md`, and the Status of each (`open`,
  `blocked`, `approved`).
- **Git:** `git status --short`, and whether the branch is ahead of its remote.

If a state is unclear (for example, you cannot tell whether the design covers the newest spec), ask
the user that one question before you route.

## 2. Sort the request

| The user asks for | Step | Skill |
| --- | --- | --- |
| New or changed behavior, or a fix where the spec is silent or wrong | 1. Spec | `/write-spec` |
| A change of architecture, data, interfaces, settings or libraries, with no change of behavior | 2. Design | `/write-design` |
| Milestones for an approved spec and design | 3. Plan | `/write-plan` |
| A fix of any size, of behavior the spec already states | 3. Plan: one fix milestone | `/write-plan` |
| To build, run or go on with the milestones | 4. Execute | see 4 below |
| Where the project stands, or what is next | none | the status report of 3 below |

When the request does not say which row it is, ask one question. Quote the user's words.

## 3. Check the order, then route

The loop runs in order. Before you start a step, check that the steps before it are done:

1. A spec in `Draft` comes first: resume `/write-spec`, or ask the user to approve it.
2. A design that is stale for the approved spec, or that has a `Proposed` decision or an open
   design question, comes next: `/write-design`.
3. A plan that is missing for an approved design comes next: `/write-plan`.
4. A `blocked` milestone comes before every other milestone: show its **Blocked** entry, and ask the
   user to approve or change it (`docs/workflow.md`, Approval). Do not edit its entries.
5. Uncommitted changes to `docs/` come before a run: name them, and ask the user to commit them.

If the request skips a step (for example, "build X" when X is not in the spec), say which step comes
first and why, and route there.

Before you start the skill, tell the user in two lines: the state you found, and the step you start.
For a status request, give only those lines and the next command.

## 4. Execute

- **Default:** give the runner command for the open rows:
  `python scripts/milestones-runner.py` (with `--start` and `--end` when the user names milestones).
  The user runs it in a terminal; it handles retries, timeouts and logs.
- **When the user asks to build a milestone in this chat:** run it as `docs/workflow.md`, Execute,
  says. Start a subagent that runs `/write-tests` for the milestone. It must not read the code in
  `src/`. Then build in this session without changing any file in `tests/`, run the checks of step
  4, and finish steps 5 to 7. One milestone per request.

## 5. Stop

Run one skill, then stop. When it ends, tell the user the next step in one line, for example
"Next: approve the design, then run `/sdd` again." Never start the next step yourself.
