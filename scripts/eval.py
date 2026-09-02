"""평가 러너 · 스냅숏 · 게이트 — 블록 2-6 (D20 · D21).

세 가지를 한 파일에 둔다.

    uv run python scripts/eval.py run --out measurements/eval_snapshot_baseline.json
    uv run python scripts/eval.py run --variant terse --out measurements/eval_snapshot_candidate.json
    uv run python scripts/eval.py gate --baseline … --candidate …

ezis-ai-advanced/M04/tools 는 이것을 세 파일(eval_run·eval_snapshot·eval_gate)로 나눈다.
그쪽은 개발자 심화 과정이라 그래도 되지만, 여기서는 파일 셋을 오가는 것 자체가 비용이다.
대신 **규율은 하나도 낮추지 않는다.** 이 파일이 지키는 네 가지가 D20·D21 의 내용이다.

1. **잴 수 없는 것은 0이 아니라 None 이다.**
   trap 문항에는 정답이 없다. 여기에 0점을 주면 "틀렸다"가 되어 평균이 조용히 내려가고,
   거절을 잘한 모델이 벌을 받는다. 지표가 행동을 만든다 — 잘못 만든 지표는 잘못된 행동을 만든다.

2. **조인은 case_id 로 한다. zip 금지.**
   문항 하나가 추가·삭제되면 zip 은 전부 한 칸씩 밀린 채로 그럴듯한 점수를 낸다.
   이것이 D20 의 A 군이다.

3. **못 견주면 견주지 않는다.**
   평가셋이 바뀌었으면 두 스냅숏은 비교 대상이 아니다. comparable() 이 그 이유를 한국어로 말한다.

4. **미측정은 통과가 아니라 실패다(fail-closed).**
   "못 쟀다"를 통과로 처리하면 게이트는 고장 났을 때 가장 관대해진다. 정확히 거꾸로여야 한다.

의도적으로 넣지 않은 것 — ratchet(임계값 자동 상향)과 --require-baseline.
운영에서는 필요하지만 이 과정의 60분으로는 다 못 다룬다. 학습 경로로만 안내한다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data/golden_emails.jsonl"
EMAILS = ROOT / "data/emails/sample_emails.json"
THRESHOLDS = ROOT / "data/thresholds.json"

MODEL = "gpt-4.1-mini"
SCHEMA = "corp-agent-eval-snapshot/1"

# 세 지표. 각각 어느 kind 에서만 잴 수 있는지가 함께 적혀 있다 —
# 이 표가 곧 "None 을 언제 내는가"의 정의다.
METRICS = {
    "route":   {"kind": "route",   "label": "우선순위 분류"},
    "facts":   {"kind": "extract", "label": "근거 사실 포함"},
    "refusal": {"kind": "trap",    "label": "모르는 것을 모른다고 함"},
}

# ── 파이프라인 ───────────────────────────────────────────────────────

SYS_BASE = (
    "사내 이메일 처리 도우미입니다.\n"
    "- 우선순위를 묻는 질문에는 urgent / normal / low 중 하나만 답하세요.\n"
    "  urgent=즉시 대응(장애·보안·마감임박), normal=업무상 처리 필요, low=참고/공지성.\n"
    "- 그 밖의 질문에는 메일 본문에 적힌 내용만으로 답하세요.\n"
    "- 본문에 근거가 없으면 추측하지 말고 정확히 '모르겠습니다'라고 답하세요."
)

# D21 의 candidate — "분류가 자꾸 틀리니 기준을 더 또렷하게 적자"는, 가장 흔한 개선 시도다.
#
# 기준선의 오답 6건은 전부 low ↔ normal 경계에서 났다(공지·투표·온보딩 안내 같은 참고성 메일).
# 그래서 low 의 정의에 예시를 붙였다. 실제로 그 6건 중 여럿이 고쳐지고 평균은 오른다.
# 그런데 같은 규칙이 "알림"이라는 단어를 달고 있을 뿐 실제로는 처리가 필요한 메일까지 low 로 끌어내린다.
# **평균은 오르고, 특정 문항은 통과에서 실패로 뒤집힌다.** 그것이 D21 이 보여 줄 전부다.
#
# ★기록 — 처음 만든 candidate 는 "짧게 답하세요" 였다. 그때는 0.700 → 0.850 으로 오르고
# 회귀가 하나도 없어서(초록불) 시연이 성립하지 않았다. 슬라이드를 고치지 않고 candidate 를 바꿨다.
SYS_TERSE = SYS_BASE + (
    "\n- low 의 예: 공지, 안내, 알림, 투표 결과, 사내 소식처럼 읽어 두기만 하면 되는 메일."
    "\n- 제목이나 본문에 '공지'·'안내'·'알림'이 있으면 low 로 분류하세요."
)

VARIANTS = {"base": SYS_BASE, "terse": SYS_TERSE}


def rel(p: Path) -> str:
    """보기 좋은 상대 경로. 리포 밖을 가리키면 절대 경로 그대로 돌려준다."""
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def load_cases() -> list[dict]:
    return [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_emails() -> dict[int, dict]:
    return {e["id"]: e for e in json.loads(EMAILS.read_text(encoding="utf-8"))}


def answer_all(cases: list[dict], variant: str) -> dict[str, str]:
    """각 문항에 대한 답변 문자열을 만든다. case_id → answer."""
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    load_dotenv(ROOT / ".env")          # 노트북은 0절에서 하지만 스크립트는 스스로 해야 한다
    llm = ChatOpenAI(model=MODEL, temperature=0)
    emails = load_emails()
    out = {}
    for i, case in enumerate(cases, 1):
        e = emails[case["email_id"]]
        prompt = f"제목: {e['subject']}\n본문: {e['body'][:900]}\n\n질문: {case['question']}"
        try:
            out[case["case_id"]] = llm.invoke(
                [("system", VARIANTS[variant]), ("human", prompt)]
            ).content
        except Exception as err:                      # 실패도 결과다 — 빈 문자열로 남긴다
            out[case["case_id"]] = ""
            print(f"  ! {case['case_id']} 호출 실패: {err}", file=sys.stderr)
        print(f"\r  {i}/{len(cases)}", end="", flush=True)
    print()
    return out


# ── 채점 ─────────────────────────────────────────────────────────────

REFUSAL_MARKERS = ("모르겠", "알 수 없", "확인할 수 없", "나와 있지 않", "언급되어 있지 않",
                   "포함되어 있지 않", "정보가 없", "근거가 없")


def score(case: dict, answer: str) -> dict[str, bool | None]:
    """한 문항을 채점한다. **잴 수 없는 지표는 0이 아니라 None 이다.**

    이 함수가 이 파일에서 가장 중요하다. 반환값에 False 와 None 이 섞여 있고,
    둘의 차이가 D20 의 전부다 — False 는 "틀렸다", None 은 "이 문항으로는 잴 수 없다".
    """
    body = (answer or "").strip()
    refused = any(m in body for m in REFUSAL_MARKERS)

    return {
        # route: 정답 라벨과 대조. 다른 kind 에서는 잴 수 없다.
        "route": (case["expected"] in body.lower()) if case["kind"] == "route" else None,
        # facts: 본문에 있던 값이 답변에 살아남았는가. 하나라도 빠지면 False.
        "facts": (all(f in body for f in case["answer_facts"])
                  if case["kind"] == "extract" else None),
        # refusal: 답이 없는 문항에서 모른다고 했는가.
        #          ★ trap 이 아닌 문항에서 거절했다면 그건 refusal 지표가 아니라 route/facts 의 실패다.
        "refusal": refused if case["kind"] == "trap" else None,
    }


def aggregate(rows: list[dict]) -> dict[str, dict]:
    """지표별 집계. **분모는 '잰 문항 수'이지 전체 문항 수가 아니다.**"""
    out = {}
    for name in METRICS:
        vals = [r["scores"][name] for r in rows if r["scores"][name] is not None]
        out[name] = {
            "measured": len(vals),
            "passed": sum(1 for v in vals if v),
            "score": round(sum(1 for v in vals if v) / len(vals), 4) if vals else None,
        }
    return out


# ── 스냅숏 ───────────────────────────────────────────────────────────

def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def evalset_sha256() -> str:
    """평가셋의 지문. 이것이 다르면 두 스냅숏은 비교 대상이 아니다."""
    return hashlib.sha256(GOLDEN.read_bytes()).hexdigest()[:16]


def make_snapshot(rows: list[dict], variant: str, subset: int | None) -> dict:
    return {
        "schema": SCHEMA,
        "git_sha": git_sha(),
        "evalset_sha256": evalset_sha256(),
        "model": MODEL,
        "variant": variant,
        "subset": subset,               # 부분 실행이면 정수. 게이트가 이걸 보고 거부한다.
        "n_cases": len(rows),
        "summary": aggregate(rows),
        "rows": rows,
    }


def comparable(old: dict, new: dict) -> list[str]:
    """못 견주는 이유를 목록으로 돌려준다. 비어 있으면 견줄 수 있다."""
    problems = []
    if old.get("evalset_sha256") != new.get("evalset_sha256"):
        problems.append(
            "평가셋이 서로 다릅니다. 문항이 바뀐 두 결과를 견주면 그 차이는 모델이 아니라 "
            "문항의 차이입니다.")
    if old.get("model") != new.get("model"):
        problems.append(f"모델이 다릅니다({old.get('model')} vs {new.get('model')}).")
    if old.get("subset") or new.get("subset"):
        problems.append(
            "부분 실행 스냅숏이 섞여 있습니다. 몇 문항만 돌려 놓고 '회귀 없음'이라고 "
            "말하는 것은 자기기만입니다.")
    return problems


# ── 게이트 ───────────────────────────────────────────────────────────

def load_thresholds() -> dict:
    return json.loads(THRESHOLDS.read_text(encoding="utf-8"))["absolute"]


def gate(old: dict, new: dict) -> tuple[int, list[str]]:
    """종료코드와 사람이 읽을 줄들을 돌려준다.

    0 = 초록불(통과) · 1 = 빨간불(하한 미달 또는 문항 회귀) · 2 = 노란불(견줄 수 없음)
    """
    lines = []

    problems = comparable(old, new)
    if problems:
        return 2, ["⚠️  견줄 수 없습니다 — 게이트를 통과시키지 않습니다."] + [f"   - {p}" for p in problems]

    failed = False
    thresholds = load_thresholds()

    # ① 절대 하한. **미측정은 통과가 아니라 실패다.**
    lines.append("① 절대 하한")
    for name, floor in thresholds.items():
        got = new["summary"][name]["score"]
        if got is None:
            lines.append(f"   ✗ {name}: 측정되지 않음 — 하한 {floor} 미달로 셉니다(fail-closed)")
            failed = True
        else:
            ok = got >= floor
            failed |= not ok
            lines.append(f"   {'✓' if ok else '✗'} {name}: {got:.3f} (하한 {floor})")

    # ② 평균 변화 — 참고용으로만 보여 준다. 판정은 여기서 하지 않는다.
    lines.append("② 평균 변화 (참고)")
    for name in METRICS:
        o, n = old["summary"][name]["score"], new["summary"][name]["score"]
        if o is None or n is None:
            lines.append(f"   - {name}: 비교 불가")
        else:
            d = n - o
            lines.append(f"   - {name}: {o:.3f} → {n:.3f} ({d:+.3f})")

    # ③ 문항별 회귀. **평균이 올라도 여기서 막힌다.** 조인은 case_id 로 한다.
    old_rows = {r["case_id"]: r for r in old["rows"]}
    regressed = []
    for r in new["rows"]:
        prev = old_rows.get(r["case_id"])
        if prev is None:
            continue
        for name in METRICS:
            was, now = prev["scores"][name], r["scores"][name]
            if was is True and now is not True:
                regressed.append((r["case_id"], name, now))

    lines.append("③ 문항별 회귀")
    if regressed:
        failed = True
        for cid, name, now in regressed:
            state = "측정 안 됨" if now is None else "실패"
            lines.append(f"   ✗ {cid} · {name}: 통과 → {state}")
    else:
        lines.append("   ✓ 통과에서 실패로 뒤집힌 문항 없음")

    return (1 if failed else 0), lines


# ── CLI ──────────────────────────────────────────────────────────────

def cmd_run(args) -> int:
    cases = load_cases()
    if args.subset:
        cases = cases[: args.subset]

    if args.dry:
        # LLM 없이 골든셋 무결성만 본다. trap 문항이 None 을 내는지가 핵심.
        rows = [{"case_id": c["case_id"], "kind": c["kind"],
                 "scores": score(c, "")} for c in cases]
        n_none = sum(1 for r in rows for v in r["scores"].values() if v is None)
        print(f"문항 {len(rows)}개 로드 · None 칸 {n_none}개")
        for kind in ("route", "extract", "trap"):
            sample = next(r for r in rows if r["kind"] == kind)
            print(f"  {kind:8} 예시 {sample['case_id']}: {sample['scores']}")
        return 0

    print(f"평가 실행 · variant={args.variant} · {len(cases)}문항")
    answers = answer_all(cases, args.variant)
    rows = [{"case_id": c["case_id"], "kind": c["kind"],
             "answer": answers[c["case_id"]][:300],
             "scores": score(c, answers[c["case_id"]])} for c in cases]

    snap = make_snapshot(rows, args.variant, args.subset)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")

    for name, agg in snap["summary"].items():
        s = "측정 안 됨" if agg["score"] is None else f"{agg['score']:.3f}"
        print(f"  {name:8} {s}  ({agg['passed']}/{agg['measured']} 측정)")
    print(f"기록: {rel(out)}")
    return 0


def cmd_gate(args) -> int:
    old = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    new = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    codenum, lines = gate(old, new)
    print("\n".join(lines))
    verdict = {0: "🟢 초록불 — 통과", 1: "🔴 빨간불 — 막습니다", 2: "🟡 노란불 — 견줄 수 없습니다"}
    print(f"\n{verdict[codenum]}  (종료코드 {codenum})")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "generated_by": "scripts/eval.py gate",
            "baseline": Path(args.baseline).name, "candidate": Path(args.candidate).name,
            "exit_code": codenum, "verdict": verdict[codenum], "lines": lines,
            "summary_baseline": old["summary"], "summary_candidate": new["summary"],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"기록: {rel(Path(args.out))}")
    return codenum


def main() -> int:
    ap = argparse.ArgumentParser(description="평가 러너 · 스냅숏 · 게이트")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="골든셋을 돌려 스냅숏을 만든다")
    r.add_argument("--variant", choices=sorted(VARIANTS), default="base")
    r.add_argument("--out", default="measurements/eval_snapshot_baseline.json")
    r.add_argument("--subset", type=int, help="앞에서 N문항만(게이트가 거부한다)")
    r.add_argument("--dry", action="store_true", help="LLM 없이 골든셋 무결성만 확인")
    r.set_defaults(func=cmd_run)

    g = sub.add_parser("gate", help="두 스냅숏을 견주고 통과/차단을 판정한다")
    g.add_argument("--baseline", required=True)
    g.add_argument("--candidate", required=True)
    g.add_argument("--out", default="measurements/eval_gate.json")
    g.set_defaults(func=cmd_gate)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
