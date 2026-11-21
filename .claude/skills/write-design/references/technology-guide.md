# Technology choices

## Recommend a stack from the constraints

Read the current stack, manifests, environment rules, deployment target, and approved integrations first.
The stack is decided in `docs/design.md` (D-15, D-16, D-20). Do not add a technology because it is familiar.
Treat the decided technologies as constraints until a replacement has a concrete benefit that outweighs migration and maintenance costs.
Prefer the standard library when it satisfies the requirements. Explain the capability that requires each new major library.

Recommend the applicable languages, runtime, frameworks, database, major libraries, and test tools.
If a category is unnecessary, state why briefly instead of inventing a technology for it.
Connect consequential choices to requirement IDs or project constraints and a `D-NN`.

## Check current facts

Use official documentation, release notes, package metadata, or license text for consequential technology claims.
Check the exact capability, platform support, compatible runtime versions, maintenance status, and license where these affect the decision.
For paid services, check current pricing and limits when they affect the proposed design. State workload assumptions behind cost estimates.
Record source URLs and the date checked. Do not treat model recall as current evidence.
If browsing is unavailable, label the candidate and capability claim unverified. Do not claim an implementation-ready choice when the uncertainty could change the stack.

## Separate recommendations from installed dependencies

In design, name the chosen technologies, their roles, reasons, and relevant compatibility constraints.
Record a required major version or support policy only when architecture depends on it.
Keep exact installed direct versions in the manifest, requirements file, or lockfile according to project rules.
Resolve and pin exact versions when adding the dependency, with the required approval. Never install a package merely to complete design.
`requirements.txt` owns the installed direct dependency list (`CLAUDE.md`, Dependencies). Do not add unused packages to it.

Identify existing, approved, proposed, and unverified technologies clearly.
A proposed library remains proposed until the user grants any required dependency approval.
A library is approved when a `Decided` decision in `docs/design.md` names it.

## Explain choices to non-programmers

Give one primary recommendation. Explain its effect on cost, setup, maintenance, privacy, or an important workflow.
Describe a meaningful alternative and the condition that would favor it.
Ask for the underlying constraint rather than a brand preference.

Example: "I recommend local storage because the approved scope has one user on one machine. Shared access would change this choice."

If shared access is not established, ask whether users need simultaneous access before finalizing persistence.
Do not infer shared access merely from the number of engineers in the organization.

## Design tools and quality checks

Reuse the project's check tools where adequate. Identify a browser test tool when UI workflow requirements need browser tests.
Define test boundaries and fakes for external services. Keep live services and private data out of automated tests unless the project explicitly permits them. Follow the project's test policy (`CLAUDE.md`, Testing). When the project rules cut test depth, record which requirements and modules get automated tests, and which are checked by hand, in one `D-NN`.
Treat coverage and lint as implementation checks. Define separate evidence for requirement behavior and important quality attributes.
