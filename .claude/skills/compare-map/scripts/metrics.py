"""Counts for the compare-map skill.

Reads one app map version (data/maps/<id>/vNNN.json) and the ChatGPT reference
HTML, and prints one JSON object with the same counts for both. With --week N
or --front it prints that week, or the front matter, from both sides as text
instead, for a side-by-side read.

Usage:
    python metrics.py [--map-id ID] [--version N] [--reference PATH] [--week N | --front]
Defaults: the newest map folder in MAPS_DIR (the environment, else
config/.env, else data/maps), its newest version, and the reference in
docs/references.
"""
import argparse
from collections import Counter
from datetime import datetime
import html
import json
import os
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from src.config import read_env_file  # noqa: E402


def setting(key: str, default: str) -> Path:
    """Return a folder setting: the environment, else config/.env, else the default under the repo."""
    value = os.environ.get(key) or read_env_file(ROOT / "config" / ".env").get(key)
    return ROOT / (value or default)


def shown(path: Path) -> str:
    """Return a path relative to the repo when it is under it, else as it is."""
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


MAPS_DIR = setting("MAPS_DIR", "data/maps")
COST_DIR = setting("COST_LOG_DIR", "log/cost")
DEFAULT_REFERENCE = ROOT / "docs" / "references" / "Grade_6_ELA_Curriculum_Map_2026-2027 - v2.html"
CATALOG_FILE = ROOT / "data" / "standards" / "ccss_ela_grade6.json"
LONG_CLASSWORK_CHARS = 100
MAX_SENTENCE_WORDS = 20
LONG_WORD_LETTERS = 9
ASSUMPTION_KEY_WORDS = 8
COURSE = "course"
UNKNOWN_TARGET = "unknown"
EXPORT_COMMAND = "run python main.py --html <map id> --version <n>"
# What html_facts counts in the app's map page (a regular expression per part).
PAGE_PARTS = {
    "weeks": r'data-id="week:\d+"',
    "lesson_rows": r'class="block kind-lesson[ "]',
    "lesson_details": r'class="lesson-detail"',
    "assumption_notes_inline": r'class="map-note kind-(?!screening[ "])',
    "screening_notes_inline": r'class="map-note kind-screening[ "]',
    "switches": r'<label class="map-switch"',
    "tabs": r'<a class="map-tab"',
}
# A map section's own heading: an h2 whose id is its block (section:<key>), a
# slash, and the slug of its text (src/backend/map_folds.py heading_ids_html).
SECTION_HEADING = re.compile(r'<h2 id="section:([^/"]+)/[^"]*">(.*?)</h2>', re.S)
PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+\w+(?:ed|en)\b", re.I)
FRONT_TEXT_CHARS = 14000


def words(text: str) -> int:
    """Count the words in a text."""
    return len(re.findall(r"\S+", text or ""))


def words_per_sentence(texts: list[str]) -> float:
    """Average words per sentence over several texts."""
    sentences = 0
    total = 0
    for text in texts:
        parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]
        sentences += len(parts)
        total += words(text)
    return round(total / sentences, 1) if sentences else 0.0


def normalize_code(code: str) -> str:
    """Map 'RL.6.1' and 'RL1' to 'RL1', and 'L.6.4.a' and 'L4a' to 'L4a'."""
    code = code.strip().replace("CCSS.ELA-Literacy.", "")
    dotted = re.fullmatch(r"([A-Z]+)\.6\.(\d+)(?:\.([a-z]))?", code)
    if dotted:
        return f"{dotted.group(1)}{dotted.group(2)}{dotted.group(3) or ''}"
    return code.replace(".", "")


