"""The seed data: fixed records with invented names for the demo (NFR-04, NFR-05, NFR-06, D-26).

The records hold the persons that the 3 example searches of AC-01 expect: a lead of a PLL design on
a 7nm project, a member of a CDR leaf, and a senior employee of the team Analog in a low-noise
amplifier leaf. No level is stored: each level comes from the assignments and the flags (NFR-05).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from src.domain.models import Assignment, Employee, Flag, Node, Project

LEAD = "lead"
MEMBER = "member"

# A node of the tree: its name, its description and its children (none for a leaf).
TreeItem = Tuple[str, str, tuple]


def _leaf(name: str, description: str) -> TreeItem:
    """Return a tree item with no children."""
    return (name, description, ())


TREE: List[TreeItem] = [
    (
        "Analog design",
        "Transistor-level design of continuous-time circuits.",
        (
            _leaf("LNA", "Low-noise amplifier design for receiver front ends."),
            _leaf("Op-amp", "Operational amplifier design for filters and readout."),
            _leaf("Bandgap reference", "Voltage reference that does not drift with temperature."),
            _leaf("LDO regulator", "Low-dropout linear regulator for clean supply rails."),
        ),
    ),
    (
        "Mixed-signal design",
        "Circuits that join the analog and the digital world.",
        (
            (
                "Data converters",
                "Circuits that turn a signal into numbers and back.",
                (
                    _leaf("SAR ADC", "Successive-approximation analog-to-digital converter."),
                    _leaf("Sigma-delta ADC", "Oversampling converter with noise shaping."),
                    _leaf("DAC", "Digital-to-analog converter."),
                ),
            ),
            (
                "Clocking",
                "Circuits that make and clean clocks.",
                (
                    _leaf("PLL", "Phase-locked loop that makes a low-jitter clock."),
                    _leaf("DLL", "Delay-locked loop that aligns clock phases."),
                    _leaf(
                        "CDR",
                        "Clock and data recovery: gets the clock back from a serial data stream.",
                    ),
                ),
            ),
        ),
    ),
    (
        "Digital design",
        "Logic design from the architecture to the netlist.",
        (
            _leaf("RTL design", "Writing synthesizable register-transfer-level code."),
            _leaf("Logic synthesis", "Turning RTL into a gate-level netlist."),
            _leaf("Static timing analysis", "Checking setup and hold timing and closing it."),
            _leaf("Low-power design", "Clock gating, power domains and leakage control."),
        ),
    ),
    (
        "Physical design",
        "From the netlist to the layout that goes to the foundry.",
        (
            _leaf("Floorplanning", "Placing the blocks and the pins of the chip."),
            _leaf("Place and route", "Placing the cells and routing the wires."),
            _leaf("Power grid design", "Planning the supply network of the chip."),
            _leaf("Physical verification", "DRC and LVS signoff of the layout."),
        ),
    ),
    (
        "Verification and test",
        "Proving that the design works before and after the silicon.",
        (
            _leaf("UVM verification", "Constrained-random testbenches in UVM."),
            _leaf("Formal verification", "Proving properties with formal tools."),
            _leaf("Design for test", "Scan insertion and test pattern generation."),
            _leaf("Post-silicon validation", "Bring-up and measurement of the first silicon."),
        ),
    ),
    (
        "Memory and interfaces",
        "Memories, chip-to-chip links and reliability.",
        (
            _leaf("SRAM design", "Bit cells, arrays and compilers for on-chip memory."),
            _leaf("DDR PHY", "Physical layer of the DDR memory interface."),
            _leaf("PCIe PHY", "Physical layer of the PCI Express interface."),
            _leaf("ESD protection", "Protecting pins against electrostatic discharge."),
            _leaf("EM and IR analysis", "Electromigration and supply-drop signoff."),
        ),
    ),
]

# The employees by team: the team, the job title, and the name and career level of each member.
TEAMS = [
    (
        "Analog",
        "Analog Design Engineer",
        [
            ("Ilsa Vantor", "Senior"),
            ("Doran Kesh", "Principal"),
            ("Marit Oyelaran", "Mid"),
            ("Tavish Brenn", "Junior"),
            ("Sunniva Alder", "Senior"),
            ("Joaquim Prell", "Staff"),
            ("Nadia Fenwick", "Mid"),
            ("Oskar Teal", "Junior"),
        ],
    ),
    (
        "Mixed-Signal",
        "Mixed-Signal Design Engineer",
        [
            ("Priya Halloran", "Senior"),
            ("Wen Castellan", "Principal"),
            ("Leif Moorgate", "Mid"),
            ("Amara Dunleavy", "Staff"),
            ("Kofi Brandvold", "Mid"),
            ("Yara Pellham", "Senior"),
            ("Emil Rask", "Mid"),
            ("Zora Quint", "Junior"),
        ],
    ),
    (
        "Digital",
        "Digital Design Engineer",
        [
            ("Hugo Ravenscar", "Principal"),
            ("Linnea Voss", "Staff"),
            ("Tomas Draycott", "Senior"),
            ("Selma Ketterer", "Senior"),
            ("Ravi Aldous", "Mid"),
            ("Cleo Brannigan", "Mid"),
            ("Finn Abara", "Junior"),
            ("Mei Sundqvist", "Junior"),
        ],
    ),
    (
        "Physical Design",
        "Physical Design Engineer",
        [
            ("Gideon Marsh", "Principal"),
            ("Anika Rowntree", "Staff"),
            ("Dmitri Callow", "Senior"),
            ("Halima Strand", "Senior"),
            ("Pedro Wickham", "Mid"),
            ("Ingrid Solano", "Mid"),
            ("Jonah Tuck", "Junior"),
            ("Beatriz Orme", "Junior"),
        ],
    ),
    (
        "Verification",
        "Verification Engineer",
        [
            ("Casimir Yoon", "Principal"),
            ("Delphine Roake", "Staff"),
            ("Arjun Whitlock", "Senior"),
            ("Sakura Delmont", "Senior"),
            ("Magnus Eddison", "Mid"),
            ("Tamsin Kerrigan", "Mid"),
            ("Elio Brandt", "Junior"),
            ("Noor Hartley", "Junior"),
        ],
    ),
]

# The skill gaps of some employees, by employee number (the position in TEAMS, from 1).
SKILL_GAPS: Dict[int, str] = {
    4: "Wants to learn PLL design and phase noise analysis.",
    8: "Has never worked on a data converter; wants a SAR ADC project.",
    11: "Needs more practice with clock and data recovery loops.",
    13: "Does not know low-noise amplifier design yet.",
    16: "Wants to learn about high-speed serial links.",
    18: "Little experience with analog-on-digital power noise.",
    21: "Has not done a signoff of electromigration and IR drop.",
    23: "Wants to learn formal verification.",
    24: "Needs to learn low-power design flows.",
    29: "Has no experience with power grid design.",
    31: "Wants to learn timing closure of a large block.",
    32: "Needs experience with DDR interface layout.",
    38: "Wants to learn post-silicon validation.",
    39: "Has not used formal tools.",
    40: "Wants to learn design for test.",
}

# (name, description, year, process technology) of the projects, in order from P-01.
PROJECTS = [
    ("Falcon", "Serial transceiver test chip with a low-jitter clock.", 2021, "7nm FinFET"),
    ("Harbor", "Low-power sensor hub SoC with always-on domains.", 2019, "28nm CMOS"),
    ("Juniper", "Wireless receiver front end with a gain-controlled amplifier.", 2022, "16nm FinFET"),
    ("Kestrel", "Memory controller and PHY for the fifth DDR generation.", 2023, "5nm FinFET"),
    ("Lumen", "Readout and conversion array for an image sensor.", 2020, "40nm CMOS"),
    ("Marlin", "Automotive microcontroller with an analog front end.", 2018, "65nm CMOS"),
    ("Nimbus", "112 Gb/s serial link with a clock and data recovery loop.", 2023, "7nm FinFET"),
    ("Osprey", "Radio SoC for wireless local networks.", 2021, "12nm FinFET"),
    ("Pioneer", "Power management IC with regulators and references.", 2019, "180nm BCD"),
    ("Quartz", "Accelerator tile for machine learning inference.", 2024, "5nm FinFET"),
    ("Raven", "Clock generation macro with several PLLs.", 2022, "7nm FinFET"),
    ("Sable", "Edge SoC with a processor cluster and an interface block.", 2020, "14nm FinFET"),
    ("Tundra", "Ultra-low-power radio for sensor nodes.", 2018, "40nm CMOS"),
    ("Umbra", "Physical layer of the fifth PCI Express generation.", 2022, "10nm FinFET"),
    ("Vesper", "Test chip for a compiler of SRAM macros.", 2017, "22nm FD-SOI"),
]

# (employee number, project number, leaf name, participation, description) of the assignments.
ASSIGNMENTS = [
    # Analog team
    (1, 3, "LNA", LEAD, "Led the low-noise amplifier of the receiver front end for a 2 dB noise figure."),
    (1, 8, "LNA", LEAD, "Led the low-noise amplifier of the radio, with gain steps."),
    (1, 3, "Op-amp", MEMBER, "Designed the baseband filter op-amp."),
    (2, 3, "LNA", LEAD, "Architect of the receiver front end and its low-noise amplifier."),
    (2, 8, "LNA", LEAD, "Led the low-noise amplifier and the input matching."),
    (2, 13, "LNA", LEAD, "Led the low-noise amplifier of the ultra-low-power radio."),
    (2, 9, "Bandgap reference", LEAD, "Led the bandgap reference with 20 ppm drift."),
    (3, 3, "LNA", MEMBER, "Simulated and laid out the noise matching network."),
    (3, 9, "LDO regulator", MEMBER, "Designed the error amplifier of the regulator."),
    (4, 13, "LNA", MEMBER, "Measured the amplifier on the bench."),
    (4, 9, "Bandgap reference", MEMBER, "Ran the temperature sweeps of the reference."),
    (5, 9, "LDO regulator", LEAD, "Led the low-dropout regulator of the sensor supply rail."),
    (5, 2, "LDO regulator", LEAD, "Led the regulator of the always-on domain."),
    (5, 9, "ESD protection", LEAD, "Led the pad ring and the ESD clamps."),
    (5, 6, "Bandgap reference", MEMBER, "Trimmed the reference at wafer test."),
    (6, 5, "Op-amp", LEAD, "Led the readout op-amp array of the image sensor."),
    (6, 2, "Op-amp", LEAD, "Led the low-power op-amp of the sensor hub."),
    (6, 5, "SAR ADC", MEMBER, "Designed the comparator of the converter."),
    (7, 6, "Op-amp", MEMBER, "Designed a precision amplifier for the front end."),
    (7, 9, "ESD protection", MEMBER, "Simulated the discharge paths."),
    (8, 6, "Bandgap reference", MEMBER, "Drew the layout of the reference core."),
    # Mixed-Signal team
    (9, 11, "PLL", LEAD, "Led the ring-oscillator PLL of the clock generation macro."),
    (9, 1, "PLL", LEAD, "Led the low-jitter PLL of the serial transceiver."),
    (9, 14, "CDR", MEMBER, "Designed the loop filter of the CDR."),
    (9, 14, "PCIe PHY", MEMBER, "Integrated the clocks of the PHY."),
    (10, 11, "PLL", LEAD, "Architect of the PLLs of the clock generation macro."),
    (10, 1, "PLL", LEAD, "Architect of the low-jitter PLL of the transceiver."),
    (10, 7, "PLL", LEAD, "Led the PLL that clocks the 112 Gb/s link."),
    (10, 7, "CDR", LEAD, "Led the clock and data recovery loop of the 112 Gb/s link."),
    (11, 1, "PLL", MEMBER, "Designed the charge pump and the loop filter."),
    (11, 12, "PLL", MEMBER, "Characterized the PLL of the interface block."),
    (11, 4, "DDR PHY", LEAD, "Led the delay lines of the memory PHY."),
    (12, 7, "CDR", LEAD, "Led a bang-bang CDR that recovers the clock from a serial data stream."),
    (12, 14, "CDR", LEAD, "Led the clock recovery of the PCI Express receiver."),
    (12, 1, "DLL", MEMBER, "Designed the phase interpolator and its delay-locked loop."),
    (12, 14, "PCIe PHY", LEAD, "Led the receiver of the physical layer."),
    (13, 7, "CDR", MEMBER, "Designed the phase detector of the CDR."),
    (13, 14, "CDR", MEMBER, "Checked the lock range of the clock recovery."),
    (14, 5, "SAR ADC", LEAD, "Led the 12-bit SAR ADC of the imaging array."),
    (14, 8, "SAR ADC", LEAD, "Led the converter of the radio receive path."),
    (14, 8, "LNA", MEMBER, "Co-simulated the amplifier with the converter."),
    (14, 14, "PCIe PHY", MEMBER, "Designed the equalizer."),
    (15, 5, "Sigma-delta ADC", MEMBER, "Modeled the sigma-delta modulator."),
    (15, 13, "DAC", MEMBER, "Designed the transmit digital-to-analog converter."),
    (15, 4, "DDR PHY", MEMBER, "Designed the data-path timing circuits."),
    (16, 5, "SAR ADC", MEMBER, "Drew the layout of the capacitor array."),
    (16, 13, "DAC", MEMBER, "Ran the post-layout simulations."),
    # Digital team
    (17, 10, "RTL design", LEAD, "Architect of the data path of the accelerator tile."),
    (17, 4, "RTL design", LEAD, "Led the RTL of the memory controller."),
    (17, 12, "RTL design", LEAD, "Led the RTL of the processor cluster."),
    (17, 4, "Low-power design", LEAD, "Led the clock gating and the power domain plan."),
    (18, 10, "Logic synthesis", LEAD, "Led the synthesis flow of the tile."),
    (18, 4, "Logic synthesis", LEAD, "Led the synthesis and the constraints of the controller."),
    (18, 12, "Static timing analysis", MEMBER, "Checked the timing of the interface block."),
    (19, 6, "RTL design", LEAD, "Led the RTL of the microcontroller core."),
    (19, 12, "RTL design", MEMBER, "Wrote the interrupt controller."),
    (20, 10, "Static timing analysis", LEAD, "Led the timing closure of the tile."),
    (20, 4, "Static timing analysis", LEAD, "Led the timing closure of the controller."),
    (21, 2, "Low-power design", MEMBER, "Added the power gating of the sensor hub."),
    (21, 6, "RTL design", MEMBER, "Wrote the timers and the bus bridge."),
    (21, 15, "SRAM design", LEAD, "Led the SRAM compiler test chip."),
    (22, 12, "Logic synthesis", MEMBER, "Ran the synthesis of the interface block."),
    (22, 10, "RTL design", MEMBER, "Wrote the activation unit."),
    (23, 10, "RTL design", MEMBER, "Wrote the buffer logic of the tile."),
    (24, 2, "Low-power design", MEMBER, "Checked the power intent files."),
    (24, 12, "RTL design", MEMBER, "Wrote the debug registers."),
    # Physical Design team
    (25, 10, "Floorplanning", LEAD, "Led the floorplan of the accelerator tile."),
    (25, 4, "Floorplanning", LEAD, "Led the floorplan of the memory controller."),
    (25, 1, "Floorplanning", LEAD, "Led the floorplan of the serial transceiver."),
    (26, 10, "Power grid design", LEAD, "Led the power grid of the tile."),
    (26, 4, "Power grid design", LEAD, "Led the power grid of the memory controller."),
    (26, 7, "EM and IR analysis", LEAD, "Led the supply-drop signoff of the link."),
    (27, 10, "Place and route", LEAD, "Led the place and route of the tile."),
    (27, 12, "Place and route", LEAD, "Led the place and route of the edge SoC."),
    (28, 4, "Physical verification", LEAD, "Led the DRC and LVS signoff of the controller."),
    (28, 7, "Physical verification", MEMBER, "Fixed the DRC errors of the link."),
    (29, 12, "Place and route", MEMBER, "Routed the clock trees of the interface block."),
    (29, 2, "Floorplanning", MEMBER, "Prepared the floorplan of the always-on domain."),
    (30, 10, "Physical verification", MEMBER, "Ran the LVS of the tile."),
    (30, 4, "Place and route", MEMBER, "Ran the routing iterations."),
    (31, 12, "Physical verification", MEMBER, "Ran the DRC checks."),
    (32, 2, "Place and route", MEMBER, "Routed the sensor hub."),
    # Verification team
    (33, 10, "UVM verification", LEAD, "Led the UVM environment of the tile."),
    (33, 4, "UVM verification", LEAD, "Led the UVM environment of the memory controller."),
    (33, 12, "UVM verification", LEAD, "Led the UVM environment of the edge SoC."),
    (34, 6, "Formal verification", LEAD, "Led the formal proofs of the bus protocol."),
    (34, 4, "Formal verification", LEAD, "Led the formal checks of the arbiter."),
    (35, 12, "Design for test", LEAD, "Led the scan insertion of the edge SoC."),
    (35, 6, "Design for test", LEAD, "Led the test patterns of the microcontroller."),
    (36, 15, "Post-silicon validation", LEAD, "Led the bring-up of the SRAM test chip."),
    (36, 12, "Post-silicon validation", MEMBER, "Measured the interface block on the bench."),
    (37, 10, "UVM verification", MEMBER, "Wrote the sequences of the tile."),
    (37, 2, "UVM verification", MEMBER, "Wrote the checkers of the sensor hub."),
    (38, 15, "SRAM design", MEMBER, "Tested the SRAM macros of the test chip."),
    (39, 10, "UVM verification", MEMBER, "Ran the regressions of the tile."),
    (40, 15, "Post-silicon validation", MEMBER, "Measured the SRAM test chip."),
]

# (employee number, leaf name, flag) of the flags. An aware flag has no assignment on its leaf.
FLAGS = [
    (2, "Op-amp", "expert"),
    (10, "DLL", "expert"),
    (19, "RTL design", "expert"),
    (26, "Power grid design", "expert"),
    (34, "Formal verification", "expert"),
    (4, "Sigma-delta ADC", "aware"),
    (17, "PLL", "aware"),
    (23, "Logic synthesis", "aware"),
    (25, "Static timing analysis", "aware"),
    (37, "Formal verification", "aware"),
]


@dataclass
class SeedData:
    """The records of the seed data, ready to be written to the store."""

    employees: List[Employee]
    projects: List[Project]
    nodes: List[Node]
    assignments: List[Assignment]
    flags: List[Flag]


def _employee_id(number: int) -> str:
    """Return the ID of the employee with the number, such as E-0007."""
    return f"E-{number:04d}"


def _project_id(number: int) -> str:
    """Return the ID of the project with the number, such as P-07."""
    return f"P-{number:02d}"


def _build_nodes() -> List[Node]:
    """Return the nodes of TREE, with IDs N-01, N-02, ... in tree order."""
    nodes: List[Node] = []

    def add(items: List[TreeItem], parent_id: str) -> None:
        """Add the items below parent_id, each followed by its children."""
        for position, (name, description, children) in enumerate(items):
            node = Node(f"N-{len(nodes) + 1:02d}", parent_id, name, description, position)
            nodes.append(node)
            add(list(children), node.id)

    add(TREE, "")
    return nodes


def _build_employees() -> List[Employee]:
    """Return the employees of TEAMS, with IDs E-0001, E-0002, ... and the skill gaps."""
    employees: List[Employee] = []
    for team, job_title, members in TEAMS:
        for name, career_level in members:
            number = len(employees) + 1
            gaps = SKILL_GAPS.get(number, "")
            employees.append(
                Employee(_employee_id(number), name, job_title, career_level, team, gaps)
            )
    return employees


def _build_projects() -> List[Project]:
    """Return the projects of PROJECTS, with IDs P-01, P-02, ..."""
    return [
        Project(_project_id(number), name, description, year, process)
        for number, (name, description, year, process) in enumerate(PROJECTS, start=1)
    ]


def _build_assignments(leaf_ids: Dict[str, str]) -> List[Assignment]:
    """Return the assignments of ASSIGNMENTS, with IDs A-001, A-002, ..."""
    return [
        Assignment(
            f"A-{number:03d}",
            _employee_id(employee),
            _project_id(project),
            leaf_ids[leaf],
            participation,
            description,
        )
        for number, (employee, project, leaf, participation, description) in enumerate(
            ASSIGNMENTS, start=1
        )
    ]


def _build_flags(leaf_ids: Dict[str, str]) -> List[Flag]:
    """Return the flags of FLAGS."""
    return [Flag(_employee_id(employee), leaf_ids[leaf], flag) for employee, leaf, flag in FLAGS]


def build() -> SeedData:
    """Return the seed data. Each call gives the same records (D-26)."""
    nodes = _build_nodes()
    leaf_ids = {node.name: node.id for node in nodes}
    return SeedData(
        employees=_build_employees(),
        projects=_build_projects(),
        nodes=nodes,
        assignments=_build_assignments(leaf_ids),
        flags=_build_flags(leaf_ids),
    )
