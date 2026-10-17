"""Offline fixture validation, including tests that the validator rejects unsafe input."""

import json
import re
from pathlib import Path
from urllib.parse import unquote

import pytest
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

FIXTURES = Path(__file__).parents[1] / "fixtures"


def fixture_violations(root: Path) -> list[str]:
    """Return parse/privacy problems without echoing potentially sensitive values."""
    problems: list[str] = []
    credential = re.compile(
        r"(?:access-key|authKey)[\s\"']*(?:=|:|>)[\s\"']*[A-Za-z0-9]{16,}", re.I
    )
    email = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@([A-Za-z0-9.-]+)")
    phone = re.compile(
        r"(?<![\w])(?:0\d{1,2}[- .]\d{3,4}[- .]\d{4}|0\d{8,10}|1[568]\d{2}-\d{4})(?![\w])"
    )
    safe_phone = re.compile(r"(?:02|0\d{2})[- .]0{3,4}[- .]0{4}|0{9,11}|1[568]00-0000")
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        label = path.relative_to(root).as_posix()
        try:
            raw = path.read_text(encoding="utf-8")
        except UnicodeError:
            problems.append(f"{label}: parse (UTF-8)")
            continue
        text = raw
        try:
            if path.suffix == ".json":
                text += "\n" + json.dumps(json.loads(raw), ensure_ascii=False)
            elif path.suffix == ".xml":
                parsed = ElementTree.fromstring(raw)
                text += "\n" + "\n".join(parsed.itertext())
        except ValueError, ElementTree.ParseError, DefusedXmlException:
            problems.append(f"{label}: parse")
        text = unquote(text)
        if credential.search(text):
            problems.append(f"{label}: credential")
        if any(match.group(1).lower() != "example.com" for match in email.finditer(text)):
            problems.append(f"{label}: email")
        if any(not safe_phone.fullmatch(match.group()) for match in phone.finditer(text)):
            problems.append(f"{label}: phone")
    return problems


@pytest.mark.parametrize(
    ("filename", "content", "reason"),
    [
        ("bad.json", "{", "parse"),
        ("bad.xml", "<wantedRoot>", "parse"),
        ("key.txt", "access-key=" + "a" * 16, "credential"),
        ("key.txt", "authKey=" + "9" * 16, "credential"),
        ("key.json", json.dumps({"authKey": "a" * 16}), "credential"),
        ("key.xml", "<authKey>" + "a" * 16 + "</authKey>", "credential"),
        ("email.json", '{"email": "person@private.invalid"}', "email"),
        ("phone.xml", "<tel>02-1234-5678</tel>", "phone"),
        ("phone.txt", "01012345678", "phone"),
        ("phone.txt", "1577-1234", "phone"),
        ("nested/notes.md", "person@private.invalid", "email"),
        (
            "entity.xml",
            '<!DOCTYPE x [<!ENTITY secret "hidden">]><x>&secret;</x>',
            "parse",
        ),
    ],
)
def test_validator_rejects_violations(
    tmp_path: Path, filename: str, content: str, reason: str
) -> None:
    path = tmp_path / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    problems = fixture_violations(tmp_path)
    assert any(reason in problem for problem in problems)
    assert all(content not in problem for problem in problems)


def test_validator_accepts_sanitized_data(tmp_path: Path) -> None:
    (tmp_path / "safe.json").write_text(
        json.dumps(
            {
                "name": "홍길동",
                "email": "recruit@example.com",
                "phone": "02-0000-0000",
                "mobile": "010-0000-0000",
                "timestamp": "1792162800",
                "date": "2026-10-17",
                "url": "https://example.com/?wantedAuthNo=K000002610170001",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "safe.xml").write_text("<root><empty /></root>", encoding="utf-8")
    assert fixture_violations(tmp_path) == []


def test_repository_fixtures_are_parseable_and_sanitized() -> None:
    assert FIXTURES.is_dir(), "fixtures directory must exist"
    assert list(FIXTURES.rglob("*.json")), "JSON fixtures must exist"
    assert list(FIXTURES.rglob("*.xml")), "XML fixtures must exist"
    assert fixture_violations(FIXTURES) == []


def test_saramin_pages_are_complete_and_distinct() -> None:
    pages = [
        json.loads((FIXTURES / "saramin" / f).read_text())["jobs"]
        for f in ("list_ok.json", "list_page2.json")
    ]
    assert [page["start"] for page in pages] == [0, 1]
    assert len(pages[0]["job"]) >= 3
    assert all(page["count"] == len(page["job"]) for page in pages)
    ids = [job["id"] for page in pages for job in page["job"]]
    assert len(ids) == len(set(ids)) == int(pages[0]["total"]) == int(pages[1]["total"])


def test_work24_pages_are_complete_and_distinct() -> None:
    pages = [
        ElementTree.parse(FIXTURES / "work24" / f).getroot()
        for f in ("list_ok.xml", "list_page2.xml")
    ]
    assert [page.findtext("startPage") for page in pages] == ["1", "2"]
    assert len(pages[0].findall("wanted")) >= 3
    ids = [job.findtext("wantedAuthNo") for page in pages for job in page.findall("wanted")]
    assert len(ids) == len(set(ids)) == int(pages[0].findtext("total"))
    assert pages[0].findtext("total") == pages[1].findtext("total")


def test_sources_documents_every_response_fixture() -> None:
    sources = (FIXTURES / "SOURCES.md").read_text(encoding="utf-8")
    for path in FIXTURES.rglob("*"):
        if path.suffix in {".json", ".xml"}:
            assert path.relative_to(FIXTURES).as_posix() in sources