def clean(fragment: str) -> str:
    """Strip tags and decode entities from an HTML fragment."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def share(count: int, total: int) -> float:
    """A rounded share, 0 when there is nothing to divide by."""
    return round(count / total, 2) if total else 0.0


def summarize(rows: list[dict]) -> dict:
    """Turn normalized plan rows into the counts both sides share."""
    lessons = [r for r in rows if r["type"] == "lesson"]
    n = len(lessons)
    classwork = [r["classwork"] for r in lessons if r["classwork"]]
    objectives = [o for r in lessons for o in r["objectives"]]
    supports = [s.strip().lower() for r in lessons for s in r["supports"]]
    codes = {normalize_code(c) for r in rows for c in r["standards"]}
    return {
        "rows_by_type": {t: sum(1 for r in rows if r["type"] == t) for t in sorted({r["type"] for r in rows})},
        "lesson_rows": n,
        "classwork_words_avg": round(statistics.mean([words(c) for c in classwork] or [0]), 1),
        "classwork_words_max": max([words(c) for c in classwork], default=0),
        "classwork_share_over_100_chars": share(sum(len(c) > LONG_CLASSWORK_CHARS for c in classwork), n),
        "classwork_words_per_sentence": words_per_sentence(classwork),
        "classwork_repeated_share": share(len(classwork) - len({c.lower() for c in classwork}), n),
        "objectives_per_lesson": share(len(objectives), n),
        "objective_words_avg": round(statistics.mean([words(o) for o in objectives] or [0]), 1),
        "objective_words_per_sentence": words_per_sentence(objectives),
        "standards_per_lesson": share(sum(len(r["standards"]) for r in lessons), n),
        "distinct_standard_codes": len(codes),
        "strategies_per_lesson": share(sum(len(r["strategies"]) for r in lessons), n),
        "support_entries_per_lesson": share(len(supports), n),
        "support_words_avg": round(statistics.mean([words(s) for s in supports] or [0]), 1),
        "support_texts_repeated_share": share(len(supports) - len(set(supports)), len(supports)),
        "lessons_with_homework_share": share(sum(bool(r["homework"]) for r in lessons), n),
        "lessons_with_resources_share": share(sum(bool(r["resources"]) for r in lessons), n),
        "total_words_in_weekly_plan": sum(
            words(" ".join([r["classwork"], r["homework"], *r["objectives"], *r["supports"], *r["resources"]]))
            for r in rows
        ),
    }


def sentences(texts: list[str]) -> list[str]:
    """Split texts into sentences."""
    return [p for text in texts for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]


def catalog_codes() -> set[str]:
    """The normalized standard codes of the grade 6 ELA catalog."""
    data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    entries = next(v for v in data.values() if isinstance(v, list))
    return {normalize_code(e["code"]) for e in entries}


def repeated(items: list[str], key_words: int = 0) -> float:
    """Share of items that repeat an earlier one (compared on their first key_words words, or whole)."""
    keys = [" ".join(i.lower().split()[: key_words or None]) for i in items]
    return share(len(keys) - len(set(keys)), len(keys))


def measures(rows: list[dict], assumptions: list[str]) -> dict:
    """The four report measures: precision, length, plain English, assumptions noise."""
    lessons = [r for r in rows if r["type"] == "lesson"]
    n = len(lessons)
    codes = [normalize_code(c) for r in lessons for c in r["standards"]]
    known = catalog_codes()
    classwork = [r["classwork"] for r in lessons if r["classwork"]]
    objectives = [o for r in lessons for o in r["objectives"]]
    supports = [s for r in lessons for s in r["supports"]]
    prose = sentences(classwork + objectives + supports)
    return {
        "precision": {
            "standard_codes_in_catalog_share": share(sum(c in known for c in codes), len(codes)),
            "lessons_over_4_codes_share": share(sum(len(r["standards"]) > 4 for r in lessons), n),
            "standards_lists_repeated_share": repeated([",".join(sorted(r["standards"])) for r in lessons]),
            "objectives_repeated_share": repeated(objectives),
            "classwork_repeated_share": repeated(classwork),
            "support_texts_repeated_share": repeated(supports),
        },
        "length": {
            "classwork_chars_avg": round(statistics.mean([len(c) for c in classwork] or [0])),
            "classwork_share_over_100_chars": share(sum(len(c) > LONG_CLASSWORK_CHARS for c in classwork), n),
            "words_per_row_avg": round(sum(words(" ".join([r["classwork"], r["homework"], *r["objectives"], *r["supports"], *r["resources"]])) for r in rows) / (len(rows) or 1), 1),
            "words_in_weekly_plan": sum(words(" ".join([r["classwork"], r["homework"], *r["objectives"], *r["supports"], *r["resources"]])) for r in rows),
        },
        "plain_english": {
            "words_per_sentence_avg": words_per_sentence(classwork + objectives + supports),
            "sentences_over_20_words_share": share(sum(words(s) > MAX_SENTENCE_WORDS for s in prose), len(prose)),
            "sentences_with_passive_share": share(sum(bool(PASSIVE.search(s)) for s in prose), len(prose)),
            "long_words_share": share(sum(len(w) >= LONG_WORD_LETTERS for s in prose for w in re.findall(r"[A-Za-z]+", s)), sum(words(s) for s in prose)),
        },
        "assumptions_noise": {
            "assumptions": len(assumptions),
            "words_avg": round(statistics.mean([words(a) for a in assumptions] or [0]), 1),
            "repeated_share": repeated(assumptions, key_words=ASSUMPTION_KEY_WORDS),
            "with_source_citation_share": share(sum("[Source" in a for a in assumptions), len(assumptions)),
            "per_10_lessons": round(len(assumptions) / (n or 1) * 10, 2),
        },
    }


def html_facts(path: Path) -> dict:
    """Facts about the app's exported map page (read by its structure, not its text), or a note when there is no export or it is older than the page (no weeks to count). sections lists the first h2 of each section block (one per map section, never a subsection); assumption notes (assumptions, open questions, limitations) and screening notes are counted apart. lesson_rows counts every plan row: the page draws each row, of any type, as a lesson block."""
    if not path.exists():
        return {"file": None, "note": f"no export; {EXPORT_COMMAND}"}
    source = path.read_text(encoding="utf-8")
    markup = re.sub(r"<(script|style)\b.*?</\1>", "", source, flags=re.S | re.I)
    counts = {name: len(re.findall(pattern, markup)) for name, pattern in PAGE_PARTS.items()}
    if not counts["weeks"]:
        return {"file": shown(path), "note": f"older export; {EXPORT_COMMAND}"}
    section_labels = {}
    for key, label in SECTION_HEADING.findall(markup):
        section_labels.setdefault(key, label)
    return {
        "file": shown(path),
        "size_kb": round(path.stat().st_size / 1024),
        "has_scripts": "<script" in source,
        "has_remote_stylesheet": bool(re.search(r'<link[^>]+href="https?:', source)),
        **counts,
        "search_toolbar": 'class="map-toolbar"' in markup,
        "sections": [clean(label) for label in section_labels.values()],
    }


