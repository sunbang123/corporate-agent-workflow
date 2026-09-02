# 개발 표준 가이드

본 문서는 개발팀의 효율적인 협업과 고품질 소프트웨어 개발을 위한 표준을 정의합니다. 모든 개발자는 이 가이드를 준수해야 합니다.

---

## 1. 코딩 컨벤션

### 1.1 공통 원칙
- **가독성 우선:** 코드는 다른 개발자가 쉽게 이해할 수 있어야 합니다.
- **일관성 유지:** 프로젝트 전체에서 동일한 스타일을 유지합니다.
- **자기 문서화:** 변수명, 함수명만으로 의도를 파악할 수 있게 작성합니다.

### 1.2 언어별 스타일 가이드

| 언어 | 스타일 가이드 | 린터/포매터 |
|------|--------------|------------|
| **Python** | PEP 8 | black, flake8, isort |
| **JavaScript/TypeScript** | Airbnb Style Guide | ESLint, Prettier |
| **Java** | Google Java Style | Checkstyle |
| **Go** | Effective Go | gofmt, golint |

### 1.3 네이밍 규칙

**변수 및 함수:**
```
- Python/JavaScript: snake_case (변수), camelCase (JS 함수)
- Java: camelCase
- 상수: UPPER_SNAKE_CASE
- 클래스: PascalCase
```

**파일 및 디렉토리:**
```
- 소스 파일: snake_case.py, kebab-case.ts
- 컴포넌트: PascalCase.tsx
- 테스트: test_module.py, module.test.ts
```

### 1.4 주석 작성 원칙
- **Why, not What:** 코드가 "왜" 그렇게 작성되었는지 설명
- **TODO/FIXME:** 추후 작업이 필요한 부분 명시
- **Docstring:** 모든 공개 API에는 문서화 필수

```python
# Good: 비즈니스 로직 설명
# 30일 이상 미접속 사용자는 휴면 처리 (개인정보보호법 준수)
if days_inactive >= 30:
    deactivate_user(user)

# Bad: 코드를 그대로 설명
# days_inactive가 30보다 크거나 같으면 deactivate_user 호출
```

---

## 2. Git 워크플로우

### 2.1 브랜치 전략 (Git Flow)

```
main (production)
  ↑
develop (staging)
  ↑
feature/[ticket-id]-[description]
bugfix/[ticket-id]-[description]
hotfix/[ticket-id]-[description]
release/v[version]
```

### 2.2 브랜치 명명 규칙

| 유형 | 형식 | 예시 |
|------|------|------|
| 기능 개발 | feature/PROJ-123-user-login | feature/SW-456-add-oauth |
| 버그 수정 | bugfix/PROJ-123-fix-null-error | bugfix/SW-789-fix-timeout |
| 긴급 수정 | hotfix/PROJ-123-critical-fix | hotfix/SW-001-security-patch |
| 릴리즈 | release/v1.2.0 | release/v2.0.0-beta |

### 2.3 커밋 메시지 규칙

**Conventional Commits 형식:**
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Type 종류:**
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅 (기능 변화 없음)
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 설정, 패키지 매니저 등

**예시:**
```
feat(auth): OAuth 2.0 로그인 기능 추가

- Google, Kakao OAuth 연동
- 토큰 갱신 로직 구현
- 로그인 페이지 UI 업데이트

Closes #456
```

### 2.4 PR(Pull Request) 규칙

**PR 제목 형식:**
```
[PROJ-123] 기능에 대한 간략한 설명
```

**PR 본문 필수 항목:**
- [ ] 변경 사항 요약
- [ ] 관련 이슈/티켓 링크
- [ ] 테스트 방법 및 결과
- [ ] 스크린샷 (UI 변경 시)
- [ ] 체크리스트 (lint, test, build 통과 여부)

---

## 3. 코드 리뷰

### 3.1 리뷰 원칙
- **48시간 내 응답:** 리뷰 요청 후 2영업일 내 최초 피드백
- **건설적 피드백:** 비판보다 개선 제안에 집중
- **질문 환영:** 이해되지 않는 부분은 적극적으로 질문

### 3.2 리뷰 체크리스트

**기능:**
- [ ] 요구사항을 정확히 구현했는가?
- [ ] 엣지 케이스를 처리했는가?
- [ ] 에러 핸들링이 적절한가?

**코드 품질:**
- [ ] 코딩 컨벤션을 준수했는가?
- [ ] 불필요한 코드/주석이 없는가?
- [ ] 중복 코드가 없는가?
- [ ] 함수/클래스가 단일 책임을 가지는가?

