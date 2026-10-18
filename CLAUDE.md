@AGENTS.md

# Claude Code 전용: 최상위 오케스트레이터 규칙

## AI 오케스트레이션 규칙 (필수)

| 역할 | 실행 주체 | 모델 | effort |
| --- | --- | --- | --- |
| 최상위 에이전트 (오케스트레이터) | Claude Code | Opus 5.5 (`claude-opus-5-5`) | `high` |
| 하위 에이전트 (워커) | Orca가 띄운 Codex CLI | GPT-6.1 Sol (`gpt-6.1-sol`) | `medium` |

- 하위 에이전트는 Orca 오케스트레이션으로만 띄운다. 모든 새 워커는 아래 형식을 지킨다.
  ```
  orca orchestration worker-start --spec "<명세>" --worktree current --agent codex --model gpt-6.1-sol --effort medium --json
  ```
  기존 Task를 다시 시도할 때는 `--spec` 대신 `--task <id> --retry-of <dispatch_id>`를 쓰고 나머지 플래그는 같다.
- Claude 서브에이전트(Agent/Task 도구)와 Workflow 도구는 쓰지 않는다. 다른 에이전트, 모델, effort로 워커를 띄우지 않는다.
- 시작 영수증의 `launch.effective`가 `codex / gpt-6.1-sol / medium`인지 확인한다. 요청 인자만 보고 모델을 주장하지 않는다.
- 이 규칙은 아래 세 곳에서 강제한다. 규칙을 바꿀 때는 이 표와 세 곳을 함께 고친다.
  - `.claude/settings.json`: 최상위 모델과 effort 고정. 사용자 전역 설정의 Opus 5.5 `xhigh`를 덮어쓴다.
  - `.claude/hooks/orchestration_policy.py`: Agent/Task/Workflow 호출과, 플래그가 틀린 `worker-start`를 차단한다.
  - `.codex/config.toml`: 워커 기본 모델과 effort. 신뢰된 프로젝트에서만 적용되므로 `worker-start` 플래그가 1차 기준이다.

## 역할 분담

- **최상위:** 요구 해석, 사용자 질문, 작업 분할, 명세 작성, 워커 결과 검증, 통합, `features.json`과 `progress.md` 갱신, 게이트 승인 요청.
- **워커:** 명세 하나만 구현·테스트·조사하고 `worker_done`으로 보고한다.
- 구현 코드는 워커가 쓴다. 최상위는 하네스 문서·설정과, 통합에 필요한 작은 수정만 직접 한다.

## 오케스트레이션 절차

1. **세션 시작:** `docs/harness/progress.md`의 최신 항목, `features.json`의 다음 미통과 기능, `git log -5`를 확인한다.
2. **가이드 로드:** `orca skills get orchestration`. 버전에 맞는 이 가이드가 Orca 명령의 기준이다.
3. **실행:** `run-create` 후, 서로 독립인 작업은 한 웨이브로 모두 시작하고 나서 `check --wait`로 기다린다. 실제 순서가 있는 작업만 `task-create --deps`로 묶는다.
4. **명세:** `docs/harness/task-spec-template.md` 형식을 쓴다. 같은 worktree에서 동시에 도는 워커끼리 Ownership 파일이 겹치면 안 된다. 겹치면 deps로 순서를 정하거나 worktree를 나눈다. 공통 파일(스키마, 락파일, 설정)의 담당은 하나만 둔다.
   같은 worktree에서 병렬로 도는 워커의 수용 기준은 자기 파일 경로만 넣은 명령으로 쓴다. ruff check, ruff format --check, mypy, pytest 모두 해당한다. 예: `uv run mypy app/adapters/saramin.py`. 디렉터리 전체나 인자 없는 `mypy`는 다른 워커 파일까지 검사한다. 다른 워커가 아직 고치고 있는 파일 때문에 전체 `make check`가 깨질 수 있기 때문이다. 전체 `make check`는 웨이브가 끝난 뒤 코디네이터가 실행한다.
5. **수용:** `worker_done`을 받으면 보고 파일과 diff를 읽고 수용 명령을 직접 다시 실행한다. 통과했을 때만 받아들이고, 그다음 release·retain·재사용 중 하나를 정한 뒤 ack한다.
6. **실패:** 영수증의 `failedStage`와 `recovery`를 따른다. 같은 명령을 그대로 다시 실행하지 않는다.
7. **세션 종료:** `progress.md`에 기록을 남기고, 증거가 있는 기능만 `features.json`에 반영한다.

## 알려진 함정

- **Codex 업데이트 안내:** 안내 화면이 뜨면 워커가 `agent_readiness`에서 `Agent startup blocked: agent-update-prompt`로 실패한다. 순서는 이렇다.
  1. `orca terminal read --terminal <handle> --screen`으로 화면을 확인한다.
  2. 사용자에게 업데이트 여부를 묻거나 해당 버전을 건너뛴다.
  3. 실패한 디스패치를 `worker-release`로 정리한다.
  4. `--task <id> --retry-of <dispatch_id>`로 다시 시작한다.
- **실행 중 Codex 업데이트:** 워커가 도는 동안 Codex CLI를 업데이트하면 바이너리가 교체되는 도중이라 워커 셸 도구가 `Malformed Mach-o file`로 실패한다. 업데이트는 워커가 없을 때만 한다. 이미 실패했으면 마지막 턴에 `worker_done`이 없는지 확인한 뒤 `worker-stop` 후 `--retry-of`로 재시작한다.
- **Orca 앱 종료:** 작업 도중 Orca 앱이 꺼지면 `worker-start`가 `runtime_unavailable` 또는 `terminal_handle_stale`로 실패한다. `orca open --json`으로 다시 켜고 `orca status`가 `ready`인지 확인한다. Run과 Task는 보존된다. 실패한 디스패치는 `worker-release`로 정리한 뒤 `--retry-of`로 다시 시작한다. 이후 명령에는 `--run <run_id>`를 명시한다.
- **Run 바인딩:** `run-create`를 하면 코디네이터 터미널이 새 Run에 묶인다. 이전 Run에 워커를 더 띄우려면 `orca orchestration run-use --id <run_id>`로 다시 묶는다. 묶이지 않은 Run에 명령하면 `consumer_fenced`로 거부된다(상태 변화 없음).
- **사용자 개입:** `worker-release`가 `retained / user_takeover`를 돌려주면 사용자가 그 터미널을 쓰는 중이다. 닫지 않는다.

## 사용자 승인이 필요한 일

- 단계 게이트(`G-*`) 통과 판정
- 설계 문서와 다른 결정, `docs/mvp-design-review.md`의 미정 사항 확정
- 실제 외부 API 호출(사람인 한도 소모)과 유료 LLM 호출 확대
- DB 스키마의 비호환 변경, 데이터 삭제, 배포, git push
