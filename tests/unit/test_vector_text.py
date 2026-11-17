"""Unit tests of the vector texts (M10): D-08 and D-09."""

from src.domain import vector_text
from src.domain.models import Assignment, Employee, Node, Project


def test_d_08_assignment_text_has_its_6_lines_in_order():
    leaf = Node(
        id="n-pll",
        parent_id="n-clocking",
        name="PLL",
        description="Phase-locked loop",
        position=0,
    )
    project = Project(
        id="p-1",
        name="Invented SerDes",
        description="An invented test chip",
        year=2024,
        process_technology="TSMC 7nm",
    )
    assignment = Assignment(
        id="a-1",
        employee_id="E-0001",
        project_id="p-1",
        leaf_id="n-pll",
        participation="lead",
        description="Led the fractional-N loop design",
    )

    text = vector_text.assignment_text(
        assignment, project, leaf, "Circuit design / Clocking / PLL"
    )

    lines = text.split("\n")
    assert [lines[0], lines[1], lines[2]] == [
        "PLL",
        "Phase-locked loop",
        "Circuit design / Clocking / PLL",
    ]
    assert lines[3].lower() == "lead"
    assert lines[4:] == ["Led the fractional-N loop design", "TSMC 7nm"]


def test_d_09_profile_text_is_the_skill_gaps():
    employee = Employee(
        id="E-0002",
        name="Bruno Invented",
        job_title="Design Engineer",
        career_level="Mid",
        team="Analog",
        skill_gaps="Needs experience with SerDes equalization",
    )

    assert vector_text.profile_text(employee) == "Needs experience with SerDes equalization"
