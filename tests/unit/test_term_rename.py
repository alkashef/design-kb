"""D-44: the earlier term of the person no longer appears under src/ and tests/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EARLIER_TERM = "emp" + "loyee"
TEXT_SUFFIXES = {".py", ".html", ".css", ".js"}


def test_d_44_no_file_under_src_and_tests_holds_the_earlier_term():
    hits = []
    for folder in ("src", "tests"):
        for path in (ROOT / folder).rglob("*"):
            if "__pycache__" in path.parts or not path.is_file():
                continue
            if EARLIER_TERM in path.name.lower():
                hits.append(str(path.relative_to(ROOT)))
            elif path.suffix in TEXT_SUFFIXES:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if EARLIER_TERM in text.lower():
                    hits.append(str(path.relative_to(ROOT)))
    assert hits == []
