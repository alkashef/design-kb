# Milestone guide

## Size

A milestone is one unit of delivered behavior. Test it with these questions:

- Can one session finish it, including its tests, in one commit?
- Does it have a check that shows it works: a test, or a manual `EX-nnn` row when the project's test
  policy leaves that behavior untested?
- Can the user say what is different when it is done?

If any answer is no, split the milestone or merge it with a neighbor.
Do not make a milestone for "set up" work that no test or check can show. Put setup in the first
milestone that needs it.

## Order

1. A milestone comes after everything it needs.
2. Put the riskiest unknown early, so a problem is found while the plan is cheap to change.
3. Prefer a thin end-to-end slice first. Then widen it.
4. Keep a milestone that changes a shared interface separate from the milestones that use it.

## Coverage

Make a list of requirement IDs with the milestone that owns each. A non-functional requirement
(`NFR-NNN`) belongs to the milestone where its test or manual check first can run, or to its own
milestone when it needs separate work. A requirement with status Withdrawn needs no milestone.
When the project rules defer documentation, the last milestone is "Doc sync": it brings `README.md`
and `docs/design.md` in line with the code and runs the browser tests. The manual checks are not a
milestone: they go under "## Human checks" after the last block (see Gate).

## Model and effort

| Work | Model | Effort |
| --- | --- | --- |
| Mechanical or repetitive: rename, move, copy a pattern, fill a table | `haiku` | `low` |
| Ordinary feature that follows a clear design | `sonnet` | `medium` |
| Feature with several rules, exceptions, or integration points | `sonnet` | `high` |
| Hard to reverse, security-relevant, concurrency, data migration, or a new shared structure | `opus` | `high` |
| Unclear design edge, or work where a mistake costs a lot | `opus` | `xhigh` or `max` |

Start from `sonnet` with `medium`. Move up only for a reason you can state in one line. Allowed
values are in `docs/workflow.md`.

An alias (`sonnet`) follows the newest model of its family, so the same plan can run on a newer
model next month. A full model ID (`claude-sonnet-5-5`) stays on that version. Use an ID when a run
must be repeatable.

## Tests first

- First read the project's test policy (`CLAUDE.md`, Testing, and the test decision in
  `design.md`). It says which requirement IDs and modules get automated tests.
- One test name per requirement ID that the policy tests, written so the name shows the ID. For any
  other ID write `Manual: EX-nnn`.
- A test checks behavior the spec states. It does not check how the code is built.
- Name the boundary and failure cases the spec lists. Do not invent new ones.
- Without a stated policy, test every requirement ID.

## Build

- Describe the smallest change that passes the tests.
- Name the files or modules the design assigns. Do not specify private functions.
- Leave out anything the design does not decide. A missing decision is a question for the user.

## Gate

The runner starts a milestone in a session with nobody to answer. A Gate is met by what the session
can run itself: the tests and checks of `CLAUDE.md`, AI calls off or a fake LLM client, invented
data. These are not a Gate: a call to the real LLM (needs the user's key and costs money), a read of the user's real
files, a walk through the manual `EX-nnn` rows, a person's review, or a download from the network.
List them under "## Human checks" at the end of the plan, one line each with the requirement or
design check ID, for the user to do after the run. The heading is level 2, so the runner's reading
of the milestone blocks is not affected.

## Example of one row and block

```markdown
| **M3** Record a payment | A clerk records a payment and the balance falls | sonnet | medium | open |

### M3 — Record a payment

- **Refs:** PAY-001, PAY-002, DEC-004.
- **Owner:** `src/payments/record.py`.
- **Tests first:** `test_pay_001_balance_falls_by_payment`, `test_pay_002_overpayment_rejected`.
- **Build:** add `record_payment` to the payments module; reject an amount above the balance.
- **Gate:** the tests and the checks in `CLAUDE.md` pass.
```
