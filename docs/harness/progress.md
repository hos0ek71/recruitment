# 진행 기록

세션마다 맨 위에 항목을 추가한다. 다음 세션이 이 파일과 `features.json`, `git log`만 보고 이어갈 수 있게 쓴다.

형식: 날짜 · 작업자 / 한 일 / 검증 증거 / 남은 문제 / 다음 할 일

---

## 2026-10-22 (2) · C-3 완료

**한 일**
- Run `run_47434bb74ea0`, 워커 1명(`codex / gpt-6.1-sol / medium`). 사람인 수정 공고 재수집(updated_min, sort=ua)과 원본 버전 보관(사용자 결정: 덮어쓰기 대신 버전).
- 워커 질문 2건 처리: upsert 반환은 명시적 `UpsertResult`, updated 워터마크가 여러 날 deferred 때 전진하지 않도록 초기화 규칙(A안).
- 결정: 같은 화면 회사 조사 자동화 승인(mvp-design-review 0-3), 기업기본정보·DART 키 사용자 신청.

**검증 증거**
- 코디네이터 재실행 `make check` 종료 코드 0: 백엔드 220개, mypy 24개 파일, 웹 1개. sort 값과 read-cnt·apply-cnt를 사람인 공식 명세에서 직접 확인.

**남은 위험**
- upsert가 공고마다 쿼리 3번(삽입 시도, 잠금 조회, 버전 번호)이라 페이지당 최대 330쿼리. 1인용 규모에선 문제없지만 느려지면 배치로 바꾼다.
- 실제 API의 updated_min 반응 범위는 G-1에서 확인.

## 2026-10-22 · 계획: 회사 분석과 자기소개서 맞춤 수정

**한 일**
- Run `run_79b1bad9846a`, 워커 2명(`codex / gpt-6.1-sol / medium` 확인). 회사 정보 출처 조사 `docs/research/10`, 자소서 수정 설계 조사 `docs/research/11`, 종합 계획 `docs/plans/2026-10-22-company-analysis-cover-letter.md`.
- 결론: 단계 5(K-0~K-7, G-5)로 MVP 이후 권장. 자동 회사 정보는 금융위원회 기업기본정보 + DART(공시 회사), 빈칸은 사용자 사실 메모. 뉴스 API는 약관상 AI 입력 불가로 제외.

**다음 할 일**
- 사용자 결정 6개(계획 문서 8절). 승인 전에는 features.json에 넣지 않는다.

## 2026-10-20 · 잡코리아 데이터 아이디어 회의

**한 일**
- Run `run_36789a239f5e`, 워커 3명. 사용자가 이 회의에 한해 Claude Sonnet 5.5 high를 지정했다. 정책 훅이 막고, 훅에 일회 예외를 넣는 수정은 Claude Code 자동 권한 검사(Self-Modification)가 막아 훅은 원상 복구했다. 사용자가 `! bash scratchpad/start-jk-meeting.sh`로 직접 시작했고 영수증 `launch.effective`는 3명 모두 `claude / claude-sonnet-5-5 / high`.
- 산출물 `docs/ideation/2026-10-20-jobkorea-data/00~04`. 결론: 잡코리아 허락 경로 0개(Open API 약관 제5조가 개인·프로젝트·개인 사용·DB 수집 거절, 코디네이터 원문 확인). 다음 수는 사람인 키 발급 후 커버리지 실험.

**배운 점**
- 사용자가 지정한 워커 모델이 정책 훅과 다르면 처음부터 한 줄로 알리고 바로 쓸 수 있는 방법(사용자 직접 실행)을 줄 것. 긴 설명은 사용자를 혼란스럽게 했다.

## 2026-10-19 · 결정: 모집 단위가 여러 개인 공고

**한 일**
- 사용자가 GPT로 공고를 고를 때 통합 공고(아이센스)가 판정 없이 빠진 사례를 분석했다. 원인은 건별 판정 장부가 없는 것과 공고 한 건을 판정 한 번으로만 다루는 것.
- 사용자 승인으로 `docs/mvp-design-review.md` 0-1절에 규칙 4개를 확정하고 features.json N-1, F-1 수용 기준에 넣었다. 코드 변경 없음.

**다음 할 일**
- 변동 없음: 사용자 키 신청 4건, 키를 기다리는 동안 C-3 updated_min 보완 가능.

