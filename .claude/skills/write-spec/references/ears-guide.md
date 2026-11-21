# EARS and IDs

Use the EARS convention of `docs/specs.md`: each requirement is a row with its ID, the letter of its
pattern in the Type column, and the requirement. Use the terms of the glossary (section 1.3).

| Type | Pattern | Structure |
| --- | --- | --- |
| U | Ubiquitous (always active) | The system shall [required response]. |
| E | Event | When [trigger], the system shall [required response]. |
| S | State | While [state], the system shall [required response]. |
| O | Optional feature | Where [feature is included], the system shall [required response]. |
| X | Unwanted behavior | If [unwanted condition], then the system shall [required response]. |

Combine a precondition and trigger only when both constrain the required response.
Write one behavior per requirement so its acceptance can be examined independently.
Do not add a trigger to a requirement that is always active.
Do not invent conditions or thresholds to complete a pattern.

Example of a rule from `docs/specs.md`, with a concrete case that uses invented data:

- `FR-29` (Type E): When the user deletes an engineer or a project, the system shall
  also delete the assignments and the flags that refer to it.
- Case: Given an engineer with 3 assignments and 2 flags, when the user deletes the
  engineer, expect 0 assignments and 0 flags that refer to that engineer.

The example does not settle what happens to the vectors of the deleted engineer.
That is a design concern (`docs/design.md`, D-13), not a requirement.
Do not generate rules for a concern merely because an example mentions it.

The IDs of `docs/specs.md`:

| ID | Use |
| --- | --- |
| `FR-NN` | Functional requirement. Each subsection of section 3 has its own block of ten: search from FR-01, views from FR-10, data entry from FR-20, settings from FR-30. |
| `NFR-NN` | Non-functional requirement. |
| `AC-NN` | Acceptance criterion (section 6), with its numbered examples. |
| `A-NN` | Assumption, with its Source: Owner or Inferred. |
| `OI-NN` | Open item, with a proposed default. |

Keep existing requirement IDs. Allocate a new ID after the highest number ever
used in its block. Examine the Git history: a closed open item leaves the file, and
its `OI-NN` is not free.
If a block is full, continue the subsection in the next free block of ten: data entry continues from FR-40.
Preserve withdrawn rows so the allocator does not reuse them.
Change wording without changing the ID when the underlying requirement continues.
Mark a retired requirement `Withdrawn`. Do not renumber surviving requirements.

Source: [Official EARS guide by Alistair Mavin](https://alistairmavin.com/ears/).
EARS controls wording. It does not establish the business value of a requirement.