def count_by(items: list, key: str) -> dict:
    """Count dict items by the value of one key."""
    counts: dict = {}
    for item in items:
        if isinstance(item, dict):
            value = str(item.get(key))
            counts[value] = counts.get(value, 0) + 1
    return counts


def target_kinds(plan: dict) -> dict[str, str]:
    """The kind of every id an assumption can be about, as the app counts them (src/backend/map_ids.py and week ids such as W05)."""
    assessments = plan.get("assessments") or {}
    groups = {
        "material": plan.get("materials", []),
        "module": plan.get("modules", []),
        "content item": plan.get("content_items", []),
        "assessment": [i for key in ("exam_windows", "projects", "ongoing_strands") for i in assessments.get(key, [])],
        "unit": [unit for week in plan["weeks"] for unit in week["units"]],
        "week": [{"id": f"W{week['week_number']:02d}"} for week in plan["weeks"]],
    }
    kinds = {COURSE: COURSE}
    for kind, items in groups.items():
        kinds.update({item["id"]: kind for item in items})
    return kinds


def assumption_anchoring(plan: dict) -> dict:
    """The share of assumptions about a real id of the map other than the course, and the count by kind of target. A map saved before the `about` tag reads as all course."""
    kinds = target_kinds(plan)
    targets = [kinds.get(a.get("about", COURSE), UNKNOWN_TARGET) for a in plan.get("assumptions", [])]
    anchored = sum(t not in (COURSE, UNKNOWN_TARGET) for t in targets)
    return {"assumptions_anchored_share": share(anchored, len(targets)), "by_target": dict(Counter(targets))}


def app_rows(plan: dict) -> list[dict]:
    """Normalize the unit rows of an app map."""
    rows = []
    for week in plan["weeks"]:
        for unit in week["units"]:
            rows.append({
                "type": str(unit.get("type", "lesson")).lower(),
                "classwork": unit.get("classwork") or "",
                "homework": unit.get("homework") or "",
                "objectives": unit.get("learning_objectives") or [],
                "standards": unit.get("standards") or [],
                "strategies": unit.get("teaching_strategies") or [],
                "supports": [d.get("support", "") for d in unit.get("differentiation") or []],
                "resources": unit.get("resources") or [],
            })
    return rows