**추가 (같은 날)**
- 완성 화면 시연 영상: `docs/demo/gongchae-demo.mp4`(90초, 예시 데이터), Artifact https://claude.ai/artifact/3KywqjZ5vx82cc4zgH1mXE
- dazzajo-portfolio 수집 방식 조사(Run `run_a783b832155a`, 워커 2명, 둘 다 `codex / gpt-6.1-sol / medium` 확인): `docs/research/05`, `06`, 종합 `07`. 비크롤링 부분은 네이버 공식 API뿐이고 제조사·다나와는 HTML 수집. 새 후보는 인크루트 공식 RSS(조건 문의 필요).
- 워커들의 `make check`는 Docker 데몬이 꺼져 있어 종료 코드 2. 문서만 바뀐 작업이라 영향 없음.
- 규칙 추가: 프롬프트마다 오케스트레이션 판단(CLAUDE.md, AGENTS.md 9번).
- 잡코리아 검색 체크리스트 검증(mvp-design-review 0-2): 파서 스파이크 `research/spikes/jobkorea-paste/`(unittest 16개, 코디네이터 재실행 통과), 보고서 `docs/research/08`. 1페이지 샘플에서 전체 109건·본 목록 40건·광고 3건·파견 1건 분리, 1페이지만 주면 "69건 부족, 2·3페이지 미입력". 공고 ID가 없어 건수 일치는 잠정 판정. 사용자 결정: 채택하지 않음(손작업 대비 가치 낮음).
- 부천대 조사 `docs/research/09`: JOB4U 공채달력은 잡코리아 공식 iframe(코디네이터가 HTML 직접 확인), 일반·추천채용 공개 목록 있음, RSS·메일 구독과 API 계약은 확인 못 함. 판정 "부분". 학교 문의 초안 포함. 사용자 결정: 문의하지 않음.

## 2026-10-18 · 아이디어 회의, 결정 반영, C-0

**한 일**
- 아이디어 회의(Run `run_e81e32c567ff`, 워커 4명): 문제 정의 → 기업 원천·공공 창구·제품 재정의 발산 → 레드팀 → 종합. `docs/ideation/2026-10-18-job-data-sources/`
- 사용자 결정: 지원 범위 민간 + 공공기관·지방공기업, 제품 약속 변경(승인한 경로 도착분 처리 + 독립 표본으로 누락 측정). 설계 문서 목표 1·데이터 소스, `docs/mvp-design-review.md` 0절, features.json(C-0, C-5~C-7, P-0) 갱신
- C-0: 키 없는 소스를 실행 오류로 기록해 매 실행이 partial이 되던 버그 수정(Run `run_87baf79db533`)

**검증 증거**
- C-0 후 `make check` 종료 코드 0: 백엔드 207개, mypy 24개 파일, 웹 1개

**배운 점**
- 회의에서 오케스트레이터의 직전 제안(관심 기업 공개 피드 주력)이 표본 20곳 0곳으로 뒤집혔다. 공채속보 API는 과소평가했었다. 근거 없이 방향을 제안하지 말고 작은 표본으로 먼저 확인할 것.
- `run-create` 후 이전 Run에 워커를 띄우려면 `run-use --id`로 다시 묶어야 한다(CLAUDE.md).

**다음 할 일**
1. 사용자: 신청 4건(사람인, 고용24 공채속보, 공공기관 채용정보 15125273, 지방공기업 15159757). 사람인 맞춤 공고 알림 켜 두기(선택).
2. 키가 나온 소스부터 C-5~C-7 어댑터와 게이트 1.

## 2026-10-17 (2) · 구현 웨이브 1~3 · Run `run_87baf79db533`

**한 일**
- 웨이브 1: H-0a 백엔드 툴체인·make check·테스트 DB·CI, H-0b 웹 툴체인
- 웨이브 2: H-1 구조 테스트, H-2 응답 픽스처, C-1 DB 스키마·저장소
- 웨이브 3: C-2 고용24 어댑터, C-3 사람인 어댑터
- 코디네이터 직접 수정: `backend/app/adapters/base.py`(어댑터 계약), 의존성 `sqlalchemy[asyncio]`과 `types-defusedxml` 추가, AGENTS.md 검증 명령, CLAUDE.md 함정·병렬 검증 규칙
- 웨이브 4: C-4 수집 엔진·/runs API. 코디네이터 코드 리뷰 후 같은 터미널에 후속 작업 1건(새 ID 없는 페이지 연속 2번이면 중단, 지원하지 않는 지역 코드 422)
- 코디네이터 직접 수정(웨이브 4): Settings에 SARAMIN_DAILY_BUDGET(400), WORK24_DAILY_BUDGET(1000) 추가, .env.example의 빈 TZ를 Asia/Seoul로

**검증 증거**
- 웨이브마다 코디네이터가 `make check`를 다시 실행했고 모두 종료 코드 0이었다. 최종: 백엔드 테스트 189개, mypy strict 24개 파일, 웹 1개.
- 구조 테스트에 일부러 위반을 넣어 실패하는 것을 확인했다.
- 모든 워커 시작 영수증의 `launch.effective`는 `codex / gpt-6.1-sol / medium`이었다.

**배운 점 (하네스에 반영함)**
- 같은 worktree에서 병렬 워커가 디렉터리 단위 ruff/mypy를 돌리면 서로의 작업 중 파일 때문에 실패한다. 명세의 수용 명령은 자기 파일 경로만 넣는다(CLAUDE.md 4번).
- 작업 도중 Orca 앱이 꺼졌다. `orca open`으로 다시 켠 뒤 `--retry-of`로 재시작했다(CLAUDE.md 알려진 함정).

