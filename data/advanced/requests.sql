-- 합성 사내 업무요청 DB — 교육용. 이 파일이 source of truth 이고 .db 는 생성물이다.
-- 재생성: uv run python scripts/bootstrap_data.py
--
-- employees.db(인사) · inventory.db(재고) 와 나란히 서는 세 번째 DB 로,
-- Day 2 의 스파인(2-1 도구 계약 → 2-5 이메일 워크플로우 → 2-6 평가)이
-- 실제로 읽고 쓰는 곳이다. drafts·tickets 는 노트북이 실행 중에 채운다.
--
-- emails 테이블은 스키마만 여기에 있다. 행은 data/emails/sample_emails.json 에서
-- bootstrap_data.py 가 적재한다 — 같은 데이터를 두 곳에 두면 반드시 어긋나기 때문이다.

BEGIN TRANSACTION;

-- 부서 예산 원장 — employees.db 의 departments 와 부서명으로 대응한다.
-- allocated 는 departments.budget 과 같고, spent 를 빼면 이번 분기 잔액이 된다.
CREATE TABLE budget_ledger (
    budget_code TEXT PRIMARY KEY,
    department  TEXT NOT NULL,
    fiscal_term TEXT NOT NULL,
    allocated   INTEGER NOT NULL,
    spent       INTEGER NOT NULL
);
INSERT INTO "budget_ledger" VALUES('B-101','개발팀','2026 Q3',100000000,96880000);
INSERT INTO "budget_ledger" VALUES('B-102','마케팅팀','2026 Q3',50000000,41550000);
INSERT INTO "budget_ledger" VALUES('B-103','인사팀','2026 Q3',30000000,12400000);
INSERT INTO "budget_ledger" VALUES('B-104','영업팀','2026 Q3',80000000,74300000);

-- 담당자 명부 — 티켓 담당자 지정의 런타임 검증용.
-- active=0 인 오세훈은 퇴사자다. 문자열 타입은 맞으므로 스키마 검증은 통과하고,
-- 몸통의 DB 조회에서만 걸린다 — 블록 2-1 의 "스키마가 못 잡는 것" 시연 재료.
CREATE TABLE staff_roster (
    name   TEXT PRIMARY KEY,
    team   TEXT NOT NULL,
    active INTEGER NOT NULL
);
INSERT INTO "staff_roster" VALUES('김철수','개발팀',1);
INSERT INTO "staff_roster" VALUES('이영희','마케팅팀',1);
INSERT INTO "staff_roster" VALUES('박민수','개발팀',1);
INSERT INTO "staff_roster" VALUES('최지은','인사팀',1);
INSERT INTO "staff_roster" VALUES('정대호','개발팀',1);
INSERT INTO "staff_roster" VALUES('한소라','마케팅팀',1);
INSERT INTO "staff_roster" VALUES('윤재민','영업팀',1);
INSERT INTO "staff_roster" VALUES('강미나','영업팀',1);
INSERT INTO "staff_roster" VALUES('오세훈','개발팀',0);

-- 티켓 — 부작용(쓰기) 도구가 실제로 남기는 곳. 아래 두 건은 과거 이력이다.
CREATE TABLE tickets (
    ticket_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    severity   TEXT NOT NULL,
    assignee   TEXT NOT NULL,
    email_id   INTEGER,
    status     TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL
);
INSERT INTO "tickets" VALUES(1,'VPN 접속 지연 신고','P2','정대호',NULL,'closed','2026-08-11T09:20:00');
INSERT INTO "tickets" VALUES(2,'사내 위키 권한 요청','P3','최지은',NULL,'closed','2026-08-19T14:05:00');

-- 초안 — 이메일 워크플로우의 save_draft 노드와 승인 게이트가 쓰는 곳.
-- 시드는 비어 있다. 노트북이 실행하면서 채운다.
CREATE TABLE drafts (
    draft_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id   INTEGER NOT NULL,
    thread_id  TEXT NOT NULL,
    revision   INTEGER NOT NULL,
    body       TEXT NOT NULL,
    status     TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 수신 메일 — 스키마만. 행은 sample_emails.json 이 정본이고 부트스트랩이 적재한다.
CREATE TABLE emails (
    id          INTEGER PRIMARY KEY,
    subject     TEXT NOT NULL,
    sender      TEXT NOT NULL,
    recipient   TEXT NOT NULL,
    received_at TEXT NOT NULL,
    body        TEXT NOT NULL,
    priority    TEXT NOT NULL,
    category    TEXT NOT NULL
);

COMMIT;
