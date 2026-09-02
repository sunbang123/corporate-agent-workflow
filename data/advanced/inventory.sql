-- 합성 사내 재고/자산 DB — 교육용. 이 파일이 source of truth 이고 .db 는 생성물이다.
-- 재생성: uv run python scripts/bootstrap_data.py

BEGIN TRANSACTION;
CREATE TABLE office_supplies (
    item_id INTEGER PRIMARY KEY,
    item_name TEXT NOT NULL,
    stock_count INTEGER NOT NULL
);
INSERT INTO "office_supplies" VALUES(1,'A4 복사용지',50);
INSERT INTO "office_supplies" VALUES(2,'모나미 볼펜',120);
INSERT INTO "office_supplies" VALUES(3,'포스트잇',80);

CREATE TABLE it_assets (
    asset_id INTEGER PRIMARY KEY,
    asset_name TEXT NOT NULL,
    available_count INTEGER NOT NULL
);
INSERT INTO "it_assets" VALUES(1,'MacBook Pro 16',12);
INSERT INTO "it_assets" VALUES(2,'Dell 27인치 모니터',8);
INSERT INTO "it_assets" VALUES(3,'로지텍 무선 마우스',15);
COMMIT;