**남은 문제**
- H-2 픽스처 14개 중 13개가 합성이다. 게이트 1에서 실제 응답으로 교체해야 한다.
- 고용24 한도 초과 응답 형식은 확인하지 못했다.
- C-2: 필터 통과 공고의 고용24 상세 보강은 F-1(2단계) 이후에 한다. C-3: 수정 감지용 updated_min은 아직 없다.
- 커밋: 브랜치 `stage1-harness`에 0cef994(하네스), 8901bc3(구현)을 push. GitHub Actions run 39035622228 success.

**기능 상태**: 통과 H-0, H-1, C-1, C-4 / 미통과 P-0(키), H-2(합성 픽스처), C-2(상세 보강), C-3(updated_min), G-1(게이트)

**다음 할 일**
1. 사용자: `stage1-harness`를 main에 합칠지 결정(PR 또는 병합).
2. 사용자: P-0 API 키 신청. 키가 나오면 G-1(실제 1회 수집)을 진행하고 합성 픽스처를 실제 응답으로 바꾼다.
3. 키를 기다리는 동안 할 수 있는 것: C-3 updated_min 보완. 2단계(N-1~F-2)는 게이트 규칙상 G-1 이후다.

## 2026-10-17 · 오케스트레이터(Opus 5.5) + Orca 워커 3개(codex gpt-6.1-sol medium)

**한 일**
- MVP 설계 문서를 분석하고 검증했다. 결과는 `docs/mvp-design-review.md`.
- Orca Run `run_dd278dce2ebd`에서 웹조사 워커 3개를 돌렸다.
  - A: 하네스 원칙 → `docs/research/01-harness-engineering-principles.md`
  - B: Claude·Codex 하네스 → `docs/research/02-claude-code-multi-model-harness.md`
  - C: 채용 API 사실 검증 → `docs/research/03-mvp-external-fact-check.md`
- 하네스를 깔았다.
  - `AGENTS.md`(공통 규칙 원본), `CLAUDE.md`(`@AGENTS.md` + 오케스트레이션 규칙)
  - `.claude/settings.json`(Opus 5.5 high 고정, 훅), `.claude/hooks/`(규칙 강제, 세션 브리핑)
  - `.codex/config.toml`(워커 기본값), `docs/harness/`(features.json, 이 파일, 명세 템플릿), `.gitignore`

**검증 증거**
- `orchestration_policy.py`: 샘플 입력 10개로 확인. 허용 5개(올바른 worker-start, `=` 형식, `--terminal` 재사용, 무관한 Bash, 깨진 JSON), 차단 5개(Agent, Workflow, 틀린 모델, claude 워커, 플래그 누락).
- `session_brief.py`: 실행 출력과 종료 코드 0 확인.
- `features.json`: JSON 파싱, ID 22개 중복 없음 확인.
- 워커 시작 영수증의 `launch.effective`가 모두 `codex / gpt-6.1-sol / medium`.
- 워커 리포트 3개는 수용 기준을 확인한 뒤 받아들였다. 핵심 주장은 공식 페이지에서 직접 다시 확인했다(사람인 500회·`code=4`·`sr=directhire`·`start` 0 기반, 고용24 기업회원 전용).

**워커 실행 중 생긴 일 (하네스에 반영함)**
- 첫 시작 3건이 Codex 업데이트 안내 때문에 `agent_readiness`에서 실패했다. 0.163.0 안내는 건너뛰고 `--retry-of`로 다시 시작했다.
- 워커 C 실행 중 Codex가 0.161.0에서 0.163.0으로 업데이트되어 셸 도구가 `Malformed Mach-o file`로 실패했다. 오케스트레이터가 실행한 업데이트는 아니다. `worker-stop` 후 다시 시작해 완료했다.
- 두 함정을 `CLAUDE.md`의 "알려진 함정"에 적었다.
- 워커 A 터미널은 사용자가 조작해서 `retained / user_takeover`로 남아 있다.

**남은 문제**
- `.claude/settings.json`의 모델·effort와 훅은 새 세션부터 확실히 적용된다. 새 세션에서 `/status`로 모델과 effort를 확인할 것.
- `.codex/config.toml`은 Codex가 이 프로젝트를 신뢰할 때만 적용된다. 워커는 `worker-start` 플래그로 모델이 정해지므로 동작에는 지장이 없다.
- 설계 검토의 "결정 필요" 항목을 사용자가 정해야 한다.

**사용자 결정 (2026-10-17)**
- D1~D7: 제안 기본값으로 확정 (`docs/mvp-design-review.md` 1절)
- 이번 구현 범위: 0단계(H-0~H-2) + 1단계 코드(C-1~C-4). 게이트 1 전까지만 한다.
- 툴체인: 확인 중

**다음 할 일**
1. **P-0 (사용자):** 사람인·고용24 Open API를 신청한다. 고용24는 기업회원 전용이라 개인 신청이 안 될 수 있다.
2. 사용자가 `docs/mvp-design-review.md`의 "사용자 결정 필요" 항목과 단계·게이트 구성을 확정한다.
3. H-0(툴체인과 단일 검증 진입점) 명세를 쓰고 워커에 배정한다. 도구 선택은 명세 전에 사용자에게 확인한다. P-0과 병렬로 진행할 수 있다.