def cost_facts(map_id: str) -> dict:
    """Read the models, calls, and cost rows from the map's cost report, if there is one."""
    for report in COST_DIR.glob(f"*{map_id}.md"):
        text = report.read_text(encoding="utf-8")
        facts = {"models": re.findall(r"^\| Model \| (.+?) \|", text, flags=re.M) or re.findall(r"^\| Prices ([A-Za-z][\w.-]*) ", text, flags=re.M)}
        for label, key in (("Calls", "calls"), ("Cost (USD, approximate)", "cost_usd")):
            match = re.search(rf"\| {re.escape(label)} \| (.+?) \|", text)
            if match:
                facts[key] = match.group(1)
        stages = re.findall(r"^\| ([a-z ]+) \| (\S+) \| \d+ \|", text, flags=re.M)
        facts["model_by_stage"] = {stage.strip(): model for stage, model in stages}
        times = re.findall(r"^\| (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \|", text, flags=re.M)
        if len(times) > 1:
            facts["generation_minutes"] = round((datetime.fromisoformat(times[-1]) - datetime.fromisoformat(times[0])).total_seconds() / 60)
        return facts
    return {}


def app_report(path: Path) -> dict:
    """Counts and facts for one app map version."""
    version = json.loads(path.read_text(encoding="utf-8"))
    plan = version["map"]
    report = {"label": f"{version['map_id']} {path.stem}", "file": shown(path)}
    report.update(cost_facts(version["map_id"]))
    rows = app_rows(plan)
    report.update(summarize(rows))
    report["measures"] = measures(rows, [a["text"] for a in plan.get("assumptions", [])])
    report["measures"]["assumptions_noise"]["by_kind"] = count_by(plan.get("assumptions", []), "kind")
    report["measures"]["assumptions_noise"].update(assumption_anchoring(plan))
    items = plan.get("content_items", [])
    report["html_export"] = html_facts(path.with_suffix(".html"))
    report.update({
        "event": version.get("event"),
        "saved_at": version.get("saved_at"),
        "weeks": len(plan["weeks"]),
        "sections_filled": [k for k, v in plan.items() if v not in (None, [], {}, "") and k != "standards_appendix"],
        "grading": [[g["name"], g["weight_percent"]] for g in plan.get("grading_criteria", [])],
        "modules": len(plan.get("modules", [])),
        "content_items": len(items),
        "content_items_by_suitability": count_by([i.get("suitability") or {} for i in items], "status"),
        "assumptions": len(plan.get("assumptions", [])),
        "notes": len(plan.get("notes", [])),
        "integrity_checks": count_by(version.get("integrity") or [], "status"),
        "review_issues_by_severity": count_by((version.get("review") or {}).get("issues", []), "severity"),
    })
    return report


def split_list(text: str) -> list[str]:
    """Split a ';' or ',' separated cell into items."""
    return [p.strip() for p in re.split(r"[;,]", text) if p.strip()]


def reference_rows(source: str) -> list[dict]:
    """Normalize the lesson cards of the reference HTML."""
    rows = []
    for card in re.findall(r'<details class="lesson-card type-[^>]*>.*?</details>', source, flags=re.S):
        pairs = re.findall(r'<div class="lesson-field[^"]*"><span>(.*?)</span><p>(.*?)</p>', card, flags=re.S)
        fields = {clean(k): clean(v) for k, v in pairs}
        kind = re.search(r'data-type="([^"]+)"', card)
        objective = fields.get("Learning Objectives", "")
        support = fields.get("Differentiation / Learning Support", "")
        rows.append({
            "type": (kind.group(1) if kind else "lesson").lower(),
            "classwork": fields.get("Classwork", ""),
            "homework": fields.get("Homework", ""),
            "objectives": [objective] if objective else [],
            "standards": split_list(fields.get("Standards", "")),
            "strategies": split_list(fields.get("Teaching strategies", "")),
            "supports": [support] if support else [],
            "resources": [],
        })
    return rows


