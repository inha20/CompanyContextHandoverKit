"""Command line interface: init / check / build / log."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"
FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
PLACEHOLDER = "TODO"

# Files that make up a handover folder, in the order they are given to the model.
REQUIRED = [
    "01_company_profile.md",
    "02_current_status.md",
    "03_glossary.md",
    "04_rules_and_constraints.md",
    "05_people_and_roles.md",
    "06_ongoing_tasks.md",
    "07_decision_log.md",
    "08_changelog.md",
]
# Files whose content changes often; these are checked for staleness.
VOLATILE = {"02_current_status.md", "06_ongoing_tasks.md"}


def parse_front(text: str) -> tuple[dict[str, str], str]:
    text = text.replace("\r\n", "\n")
    m = FRONT_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def estimate_tokens(text: str) -> int:
    """Rough estimate: ~4 chars/token for ASCII, ~1.5 chars/token for CJK."""
    cjk = sum(1 for c in text if ord(c) > 0x2E80)
    return int((len(text) - cjk) / 4 + cjk / 1.5)


def cmd_init(args) -> int:
    dest = Path(args.dir)
    if dest.exists() and any(dest.iterdir()) and not args.force:
        print(f"error: {dest} is not empty (use --force)", file=sys.stderr)
        return 1
    dest.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    files = sorted(TEMPLATE_DIR.glob("*.md"))
    for src in files:
        text = src.read_text(encoding="utf-8").replace("{{DATE}}", today)
        (dest / src.name).write_text(text, encoding="utf-8")
    print(f"created handover folder: {dest}  ({len(files)} files)")
    return 0


def check_folder(folder: Path, max_age: int, today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    problems = []
    for name in REQUIRED:
        path = folder / name
        if not path.exists():
            problems.append(f"{name}: missing")
            continue
        meta, body = parse_front(path.read_text(encoding="utf-8"))
        if PLACEHOLDER in body:
            problems.append(f"{name}: contains unfilled {PLACEHOLDER} placeholder")
        updated = meta.get("updated")
        try:
            age = (today - dt.date.fromisoformat(updated)).days
        except (TypeError, ValueError):
            problems.append(f"{name}: missing or invalid 'updated:' date")
            continue
        if name in VOLATILE and age > max_age:
            problems.append(f"{name}: stale ({age} days since update, limit {max_age})")
    return problems


def cmd_check(args) -> int:
    folder = Path(args.dir)
    if not folder.is_dir():
        print(f"error: {folder} not found", file=sys.stderr)
        return 1
    problems = check_folder(folder, args.max_age)
    for p in problems:
        print("WARN", p)
    print("OK: handover folder is complete and fresh" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def build_pack(folder: Path) -> str:
    parts = []
    for name in REQUIRED:
        path = folder / name
        if not path.exists():
            continue
        meta, body = parse_front(path.read_text(encoding="utf-8"))
        parts.append(f'<document name="{name}" updated="{meta.get("updated", "unknown")}">\n{body.strip()}\n</document>')
    header = (
        "아래는 이 회사의 인수인계 문서입니다. 이후 모든 답변은 이 문서를 기준으로 하세요.\n"
        "문서에 없는 내용은 추측하지 말고 '문서에 없음'이라고 답한 뒤 확인을 요청하세요.\n"
        "문서 간 내용이 충돌하면 updated 날짜가 최신인 문서를 우선하고 충돌 사실을 알리세요.\n"
    )
    return header + "\n" + "\n\n".join(parts) + "\n"


def cmd_build(args) -> int:
    folder = Path(args.dir)
    if not folder.is_dir():
        print(f"error: {folder} not found", file=sys.stderr)
        return 1
    pack = build_pack(folder)
    tokens = estimate_tokens(pack)
    if args.output:
        Path(args.output).write_text(pack, encoding="utf-8")
        print(f"wrote {args.output}  (~{tokens} tokens)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(pack)
        print(f"(~{tokens} tokens)", file=sys.stderr)
    return 0


def cmd_log(args) -> int:
    path = Path(args.dir) / "08_changelog.md"
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 1
    today = dt.date.today().isoformat()
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    text = re.sub(r"^updated:.*$", f"updated: {today}", text, count=1, flags=re.M)
    text = text.rstrip("\n") + f"\n- {today} {args.message}\n"
    path.write_text(text, encoding="utf-8")
    print(f"logged: {args.message}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="companytoai", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a handover folder from templates")
    s.add_argument("dir")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("check", help="validate completeness and freshness")
    s.add_argument("dir")
    s.add_argument("--max-age", type=int, default=30, help="max days for volatile files")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("build", help="assemble a context pack to paste into an LLM")
    s.add_argument("dir")
    s.add_argument("-o", "--output")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("log", help="append an entry to the changelog")
    s.add_argument("dir")
    s.add_argument("message")
    s.set_defaults(func=cmd_log)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
