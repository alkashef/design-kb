---
name: write-design
description: Turn an approved software spec into a practical technical design through a lightweight adaptation of Attribute-Driven Design 3.0. Use for architecture, technology stack selection, design reviews, or changes to docs/design.md in a Spec, Design, Plan workflow. Recommend languages, frameworks, and major libraries. Preserve requirement IDs and stable D-NN decision IDs. Support users without programming experience through one question at a time. Do not use for initial requirements discovery, visual styling alone, implementation planning, or coding.
---

# Write Design

Build a design that explains how the approved requirements will work. Apply ADD 3.0 with depth proportional to technical risk.
Treat this as an adaptation of ADD, not the official method or a guarantee of technical quality.

## Establish the baseline

- Read project instructions, applicable rules, `docs/workflow.md`, `docs/specs.md`, and the current `docs/design.md`.
- Read existing code, manifests, and tests when available. Distinguish an implemented fact from a proposed design.
- The design is `docs/design.md`. Use its format and conventions.
- Identify whether the request creates, resumes, reviews, or amends a design. Preserve unrelated decisions and user edits.
- Confirm approval from the available record or the user's instruction. If the spec is unapproved, analyze it provisionally and resolve approval before finalizing design.
- If requirements are absent, ask for the spec or use `/write-spec` first. Do not invent business behavior to make architecture possible.

Read [the design guide](references/design-guide.md) when choosing drivers, boundaries, or validation methods.
Read [the technology guide](references/technology-guide.md) before recommending a stack or new dependency.
[The design template](assets/design-template.md) shows the format of `docs/design.md` and the sections that it can get. Preserve the existing format.

## Keep each fact in its proper file

Keep requirements, EARS statements, and the data model in `specs.md`. Cite their IDs and sections in design instead of copying their text.
Keep architecture, technical rules, data storage, interfaces, settings, and decisions in `design.md`.
Keep milestones, task order, and implementation approvals in `plan.md` under the local workflow.
Keep installed direct dependencies and exact pins in the existing dependency files. Do not duplicate the installed inventory in design.

When a design requires a changed requirement, propose the exact spec change for approval. Do not silently edit the spec.
Treat the spec as authoritative when design and spec conflict. Analyze unaffected parts while the conflict awaits resolution.
Follow local rules for an active blocked milestone. Do not start a milestone or create a plan merely to finish design.

## Select the drivers

Find the requirements and constraints that most affect structure or technology. Cite existing IDs and the source of project constraints.
Consider critical workflows, data ownership, performance, availability, security, privacy, deployment, cost, and maintainability only where relevant.
Use measurable quality scenarios from the spec. If a missing target could change the design, ask one business question to resolve it.
Do not invent traffic volumes, uptime targets, budgets, retention periods, or regulatory obligations.
Label estimates and assumptions. Record who must resolve each material unknown and whether it blocks design or later implementation.

## Develop the design

For each major design issue, apply this cycle internally:

1. Select the driver or risk to address.
2. Compare the recommended approach with a meaningful feasible alternative.
3. Define responsibilities, data ownership, interfaces, and allowed dependencies.
4. Walk a critical workflow and its failure paths through the design.
5. Assess the result against the driver and identify the remaining uncertainty.

Repeat only where another decision or unresolved risk warrants more detail. Avoid alternatives for trivial choices.
Prefer the smallest structure that satisfies the drivers and project rules. Add distributed services, queues, or abstraction layers only with a concrete reason.
In an existing project, examine the cost of reuse, migration, and operating both designs before proposing a replacement.
Record enough detail for separate implementation sessions to make consistent choices. Do not specify every private function.

## Work with the user

Infer expertise from the conversation. Ask at most one question per message and give one procedural step at a time.
Explain consequences in business terms. Recommend the technical choice yourself rather than asking a non-programmer to choose a library by name.
Ask only for facts, priorities, permissions, or trade-offs that the available evidence cannot resolve.
For a consequential choice, state the recommendation, relevant alternatives, business effect, and the exact decision needed.
Do not ask for approval again when the user already approved that choice and scope.
Distinguish business approval from technical review. Identify the specific decision that needs an experienced software reviewer when the evidence exceeds your ability to assess it.
Do not require a technical reviewer for every routine choice or claim that an AI review proves correctness.

## Write the design

Preserve the headings of `docs/design.md`: Decisions and Open Design Questions.
Add a section for architecture, data storage, interfaces, settings, or the test policy when the design first needs it. The template shows them.
Add compact subsections for drivers, important flows, and unresolved risks only when needed.
Cover these concerns where they apply:

- Components, layers, responsibilities, import rules, and the directory structure.
- Languages, runtime, frameworks, database, major libraries, and verification tools.
- Data types, identities, ownership, relationships, integrity, persistence, and migration boundaries.
- Public contracts, authorization boundaries, validation, errors, and recovery behavior.
- Deployment, external data flows, secrets, settings, and operational failure handling.
- How each requirement is tested: its level (unit for a pure rule module, route through the API
  test client, browser for what only the page shows), and the fake for each external system (the
  embedding client). The test writer reads only the spec and the design, never the code, so name
  every interface a test needs: routes, request and response fields, stored records, and public
  functions.

For the embedding step (D-16), define the local runtime, the text sent to the model, failure handling, and test boundaries. Respect project rules.
Choose diagrams only when they clarify boundaries, dependencies, or runtime behavior. Use the least detail that helps implementation.
Keep directory entries and technical settings concrete. Reference requirement IDs for user-visible rules and limits.

## Record decisions and evidence

Give every significant design decision a stable `D-NN`, as one row of the Decisions table: ID, Status, Decision, Reason.
Set the Status to `Decided` only when the product owner chose the decision. A decision that you derived from a requirement is `Proposed` until the product owner confirms it.
Never renumber or reuse IDs. Find the highest allocated ID in the current document and available Git history before assigning a new one.
If history is unavailable, resolve the allocation boundary before finalizing new IDs. Provisional labels must not enter the approved design.
Write the choice in Decision. Write the rationale and the requirement references in Reason. Add alternatives, consequences, and a validation method there when they affect the choice (D-15 and D-16 show this).
Keep one current decision per topic. When a decision is replaced, keep its row, set its Status to `Superseded`, start its Decision with "Was:", and name the replacement in its Reason (D-12 shows this). Give the replacement a new ID.
Record a question that the design cannot settle in the table "Open Design Questions" with a `DQ-NN`. Delete the row when the question is closed. Git history keeps it, so examine the history before you allocate a new `DQ-NN`.
Separate observed results, documented capabilities, estimates, assumptions, and planned checks. Cite sources for consequential claims.
Never mark a test, benchmark, compatibility check, or prototype as successful unless it actually ran.

## Finish at the design boundary

Check that the design addresses the architectural drivers, respects the spec, and gives significant decisions real alternatives and validation methods.
Check references, unique IDs, technology evidence, data flows, interface failures, and consistency with project rules.
Check that every spec ID has a test level and that the interfaces its test needs are named.
Check that material unknowns have an owner and a blocking condition. Do not call an unresolved stack choice final.
Present the concrete design before requesting any approval required by project rules. Allow review in chat or a draft without replacing approved content prematurely.
Record only approval actually given: a decision becomes `Decided` when the product owner chooses it. Technical review and user approval are separate facts.
Save authorized design edits and follow applicable document checks and Git rules. Report the result and any remaining blocker briefly.
Stop after design. Do not install dependencies, create application code, run experiments, or build milestones unless separately authorized.
After approval, tell the user the next step is `/write-plan`.