def reference_assumptions(source: str) -> list[str]:
    """The list items of the reference's Assumptions section."""
    start = source.find("Assumptions</h2>")
    return [clean(item) for item in re.findall(r"<li>(.*?)</li>", source[start:], flags=re.S)] if start >= 0 else []


def reference_report(path: Path) -> dict:
    """Counts and facts for the ChatGPT reference HTML."""
    source = path.read_text(encoding="utf-8")
    report = {"label": "ChatGPT reference", "file": path.name}
    rows = reference_rows(source)
    report.update(summarize(rows))
    report["measures"] = measures(rows, reference_assumptions(source))
    report.update({
        "weeks": len(re.findall(r'<details class="week-card', source)),
        "sections_filled": [clean(h) for h in re.findall(r"<h2[^>]*>(.*?)</h2>", source, flags=re.S)],
    })
    return report


def reference_week_text(source: str, number: int) -> str:
    """The text of one week card of the reference, one line per field."""
    start = source.find(f'id="week-{number}"')
    end = source.find('<details class="week-card', start + 1)
    card = source[start:end if end > 0 else None]
    card = re.sub(r"</(p|div|summary)>", "\n", card)
    lines = [clean(line) for line in card.split("\n")]
    return "\n".join(line for line in lines if line)


def app_week_text(path: Path, number: int) -> str:
    """The text of one week of an app map, one line per field."""
    plan = json.loads(path.read_text(encoding="utf-8"))["map"]
    week = next(w for w in plan["weeks"] if w["week_number"] == number)
    lines = [f"Week {number}: {week['start_date']} to {week['end_date']}"]
    for unit in week["units"]:
        lines.append(f"[{unit['id']} {unit['type']}] {unit['topic']}")
        for key in ("learning_objectives", "standards", "teaching_strategies", "differentiation", "classwork", "homework"):
            if unit.get(key):
                lines.append(f"  {key}: {unit[key]}")
    return "\n".join(lines)


def reference_front_text(source: str) -> str:
    """The text of the reference before its weekly plan (description, objectives, materials, grading)."""
    start = source.find("Course Description</h2>")
    end = source.find("Detailed Chronological Teacher Plan</h2>", start)
    block = re.sub(r"</(p|div|li|tr|h\d)>", "\n", source[start:end])
    lines = [clean(line) for line in block.split("\n")]
    return "\n".join(line for line in lines if line)[:FRONT_TEXT_CHARS]


def app_front_text(path: Path) -> str:
    """The front matter of an app map (everything before the weeks), as JSON text."""
    plan = json.loads(path.read_text(encoding="utf-8"))["map"]
    keys = ("course_description", "course_objectives", "learning_outcomes", "teaching_strategies",
            "materials", "modules", "grading_criteria", "assessments", "pacing_guide", "notes", "assumptions")
    return json.dumps({k: plan.get(k) for k in keys}, ensure_ascii=False, indent=1)[:FRONT_TEXT_CHARS]


def version_file(map_id: str | None, version: int | None) -> Path:
    """Find the version file: the given map and version, or the newest of each."""
    if map_id:
        folder = MAPS_DIR / map_id
    else:
        folder = max((p for p in MAPS_DIR.iterdir() if list(p.glob("v*.json"))), key=lambda p: p.name)
    return folder / f"v{version:03d}.json" if version else max(folder.glob("v*.json"))


def main() -> None:
    """Print the counts for the app map and the reference, or one week from both."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-id")
    parser.add_argument("--version", type=int)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--week", type=int, help="print this week from both sides as text, not the counts")
    parser.add_argument("--front", action="store_true", help="print the front matter from both sides as text")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    path = version_file(args.map_id, args.version)
    if args.front:
        reference = args.reference.read_text(encoding="utf-8")
        sys.stdout.write(f"=== APP ===\n{app_front_text(path)}\n\n=== REFERENCE ===\n{reference_front_text(reference)}\n")
        return
    if args.week:
        reference = args.reference.read_text(encoding="utf-8")
        app_text = app_week_text(path, args.week)
        reference_text = reference_week_text(reference, args.week)
        sys.stdout.write(f"=== APP ===\n{app_text}\n\n=== REFERENCE ===\n{reference_text}\n")
        return
    out = {"app": app_report(path), "reference": reference_report(args.reference)}
    sys.stdout.write(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
