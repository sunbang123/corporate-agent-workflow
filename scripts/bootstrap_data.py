"""생성물 데이터를 시드에서 복원한다 — 클린 클론에서 가장 먼저 실행할 것.

왜 필요한가. `data/advanced/*.db` 는 SQLite 바이너리라
상위 저장소의 `.gitignore` 에 있는 `*.db` 규칙에 **조용히 걸립니다.**
로컬에서는 잘 돌지만 클린 클론에서는 Day 2 노트북이 즉시 죽습니다.
(Codex 리뷰가 이 함정을 찾아냈습니다.)

그래서 `*.sql` 을 source of truth 로 추적하고, `.db` 는 여기서 만듭니다.
노트북도 DB 가 없으면 스스로 이 스크립트를 불러 복원하므로, 잊어도 진행은 됩니다.

세 가지를 지킵니다.

1. **원자성** — 임시 파일에 완성한 뒤 `replace()` 로 갈아 끼웁니다.
   중간에 실패하면 기존 DB 가 그대로 남고, 반쯤 만들어진 DB 가 남지 않습니다.
2. **스키마 검증** — "파일이 있으면 건너뛴다" 가 아니라 **필요한 테이블이 다 있는지**
   봅니다. 빈 껍데기 DB(노트북이 실수로 만든 0바이트 파일 등)를 건너뛰지 않습니다.
3. **정본 동기화** — `requests.db` 의 `emails` 는 실행할 때마다
   `sample_emails.json` 과 완전히 맞춥니다. JSON 에서 지운 메일은 DB 에서도 지웁니다.
   `drafts`·`tickets` 같은 실행 기록은 건드리지 않습니다.

실행: uv run python scripts/bootstrap_data.py [--force]
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADVANCED = ROOT / "data" / "advanced"

SEEDS = [
    (ADVANCED / "employees.sql", ADVANCED / "employees.db"),
    (ADVANCED / "inventory.sql", ADVANCED / "inventory.db"),
    (ADVANCED / "requests.sql", ADVANCED / "requests.db"),
]

# "이 테이블이 없으면 그 DB 는 쓸 수 없다" — 존재 여부가 아니라 이것으로 판정한다.
REQUIRED_TABLES = {
    "employees.db": ("departments", "employees"),
    "inventory.db": ("office_supplies", "it_assets"),
    "requests.db": ("budget_ledger", "staff_roster", "tickets", "drafts", "emails"),
}

# requests.db 의 emails 만 시드가 아니라 JSON 에서 채운다.
# 같은 메일 40건을 .sql 에도 적어 두면 두 정본이 생기고, 고칠 때 한쪽만 고치게 된다.
EMAIL_SOURCE = ROOT / "data" / "emails" / "sample_emails.json"
EMAIL_COLUMNS = ("id", "subject", "sender", "recipient", "received_at",
                 "body", "priority", "category")


def read_email_rows() -> list[tuple]:
    """JSON 을 **먼저 전부 읽고 검증한다.** DB 를 건드리기 전에 실패해야 하기 때문이다."""
    if not EMAIL_SOURCE.exists():
        raise SystemExit(f"메일 원본이 없습니다: {EMAIL_SOURCE.relative_to(ROOT)}")
    try:
        payload = json.loads(EMAIL_SOURCE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"메일 원본을 읽을 수 없습니다: {error}") from error

    if not isinstance(payload, list):
        raise SystemExit("메일 원본의 최상위는 배열이어야 합니다.")

    text_fields = ("subject", "from", "to", "date", "body", "priority", "category")
    rows, seen = [], set()
    for i, e in enumerate(payload):
        if not isinstance(e, dict):
            raise SystemExit(f"메일 {i}번이 객체가 아닙니다: {type(e).__name__}")
        missing = {"id", *text_fields} - e.keys()
        if missing:
            raise SystemExit(f"메일 {i}번에 필드가 없습니다: {sorted(missing)}")
        # ★id 는 타입까지 본다. None 이 통과하면 SQLite 가 새 id 를 배정하고,
        #   DELETE ... NOT IN (…, NULL) 은 아무것도 지우지 않아 동기화 계약이 조용히 깨진다.
        if not isinstance(e["id"], int) or isinstance(e["id"], bool) or e["id"] <= 0:
            raise SystemExit(f"메일 {i}번의 id 가 양의 정수가 아닙니다: {e['id']!r}")
        for key in text_fields:
            if not isinstance(e[key], str):
                raise SystemExit(f"메일 {e['id']}번의 {key} 가 문자열이 아닙니다: {type(e[key]).__name__}")
        if e["id"] in seen:
            raise SystemExit(f"메일 id 가 중복됩니다: {e['id']}")
        seen.add(e["id"])
        rows.append((e["id"], e["subject"], e["from"], e["to"], e["date"],
                     e["body"], e["priority"], e["category"]))
    if not rows:
        raise SystemExit("메일 원본이 비어 있습니다.")
    return rows


def sync_emails(con: sqlite3.Connection, rows: list[tuple]) -> None:
    """emails 를 JSON 과 **완전히** 맞춘다 — 넣고, 고치고, JSON 에 없는 것은 지운다."""
    placeholders = ", ".join("?" * len(EMAIL_COLUMNS))
    con.executemany(
        f"INSERT OR REPLACE INTO emails ({', '.join(EMAIL_COLUMNS)}) VALUES ({placeholders})",
        rows)
    keep = [r[0] for r in rows]
    con.execute(
        f"DELETE FROM emails WHERE id NOT IN ({', '.join('?' * len(keep))})", keep)


def tables_of(db_path: Path) -> set[str]:
    try:
        with sqlite3.connect(db_path) as con:
            return {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
    except sqlite3.DatabaseError:
        return set()


def is_healthy(db_path: Path) -> bool:
    """파일이 있는 것으로는 부족하다. 필요한 테이블이 다 있어야 건너뛴다."""
    if not db_path.exists():
        return False
    return set(REQUIRED_TABLES[db_path.name]) <= tables_of(db_path)


def build(force: bool = False) -> list[tuple[Path, bool]]:
    """시드에서 DB 를 만든다. 온전하면 건드리지 않는다(멱등)."""
    results = []
    for seed_path, db_path in SEEDS:
        if not seed_path.exists():
            raise SystemExit(f"시드가 없습니다: {seed_path.relative_to(ROOT)}")
        needs_email = db_path.name == "requests.db"
        # ★DB 를 건드리기 전에 입력을 전부 검증한다.
        rows = read_email_rows() if needs_email else []

        if is_healthy(db_path) and not force:
            if needs_email:                       # 실행 기록은 두고 정본만 맞춘다
                with sqlite3.connect(db_path) as con:
                    sync_emails(con, rows)
            results.append((db_path, False))
            continue

        # ★임시 파일에 완성한 뒤 원자적으로 갈아 끼운다.
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # ★임시 파일 이름에 PID 를 넣는다. 같은 이름을 쓰면 두 프로세스가
        #   서로의 파일을 지우고 교체해 원자성이 깨진다(동시 실행 재현됨).
        tmp_path = db_path.with_name(f"{db_path.name}.{os.getpid()}.tmp")
        try:
            with sqlite3.connect(tmp_path) as con:
                con.executescript(seed_path.read_text(encoding="utf-8"))
                if needs_email:
                    sync_emails(con, rows)
            tmp_path.replace(db_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        results.append((db_path, True))
    return results


if __name__ == "__main__":
    results = build(force="--force" in sys.argv)
    for db_path, created in results:
        with sqlite3.connect(db_path) as con:
            tables = sorted(t for t in tables_of(db_path) if t != "sqlite_sequence")
            summary = " · ".join(
                f"{t} {con.execute(f'select count(*) from {t}').fetchone()[0]}행" for t in tables)
        print(f"{'생성' if created else '확인(유지)'}: {db_path.relative_to(ROOT)}  —  {summary}")
