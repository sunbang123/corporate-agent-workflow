-- 합성 사내 인사 DB — 교육용. 이 파일이 source of truth 이고 .db 는 생성물이다.
-- 재생성: uv run python scripts/bootstrap_data.py

BEGIN TRANSACTION;
CREATE TABLE departments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    manager TEXT,
    budget INTEGER
);
INSERT INTO "departments" VALUES('D001','개발팀','정대호',100000000);
INSERT INTO "departments" VALUES('D002','마케팅팀','이영희',50000000);
INSERT INTO "departments" VALUES('D003','인사팀',NULL,30000000);
INSERT INTO "departments" VALUES('D004','영업팀','강미나',80000000);
CREATE TABLE employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    position TEXT NOT NULL,
    email TEXT NOT NULL,
    salary INTEGER,
    hire_date TEXT
);
INSERT INTO "employees" VALUES('E001','김철수','개발팀','시니어 개발자','kim@company.com',6500,'2020-03-15');
INSERT INTO "employees" VALUES('E002','이영희','마케팅팀','팀장','lee@company.com',7500,'2018-01-10');
INSERT INTO "employees" VALUES('E003','박민수','개발팀','주니어 개발자','park@company.com',4500,'2023-06-01');
INSERT INTO "employees" VALUES('E004','최지은','인사팀','인사담당자','choi@company.com',5000,'2021-09-20');
INSERT INTO "employees" VALUES('E005','정대호','개발팀','팀장','jung@company.com',8500,'2017-05-25');
INSERT INTO "employees" VALUES('E006','한소라','마케팅팀','디자이너','han@company.com',5500,'2022-02-14');
INSERT INTO "employees" VALUES('E007','윤재민','영업팀','영업사원','yoon@company.com',5000,'2022-08-01');
INSERT INTO "employees" VALUES('E008','강미나','영업팀','팀장','kang@company.com',7000,'2019-04-12');
COMMIT;
