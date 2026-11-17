"""Unit tests of the seed data (M11): NFR-04, NFR-05 and D-26.

The tests call `seed_data.build()` and the public functions of `levels` and `skill_tree`.
"""

from collections import Counter

from src.domain import levels, seed_data, skill_tree

EXPECTED_EMPLOYEES = 40
EXPECTED_PROJECTS = 15
EXPECTED_TOP_LEVEL_NODES = 6
MIN_LEAVES = 25
MAX_LEAVES = 35
LEVEL_PLL_LEAD_FROM = 3
LEVEL_HANDS_ON = 2


def leaves_of(seed):
    """Return the leaves of the seed tree."""
    return [node for node in seed.nodes if skill_tree.is_leaf(seed.nodes, node.id)]


def level_in_leaf(seed, employee_id, leaf_id):
    """Return the effective level of an employee in a leaf, computed from the seed records."""
    mine = [a for a in seed.assignments if a.employee_id == employee_id and a.leaf_id == leaf_id]
    lead_count = sum(1 for a in mine if a.participation == "lead")
    member_count = sum(1 for a in mine if a.participation == "member")
    flag = next(
        (f.flag for f in seed.flags if f.employee_id == employee_id and f.leaf_id == leaf_id),
        None,
    )
    return levels.effective_level(lead_count, member_count, flag, levels.default_thresholds())


def leaf_ids_named(seed, text):
    """Return the IDs of the leaves whose name or description holds the text, in lower case."""
    return {
        leaf.id
        for leaf in leaves_of(seed)
        if text in leaf.name.lower() or text in (leaf.description or "").lower()
    }


def test_nfr_04_seed_has_40_employees_15_projects_and_6_top_level_nodes():
    seed = seed_data.build()

    top_level = [node for node in seed.nodes if not node.parent_id]
    assert len(seed.employees) == EXPECTED_EMPLOYEES
    assert len(seed.projects) == EXPECTED_PROJECTS
    assert len(top_level) == EXPECTED_TOP_LEVEL_NODES


def test_nfr_04_seed_has_between_25_and_35_leaves():
    seed = seed_data.build()

    assert MIN_LEAVES <= len(leaves_of(seed)) <= MAX_LEAVES


def test_nfr_04_seed_holds_the_persons_of_the_3_example_searches():
    seed = seed_data.build()
    projects = {project.id: project for project in seed.projects}
    employees = {employee.id: employee for employee in seed.employees}

    # Example 1: level 3 or 4 in PLL, with a lead assignment on a 7nm project.
    pll_leaves = {leaf.id for leaf in leaves_of(seed) if leaf.name.lower() == "pll"}
    pll_leads = {
        a.employee_id
        for a in seed.assignments
        if a.leaf_id in pll_leaves
        and a.participation == "lead"
        and "7nm" in projects[a.project_id].process_technology.lower()
        and level_in_leaf(seed, a.employee_id, a.leaf_id) in (LEVEL_PLL_LEAD_FROM, 4)
    }
    assert pll_leads, "no PLL lead on a 7nm project with level 3 or 4"

    # Example 2: level 2 or higher in the leaf CDR.
    cdr_leaves = {leaf.id for leaf in leaves_of(seed) if leaf.name.lower() == "cdr"}
    cdr_people = {
        a.employee_id
        for a in seed.assignments
        if a.leaf_id in cdr_leaves
        and level_in_leaf(seed, a.employee_id, a.leaf_id) >= LEVEL_HANDS_ON
    }
    assert cdr_people, "no employee with level 2 or higher in the CDR leaf"

    # Example 3: a senior employee of the team Analog with a level in a low-noise amplifier leaf.
    lna_leaves = leaf_ids_named(seed, "low-noise amplifier")
    lna_people = {
        employee.id
        for employee in employees.values()
        if employee.team == "Analog"
        and employee.career_level == "Senior"
        and any(level_in_leaf(seed, employee.id, leaf_id) for leaf_id in lna_leaves)
    }
    assert lna_people, "no senior Analog employee with a level in a low-noise amplifier leaf"


def test_nfr_05_seed_assignments_and_flags_obey_the_entry_rules():
    seed = seed_data.build()
    employee_ids = {employee.id for employee in seed.employees}
    project_ids = {project.id for project in seed.projects}
    leaf_ids = {leaf.id for leaf in leaves_of(seed)}
    assigned_pairs = {(a.employee_id, a.leaf_id) for a in seed.assignments}

    assert len(employee_ids) == len(seed.employees)
    assert len(project_ids) == len(seed.projects)
    assert len({a.id for a in seed.assignments}) == len(seed.assignments)
    for assignment in seed.assignments:
        assert assignment.employee_id in employee_ids
        assert assignment.project_id in project_ids
        assert assignment.leaf_id in leaf_ids
        assert assignment.participation in ("lead", "member")
    triples = Counter((a.employee_id, a.project_id, a.leaf_id) for a in seed.assignments)
    assert max(triples.values()) == 1
    flag_pairs = Counter((f.employee_id, f.leaf_id) for f in seed.flags)
    if flag_pairs:
        assert max(flag_pairs.values()) == 1
    for flag in seed.flags:
        assert flag.employee_id in employee_ids
        assert flag.leaf_id in leaf_ids
        assert flag.flag in ("aware", "expert")
        if flag.flag == "aware":
            assert (flag.employee_id, flag.leaf_id) not in assigned_pairs