**보안:**
- [ ] SQL Injection 취약점이 없는가?
- [ ] XSS 취약점이 없는가?
- [ ] 민감 정보(비밀번호, API 키)가 하드코딩되지 않았는가?

**성능:**
- [ ] N+1 쿼리 문제가 없는가?
- [ ] 불필요한 API 호출이 없는가?
- [ ] 메모리 누수 가능성이 없는가?

### 3.3 리뷰 라벨

| 라벨 | 의미 | 대응 |
|------|------|------|
| `[Blocker]` | 반드시 수정 필요 | 수정 후 재리뷰 |
| `[Major]` | 강력히 권장하는 수정 | 토론 후 결정 |
| `[Minor]` | 개선 제안 | 선택적 반영 |
| `[Nit]` | 사소한 제안 | 선택적 반영 |
| `[Question]` | 이해를 위한 질문 | 답변 필요 |

---

## 4. 테스트

### 4.1 테스트 커버리지 기준

| 유형 | 최소 커버리지 | 목표 커버리지 |
|------|-------------|-------------|
| 단위 테스트 | 70% | 85% |
| 통합 테스트 | 50% | 70% |
| E2E 테스트 | 핵심 시나리오 100% | 주요 시나리오 |

### 4.2 테스트 작성 원칙

**AAA 패턴:**
```python
def test_user_login():
    # Arrange (준비)
    user = create_test_user(email="test@example.com")

    # Act (실행)
    result = login(email="test@example.com", password="password123")

    # Assert (검증)
    assert result.success is True
    assert result.user.id == user.id
```

### 4.3 테스트 명명 규칙
```
test_[대상]_[상황]_[예상결과]

예시:
- test_login_with_valid_credentials_returns_token
- test_create_user_with_duplicate_email_raises_error
```

---

## 5. 배포 절차

### 5.1 환경 구성

| 환경 | 용도 | 배포 방식 |
|------|------|----------|
| **local** | 개발자 로컬 | 수동 |
| **dev** | 개발/테스트 | PR 머지 시 자동 |
| **staging** | QA/UAT | release 브랜치 자동 |
| **production** | 실서비스 | main 머지 + 승인 |

### 5.2 배포 프로세스

```
개발 완료 → PR 생성 → 코드 리뷰 → CI 통과 → Staging 배포
    → QA 검증 → Production 승인 → Production 배포 → 모니터링
```

### 5.3 배포 체크리스트

**배포 전:**
- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료 및 승인
- [ ] 마이그레이션 스크립트 검토
- [ ] 환경 변수 확인
- [ ] 배포 공지 (슬랙 #deploy 채널)

**배포 후:**
- [ ] 헬스 체크 확인
- [ ] 핵심 기능 스모크 테스트
- [ ] 에러 모니터링 (Sentry, DataDog)
- [ ] 성능 메트릭 확인

### 5.4 롤백 절차

1. 문제 감지 시 즉시 PagerDuty 알림
2. 이전 버전으로 롤백 (1-Click Rollback)
3. 인시던트 채널 생성 및 팀 소집
4. 원인 분석 및 수정
5. 포스트모템 작성

---

## 6. 문서화

### 6.1 필수 문서

| 문서 | 위치 | 담당 |
|------|------|------|
| README.md | 프로젝트 루트 | 개발 리드 |
| API 명세서 | /docs/api | 백엔드 개발자 |
| 아키텍처 문서 | /docs/architecture | 아키텍트 |
| 배포 가이드 | /docs/deployment | DevOps |

### 6.2 API 문서화

- OpenAPI(Swagger) 3.0 표준 사용
- 모든 엔드포인트에 요청/응답 예시 포함
- 에러 코드 및 메시지 정의

---

## 7. 기술 부채 관리

### 7.1 기술 부채 등급

| 등급 | 기준 | 해결 기한 |
|------|------|----------|
| **Critical** | 보안 취약점, 시스템 불안정 | 즉시 |
| **High** | 성능 저하, 유지보수 어려움 | 1개월 내 |
| **Medium** | 코드 품질, 테스트 부족 | 분기 내 |
| **Low** | 개선 사항, 리팩토링 | 연간 계획 |

### 7.2 기술 부채 백로그
- Jira "Tech Debt" 보드에서 관리
- 스프린트당 20% 용량을 기술 부채 해소에 할당

---

> **문의처**
> 개발 표준 관련 문의는 개발팀 리드에게 연락하세요.
> - 이메일: dev-lead@company.com
> - Slack: #dev-standards

**최종 수정일:** 2026년 1월 31일

**발행처:** 개발팀

---
