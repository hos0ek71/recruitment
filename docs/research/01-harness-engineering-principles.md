# AI 코딩 에이전트를 위한 하네스 엔지니어링 원칙

조사일: 2026-10-17 · 대상: FastAPI + PostgreSQL + React/TypeScript 개인 프로젝트

필수 자료 4개와 추가 자료 3개, 총 **1차 출처 7개**의 본문을 직접 확인했다. 아래 12개 원칙은 출처의 실험·관점을 종합한 것이며, 3절의 도구·파일명·우선순위는 이 저장소를 위한 적용 제안이다. 제품 내부의 LLM 평가 파이프라인과, 그 제품을 개발하는 코딩 에이전트의 하네스는 구분한다.

## 1) 정의와 인접 개념

하네스 엔지니어링은 코딩 에이전트가 목표를 수행하고 결과를 검증·수정할 수 있도록 지침, 도구, 실행 흐름, 상태 인계와 피드백 체계를 설계하고 개선하는 일이다. 프롬프트 엔지니어링이 지시문의 작성·구성에 초점을 둔다면, 컨텍스트 엔지니어링은 매 추론 시점에 제공할 정보 전체를 선별·유지하는 일이다. 하네스는 그 정보를 전달하고 검사 결과에 따라 다음 행동을 유도하는 실행 환경까지 다룬다. 다만 용어 경계는 통일되지 않았으며, Böckeler는 코딩 에이전트 사용자의 하네스를 컨텍스트 엔지니어링의 한 형태로 설명하므로 세 개념을 서로 배타적인 발전 단계로 단정하면 안 된다. [Anthropic: 컨텍스트](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [LangChain](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering), [Böckeler](https://martinfowler.com/articles/harness-engineering.html)

## 2) 핵심 원칙 12개

### 원칙 1. 진입 지침은 백과사전이 아니라 지도다

- **설명:** 자주 읽는 지침에는 탐색 경로와 핵심 규칙을 둔다.
- **실천:** OpenAI는 짧은 `AGENTS.md`에서 상세 문서로 연결했다. `CLAUDE.md`에도 같은 원칙을 적용하되 규칙 원본을 중복 관리하지 않는다.
- **출처:** [OpenAI — We made repository knowledge the system of record](https://openai.com/index/harness-engineering/), [Anthropic — Context retrieval and agentic search](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### 원칙 2. 저장소 문서를 공식 기록으로 삼는다

- **설명:** 설계·결정·계획을 다음 세션에서도 발견할 수 있어야 한다.
- **실천:** 문서 색인과 결정 기록을 버전 관리한다. 오래된 설명과 깨진 링크를 점검한다.
- **출처:** [OpenAI — We made repository knowledge the system of record](https://openai.com/index/harness-engineering/)

### 원칙 3. 세션 간 인계는 명시적 산출물로 한다

- **설명:** 대화 압축만으로 장기 작업의 연속성을 보장할 수 없다.
- **실천:** 기능 목록에는 수용 절차와 통과 여부를, 진행 파일에는 완료 사항·실패·다음 작업을 남긴다. 재시작 시 기록과 코드 상태를 대조한다.
- **출처:** [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### 원칙 4. 한 번에 검증 가능한 작은 기능을 끝낸다

- **설명:** 전체 앱을 한 세션에 완성하려는 시도를 줄인다.
- **실천:** 기능 하나를 선택해 구현·검증·인계를 마친다. 기능 상태는 검증 후에만 갱신하며 요구사항을 삭제해서 완료시키지 않는다.
- **출처:** [Anthropic — Feature list / Incremental progress](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### 원칙 5. 규칙과 실행 가능한 센서를 짝짓는다

- **설명:** 문서 지침만으로 구조를 유지할 수 없다.
- **실천:** 계층 의존성과 경계 검증을 린터·구조 테스트로 강제하고, 오류에는 수정 방법을 담는다.
- **출처:** [OpenAI — Enforcing architecture and taste](https://openai.com/index/harness-engineering/), [Böckeler — Feedforward and Feedback](https://martinfowler.com/articles/harness-engineering.html)

### 원칙 6. 빠른 검증을 작업 루프 안으로 당긴다

- **설명:** 저렴한 결정적 검사를 자주 실행해 수정 비용을 낮춘다.
- **실천:** 린트·타입검사·빠른 테스트를 변경 직후 실행한다. 구현→검증→수정을 반복하고 종료 전 요구사항과 결과를 비교한다.
- **출처:** [Böckeler — Timing: Keep quality left](https://martinfowler.com/articles/harness-engineering.html), [LangChain — Build & Self-Verify](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering)

### 원칙 7. 필요한 맥락을 점진적으로 공개한다

- **설명:** 모든 자료를 처음부터 넣기보다 필요한 순간에 읽는다.
- **실천:** 파일 경로·색인·요약을 제공하고 상세 명세는 작업별로 탐색한다. 압축할 때 결정·미해결 문제를 보존하고 중복 로그를 덜어낸다.
- **출처:** [Anthropic — Context retrieval / Compaction](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### 원칙 8. 재현 가능한 환경과 실제 동작의 관측 수단을 준다

- **설명:** 코드를 읽는 것만으로 사용자의 경험을 검증할 수 없다.
- **실천:** 시작 스크립트, 브라우저 테스트, 조회 가능한 로그를 준비한다. 세션 시작 시 기본 동작부터 확인한다.
- **출처:** [Anthropic — Environment management / Testing](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), [OpenAI — Increasing application legibility](https://openai.com/index/harness-engineering/)

### 원칙 9. 엔트로피를 조금씩 계속 제거한다

- **설명:** 중복·잘못된 패턴이 후속 생성의 본보기가 되지 않게 한다.
- **실천:** 낡은 문서·죽은 코드·규칙 위반을 주기적으로 찾아 작은 수정으로 정리한다.
- **출처:** [OpenAI — Entropy and garbage collection](https://openai.com/index/harness-engineering/)

### 원칙 10. 사람의 판단을 영향력이 큰 지점에 둔다

- **설명:** 요구사항·연구·계획의 오해는 구현 전에 발견할수록 효과가 크다.
- **실천:** 불명확한 요구는 질문하고, 큰 변경은 조사·계획을 먼저 검토한다. 기능 수용 기준은 사람이 확인한다.
- **출처:** [HumanLayer — On Human Leverage](https://www.humanlayer.dev/blog/advanced-context-engineering), [Böckeler — The role of the human](https://martinfowler.com/articles/harness-engineering.html)

### 원칙 11. 반복 실패를 하네스 개선의 입력으로 쓴다

- **설명:** 같은 오류에 같은 재시도만 반복하지 않는다.
- **실천:** 실패 기록을 보고 지침·도구·검사를 보완한다. 반복 편집이 계속되면 접근을 재검토하고 회귀 여부도 확인한다.
- **출처:** [Hashimoto — Step 5: Engineer the Harness](https://mitchellh.com/writing/my-ai-adoption-journey), [LangChain — Trace analysis / Loop detection](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering)

### 원칙 12. 테스트 통과와 제품의 올바름을 구분한다

- **설명:** 잘못 이해한 요구로 만든 테스트는 함께 잘못될 수 있다.
- **실천:** 정상·경계 사례를 원래 명세와 비교하고, 주요 여정은 브라우저·수동 확인으로 보완한다. 커버리지만 완료 기준으로 삼지 않는다.
- **출처:** [Böckeler — Behaviour harness](https://martinfowler.com/articles/harness-engineering.html), [LangChain — Build & Self-Verify](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering)

## 3) 구현 전에 깔아야 할 체크리스트 14개

아래는 기존 「공채 모아보기 MVP 설계 문서.md」와 사용자 지침을 반영한 **프로젝트 적용 제안**이다. 특정 도구가 원문에서 권장되었다는 뜻은 아니며, 이 조사에서 실제 설치·설정·기능 구현은 하지 않았다. P0는 첫 제품 기능 전, P1은 첫 기능 구현을 시작할 때 바로 사용할 수 있게 준비할 항목이다.

1. [ ] **P0 · 작업 계약:** 루트 `AGENTS.md`에 “모호하면 질문”, “기능 테스트 먼저”, 변경 범위와 완료 증거 형식을 적는다. 완료 기준: 새 세션이 규칙과 문서 경로를 찾는다. 근거: 원칙 1·10 + 사용자 지침.
2. [ ] **P0 · 문서 지도:** 기존 설계서를 기준 문서로 연결하고, 아키텍처·실행법·테스트법·결정 기록의 위치를 정한다. 미확정 사항은 확정 정책과 구분한다. 완료 기준: 같은 정책의 상충하는 원본이 없다. 근거: 원칙 2·7.
3. [ ] **P0 · 수용 기준:** 기능별 ID·검증 절차·초기 미통과 상태를 기록한다. “승인된 조건만 수집”, “누락 정보는 확인 필요”, “불완전 수집을 숨기지 않음”을 우선 사례로 둔다. 완료 기준: 기능 상태를 관찰 가능한 결과로 판정할 수 있다. 근거: 원칙 3·12 + 기존 설계.
4. [ ] **P0 · 테스트 우선 절차:** pytest와 React 테스트 실행 경로를 준비한다. 각 기능은 실패 테스트→최소 구현→통과 확인 순서로 진행하고, 미구현 상태와 환경 오류를 구별한다. 완료 기준: 첫 기능의 실패를 재현할 명령이 있다. 근거: 원칙 6 + 사용자 지침.
5. [ ] **P0 · 개발 환경:** Python·Node·PostgreSQL 버전과 잠금 파일 정책, 환경변수 예시, 의존성 설치·시작 명령을 정한다. 키 값은 저장하지 않는다. 완료 기준: 새 체크아웃에서 문서만 보고 부팅 가능하다. 근거: 원칙 8 + 기존 설계.
6. [ ] **P0 · 격리된 DB:** PostgreSQL 테스트 DB의 생성·마이그레이션·초기화 명령을 준비한다. 데이터 삭제 명령은 운영 DB를 대상으로 실행되지 않게 한다. 완료 기준: 동일 초기 상태에서 통합검증을 반복할 수 있다. 근거: 원칙 5·8의 적용.
7. [ ] **P0 · 경계 계약:** FastAPI 라우터→서비스→저장소 방향, 외부 API·LLM 어댑터 경계를 문서화한다. DB 접근 위치·역방향 import 같은 핵심 규칙만 구조 검사로 옮긴다. 완료 기준: 의도적인 위반이 탐지된다. 근거: 원칙 5의 적용.
8. [ ] **P0 · 빠른 로컬 검증:** Python은 Ruff·타입검사기·pytest, 웹은 ESLint·TypeScript 검사·테스트를 후보로 정하고 단일 검증 진입점을 준비한다. 완료 기준: 오류 시 종료 코드가 실패하며 수정할 파일을 알 수 있다. 근거: 원칙 6의 적용.
9. [ ] **P0 · CI와 완료 계약:** 로컬과 같은 검증을 CI에서 실행하고 제품 기능 통과 여부와 구분해 기록한다. 빈 테스트 묶음이나 실행하지 않은 검사를 성공 증거로 쓰지 않는다. 완료 기준: 새 변경에서 검증 결과가 남는다. 근거: 원칙 6·12의 적용.
10. [ ] **P1 · 외부 입력 픽스처:** 공식 샘플 또는 비식별 응답으로 매퍼·페이지 순회·오류 응답·LLM JSON 계약의 테스트 자료를 준비한다. 실 API 키 없이 기본 회귀검증이 가능해야 한다. 완료 기준: 정상·누락·잘못된 형식을 재현한다. 근거: 원칙 8·12 + 기존 설계.
11. [ ] **P1 · 핵심 여정의 관측:** 개발용 로그에 실행·쿼리 식별자와 실패 단계를 남길 형식을 정하고, 브라우저 스모크 테스트 경로를 준비한다. 완료 기준: 조건 승인→실행 기록→결과의 증거를 남길 수 있다. 제품 기능 완성 전에는 픽스처로 검증 경로를 준비한다. 근거: 원칙 8의 적용.
12. [ ] **P1 · 세션 인계:** 진행 파일에 선택한 기능·변경 파일·실행 명령과 결과·남은 실패·다음 행동을 남기는 양식을 둔다. 완료 기준: 새 세션이 전체 대화 없이 재개한다. 근거: 원칙 3·4.
13. [ ] **P1 · 사람의 게이트:** 요구·API 계약 미확정, 데이터 삭제·스키마의 비호환 변경, 유료 호출 확대, 배포에 대한 판단 기준을 미리 적는다. 제품의 “수집 조건 승인”과 개발 작업의 승인 절차는 별도다. 완료 기준: 질문해야 할 상황과 재량 범위가 드러난다. 근거: 원칙 10의 적용이며 출처의 공통 의무 규칙은 아니다.
14. [ ] **P1 · 개선·청소 루프:** 반복 실패·문서 불일치·중복 코드를 짧게 기록하고 정기 검토한다. 하네스 변경 후 대표 작업의 오류·소요시간·비용을 비교한다. 완료 기준: 재발한 문제 하나가 지침 또는 검사로 연결된다. 근거: 원칙 9·11.

이 목록은 대규모 오케스트레이터나 다중 에이전트 도입을 선행 조건으로 삼지 않는다. Hashimoto의 사례도 한 번에 에이전트 하나를 활용하며, 작은 프로젝트에서는 실제 실패에 대응하는 도구부터 추가하는 편이 적절하다. [Hashimoto](https://mitchellh.com/writing/my-ai-adoption-journey)

## 4) 안티패턴 5개

1. **거대한 지침 파일과 중복 정책:** 탐색과 갱신을 어렵게 한다. 짧은 진입 문서에서 상세 원본으로 연결한다. [OpenAI](https://openai.com/index/harness-engineering/)
2. **전체 앱을 한 번에 맡기고 대화 기억에 의존:** 미완료 상태와 조기 완료 선언을 부른다. 기능 목록·진행 기록을 남기고 작은 단위로 마친다. [Anthropic: 장기 작업](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
3. **초록색 테스트만으로 요구 충족을 선언:** 잘못된 요구 해석은 테스트에도 반영된다. 사람이 수용 사례를 확인한다. [Böckeler](https://martinfowler.com/articles/harness-engineering.html)
4. **실패한 접근을 무한 재시도:** 원인·도구 부족·계획 오류를 검토하지 않으면 루프가 지속된다. 실행 기록으로 실패 유형을 분류한다. [LangChain](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering)
5. **팀 실험을 보편 규칙으로 복사:** OpenAI의 최소 병합 게이트나 HumanLayer의 컨텍스트 사용률 40~60%는 환경별 사례다. 사람 판단을 없애거나 고정 비율을 강제할 근거로 삼지 않는다. [OpenAI](https://openai.com/index/harness-engineering/), [HumanLayer](https://www.humanlayer.dev/blog/advanced-context-engineering)

**확인 한계:** 보편적인 최적 지침 길이·검증 시간·컨텍스트 비율·하네스 투자량은 확인 못 함. 이 스택의 특정 도구 조합이 최적이라는 비교 실험도 확인 못 함. 기존 설계에 적힌 채용 API 한도·승인 조건·최신 응답 계약은 이번 조사에서 검증하지 않았다. 장기 유지보수성과 완전 자율화의 일반적 보장도 확인 못 함.

## 5) 출처 목록

모두 작성자 또는 실험 수행 조직이 직접 공개한 1차 자료다. 날짜는 본문에 표시된 게시일이며, 모두 2026-10-17 열람했다. 재인용·검색 요약을 최종 근거로 사용하지 않았고 직접 인용 없이 요약했다.

| ID | 제목 / 작성자·조직 | 게시일 | URL |
| --- | --- | --- | --- |
| S1 · 필수 | Harness engineering: leveraging Codex in an agent-first world / Ryan Lopopolo, OpenAI | 2026-02-11 | https://openai.com/index/harness-engineering/ |
| S2 · 필수 | Harness engineering for coding agent users / Birgitta Böckeler, Martin Fowler 사이트 | 2026-04-02 | https://martinfowler.com/articles/harness-engineering.html |
| S3 · 필수 | Effective harnesses for long-running agents / Anthropic | 2025-11-26 | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |
| S4 · 필수 | Effective context engineering for AI agents / Anthropic Applied AI 팀 | 2025-09-29 | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| S5 · 추가 | Advanced Context Engineering for Coding Agents / Dex, HumanLayer | 2025-08-29 | https://www.humanlayer.dev/blog/advanced-context-engineering |
| S6 · 추가 | Improving Deep Agents with harness engineering / Vivek Trivedy, LangChain | 2026-02-17 | https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering |
| S7 · 추가 | My AI Adoption Journey / Mitchell Hashimoto | 2026-02-05 | https://mitchellh.com/writing/my-ai-adoption-journey |

S2의 변경 이력에는 초기 메모가 2026-02-17, 정식 확장 글이 2026-04-02로 표시된다. 현재 URL은 확장 글을 제공하므로 본문 제목·날짜를 기준으로 삼았다. S6의 `blog.langchain.com` 주소는 위 `www.langchain.com/blog/…` 주소로 리디렉션된다.
