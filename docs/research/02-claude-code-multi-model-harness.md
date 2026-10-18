# Claude Code·Codex CLI 다중 모델 하네스 조사

조사일: 2026-10-17 · 대상: `/Users/juhoseok/Desktop/recruitment`

공식 문서의 현재 동작과 프로젝트 제안을 구분했다. 문서와 설치 버전이 다르면 설치 버전의 도움말을 우선 확인해야 한다. 이 조사에서는 설정 변경, 워커 실행, 커밋을 하지 않았다. 문서에 나온 모델 식별자는 확인했지만 이 머신 계정에서 실제 호출 가능한지는 **확인 못 함**.

## 1. Claude Code 하네스 구성요소

### CLAUDE.md: 지속 지침

- 조직 관리 지침, 사용자 `~/.claude/CLAUDE.md`, 프로젝트 `CLAUDE.md` 또는 `.claude/CLAUDE.md`, 개인 `CLAUDE.local.md`를 구분한다.
- 시작 디렉터리와 상위 디렉터리 지침은 루트부터 이어 붙인다. 하위 디렉터리 지침은 해당 디렉터리 파일을 읽거나 수정할 때 추가된다. 모순된 지침을 자동으로 일관되게 해결한다고 가정하지 않는다.
- 각 파일은 **200줄 미만 권장**이며 강제 길이 제한이라는 뜻은 아니다. 실행·검증 명령, 아키텍처 제약, 코드 규약을 구체적으로 적고 오래된 규칙은 제거한다.
- `@path/to/file`은 실제 임포트다. 상대 경로는 임포트를 적은 파일 기준이며 절대 경로도 가능하다. 재귀 임포트는 최대 네 단계이고 코드 블록·인라인 코드 안에서는 확장하지 않는다.
- 임포트된 내용도 시작 컨텍스트를 차지하므로 파일 분리 자체가 토큰 절감은 아니다. 경로별 규칙은 `.claude/rules/`, 필요할 때 쓰는 절차는 스킬로 옮긴다.

출처: [How Claude remembers your project](https://code.claude.com/docs/en/memory).

### .claude/settings.json: 권한과 실행 설정

프로젝트 공유 설정은 `.claude/settings.json`, 개인 예외는 `.claude/settings.local.json`, 사용자 공통 설정은 `~/.claude/settings.json`이다. 로컬 설정이 공유 설정 위에 적용되지만 관리 정책의 제한은 별도로 적용된다. [Settings files and precedence](https://code.claude.com/docs/en/settings).

`permissions.allow`는 승인 없이 허용할 호출, `deny`는 차단할 호출, `ask`는 물어볼 호출이다. 평가 순서는 **deny → ask → allow**다. 자연어 지침은 행동 유도이며 권한 설정을 대체하지 않는다. Bash 규칙은 OS 샌드박스가 아니고 외부 프로세스 전체를 통제하는 방화벽도 아니다. [Configure permissions](https://code.claude.com/docs/en/permissions).

다음은 형식 설명용 예시이며 현재 저장소에 적용하지 않았다. `npm test`도 프로젝트에서 확인한 검증 명령이 아니라 예시다.

```json
{
  "permissions": {
    "allow": ["Bash(git diff *)", "Bash(npm test)"],
    "deny": ["Read(./.env)", "Bash(git push *)"]
  },
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "printf 'Bash 호출 전 점검\\n' >&2"}]
    }],
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{"type": "command", "command": "printf '파일 수정 완료\\n' >&2"}]
    }],
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "요청한 산출물과 검증 증거가 모두 있는지 평가하라. $ARGUMENTS"
      }]
    }]
  }
}
```

| 주요 이벤트 | 시점·용도 |
| --- | --- |
| `SessionStart` | 시작·재개 시 컨텍스트 준비 |
| `UserPromptSubmit` | 사용자 프롬프트 제출 시 검사 |
| `PreToolUse` | 도구 실행 전 검사·허용/거절 결정 |
| `PostToolUse` / `PostToolUseFailure` | 성공 후 처리 / 실패 관찰 |
| `PermissionRequest` | 권한 요청 처리 |
| `SubagentStart` / `SubagentStop` | Claude 내부 서브에이전트 수명주기 |
| `Stop` | 주 에이전트가 응답을 끝내려 할 때 검증 |
| `PreCompact` / `SessionEnd` | 압축 전 / 세션 종료 처리 |

커맨드 훅은 stdin으로 이벤트 JSON을 받는다. `PreToolUse`는 실행을 막을 수 있지만 `PostToolUse`는 이미 수행된 작업을 되돌리지 않는다. `Stop`에서 계속 진행을 요구한다면 `stop_hook_active`를 확인해 반복을 방지한다. 위 두 커맨드 훅은 메시지만 출력하며 검증을 강제하지 않는다. 실제 게이트는 검증 스크립트와 이벤트별 반환 규약으로 구현해야 한다. 출처: [Hooks reference](https://code.claude.com/docs/en/hooks), [Automate actions with hooks](https://code.claude.com/docs/en/hooks-guide).

### 서브에이전트: .claude/agents/*.md

프로젝트 정의는 `.claude/agents/`, 사용자 정의는 `~/.claude/agents/`에 둔다. Markdown 본문은 역할 지침이며 YAML frontmatter에 `name`, `description`, `tools`, `model` 등을 둔다.

```markdown
---
name: integration-reviewer
description: 구현 결과를 읽고 수용 조건과 회귀 위험을 검토한다.
tools: Read, Grep, Glob
model: inherit
---
작업 명세와 diff를 대조하고 누락·회귀를 근거와 함께 보고한다.
```

`model`은 `inherit`, Claude 모델 별칭 또는 전체 ID(예: `claude-opus-5-5`)를 받는다. 현재 문서는 호출별 model → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → 주 세션 모델 순서를 설명한다. v2.1.251 이전에는 환경변수 우선순위가 달랐다. **여기에 `gpt-6.1-sol`을 적어 Codex CLI를 실행하는 기능은 확인 못 함**. 이 프로젝트의 Codex 워커는 별도 Orca 프로세스로 시작한다. [Create custom subagents](https://code.claude.com/docs/en/sub-agents).

### 스킬과 슬래시 커맨드

- `.claude/skills/<name>/SKILL.md`: `name`, `description`과 절차를 정의한다. 관련 상황에서 Claude가 선택하거나 사용자가 `/name`으로 호출한다.
- 수동 실행 전용 절차는 `disable-model-invocation: true`를 쓸 수 있다. 스크립트·참고 파일을 같은 디렉터리에 포함할 수 있다.
- 사용자 스킬은 `~/.claude/skills/`에 둔다. 스킬은 매번 필요한 규칙보다 반복 작업 절차에 적합하다.
- 현재 문서는 사용자 커맨드를 스킬에 통합했다고 설명한다. `.claude/commands/review.md`와 `.claude/skills/review/SKILL.md` 모두 `/review`를 만들며 기존 커맨드는 계속 지원한다. 신규 절차는 스킬 형태를 권장한다.
- `/init`, `/memory`, `/permissions` 같은 내장 커맨드와 프로젝트가 만드는 사용자 커맨드를 구분한다.

출처: [Extend Claude with skills](https://code.claude.com/docs/en/skills).

프로젝트 상위 모델은 다음처럼 명시할 수 있다. Opus 5.5의 문서상 기본 effort는 medium이므로 high를 명시한다. 실제 계정·배포 모델 허용 목록은 별도 확인 대상이다.

```sh
claude --model claude-opus-5-5 --effort high
```

출처: [Model configuration](https://code.claude.com/docs/en/model-config).

## 2. Codex CLI 하네스와 공통 규칙 공유

### AGENTS.md 탐색과 우선순위

1. 전역 `$CODEX_HOME`(기본 `~/.codex`)에서 `AGENTS.override.md`, 없으면 `AGENTS.md` 중 첫 비어 있지 않은 파일을 읽는다.
2. 프로젝트 루트(통상 Git 루트)부터 현재 작업 디렉터리까지 내려가며 각 디렉터리를 검사한다. 루트를 찾지 못하면 현재 디렉터리만 검사한다.
3. 각 디렉터리에서 `AGENTS.override.md` → `AGENTS.md` → `project_doc_fallback_filenames` 순서로 **최대 한 파일**을 채택한다.
4. 루트에서 하위 순으로 결합하므로 현재 디렉터리에 가까운 지침이 앞선 지침보다 우선한다. 전역 지침 위에 프로젝트 지침이 이어진다.
5. 결합 크기는 `project_doc_max_bytes`로 제한하며 기본은 **32 KiB**다. 세션 시작 시 구성하므로 변경 후 새 세션에서 확인한다. 루트에서 실행하면 모든 하위 지침을 시작 시 재귀 수집하는 것은 아니다.

출처: [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

### Codex가 CLAUDE.md를 읽는가?

**기본 지침 자동 탐색 대상으로는 읽지 않는다.** 공식 문서는 위 이름과 설정된 fallback 이외의 이름은 지침 탐색에서 무시한다고 명시한다. 따라서 `CLAUDE.md`만 두고 Codex가 자동 적용한다고 기대하면 안 된다. 도구로 파일을 직접 읽게 하는 것과 자동 지침 탐색은 별개다. [Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

사용자 설정에서 다음처럼 fallback에 추가하면, 같은 디렉터리에 우선 지침 파일이 없는 경우 읽게 할 수 있다. AGENTS.md와 CLAUDE.md를 둘 다 합쳐 읽는 설정은 아니다.

```toml
project_doc_fallback_filenames = ["CLAUDE.md"]
```

**프로젝트 권장:** 공통 규칙의 원본을 루트 `AGENTS.md`로 두고 `CLAUDE.md`를 다음처럼 만든다.

```markdown
@AGENTS.md

## Claude 오케스트레이터
계획·작업 분할·통합 검증을 맡는다.
Codex 구현 워커는 Orca orchestration으로 시작한다.
```

Claude의 `@` 임포트 문법을 Codex도 해석한다고 가정하지 않는다. Codex는 공통 원본을 직접 발견하고, Claude는 임포트로 읽는다. Claude 전용 문서는 AGENTS.md 안에서 임포트하지 않는다.

대안은 **`CLAUDE.md -> AGENTS.md` 심볼릭 링크**다. Claude 전용 내용을 덧붙일 필요가 없을 때 적합하지만 플랫폼·체크아웃의 링크 지원을 확인하고 원본 AGENTS.md를 편집한다. 이 조사에서는 링크도 만들지 않았다.

버전 주의: 현재 Claude 문서는 **v2.1.277 이상에서**, 상위·현재 디렉터리에 CLAUDE.md/CLAUDE.local.md가 없으면 AGENTS.md를 직접 읽는다고 설명한다. 조건·플러그인 상태가 있고 Claude는 Codex의 `AGENTS.override.md`를 같은 방식으로 처리하지 않으므로, 이 프로젝트는 명시적 임포트를 유지하는 편이 예측 가능하다. 임포트·심볼릭 링크 공유 모두 [Claude 공식 메모리 문서](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools)에 나온다.

### config.toml: 모델·프로필·권한·검색

사용자 기본값은 `~/.codex/config.toml`, 신뢰한 프로젝트의 공유 기본값은 `.codex/config.toml`이다. 일반 설정 우선순위는 CLI → 프로젝트(가까운 디렉터리 우선) → 선택한 프로필 → 사용자 → 클라우드 기본값 → 시스템 → 내장 기본값이다. 관리 requirements의 제한은 이 기본값 계층과 별도다. [Config basics](https://developers.openai.com/codex/config-basic).

```toml
model = "gpt-6.1-sol"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"
approval_policy = "on-request"
web_search = "cached"
```

- `model`은 계정에서 사용 가능한 식별자여야 한다. effort 값의 지원 범위도 모델·클라이언트에 따라 다르다. 위 모델은 현재 공식 예시에 있으나 로컬 호출 성공은 확인 못 함.
- 샌드박스는 실행 가능 범위, 승인은 언제 허락을 받을지다. `read-only`, `workspace-write`, `danger-full-access`를 구분한다. `never` 승인 정책이 샌드박스 해제를 의미하지 않는다.
- 승인 정책은 `on-request`와 `never`의 동작을 구분해야 한다. 현행 공식 문서는 `untrusted` 승인 정책을 더 이상 지원하지 않는다고 명시하므로 오래된 예시를 복사하지 않는다.
- 검색 모드는 `cached`(일반 로컬 기본), `indexed`, `live`, `disabled`다. `--search`는 live 검색이며 full-access 설정에서는 검색 기본값이 live가 될 수 있다. 검색 설정은 셸의 네트워크 권한과 별개다.

출처: [Configuration Reference](https://developers.openai.com/codex/config-reference), [Config basics](https://developers.openai.com/codex/config-basic).

**프로필 버전 변화:** Codex 0.134.0 이상은 사용자 config 옆의 별도 파일을 사용한다. 예를 들어 `~/.codex/recruitment-worker.config.toml`에 위 모델·effort 등 차이만 적고 `codex --profile recruitment-worker`로 선택한다. 과거의 `[profiles.recruitment-worker]` 테이블과 최상위 `profile` 선택자는 해당 버전부터 지원하지 않는다. 설치된 Codex 버전은 이 조사에서 확인 못 함. [Advanced Config — Profiles](https://learn.chatgpt.com/docs/config-file/config-advanced#profiles).

## 3. 오케스트레이터–워커 다중 모델 운영 패턴

### 1차 출처에서 확인한 원칙

Anthropic Research 시스템은 리드가 전략을 세우고 병렬 서브에이전트가 탐색 결과를 반환하는 구조다. 위임 시 **목표·출력 형식·도구/출처·경계**를 명시해야 중복·누락이 줄어든다. 코딩처럼 의존성이 강한 작업은 연구보다 병렬화 여지가 작고 비용도 증가한다. 이 글은 다른 모델 조합을 다루므로 Opus 5.5 + GPT-6.1 Sol 조합의 성능 근거로 확대 해석하지 않는다. [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system).

OpenAI 문서는 주 에이전트에 요구사항·결정·최종 결과를 남기고 탐색·테스트 로그는 별도 에이전트에서 처리한 후 요약을 반환하도록 권한다. 병렬 쓰기는 충돌과 조정 비용이 있으므로 읽기 중심 작업부터 분리하는 접근을 제시한다. [Subagents](https://developers.openai.com/codex/multi-agent).

### 이 프로젝트 적용안: 문서 원칙을 운영 규약으로 구체화한 제안

| 단계 | 상위 Claude Code / Opus 5.5 high | Orca의 Codex / gpt-6.1-sol medium |
| --- | --- | --- |
| 계획 | 사용자 의도·모호함 확인, 인터페이스·수용 조건 결정 | 지정 범위 탐색, 필요한 질문 보고 |
| 구현 | 파일 소유권·의존 작업 순서 지정 | 기능은 실패 테스트 먼저 작성 후 구현 |
| 검증 | diff·실제 실행 증거 대조, 통합·회귀 확인 | 테스트 명령·결과·미실행 항목 보고 |
| 완료 | 수용 조건 충족 판단, 남은 위험 보고 | 성공/실패와 산출물 위치를 명시 |

본 세션의 사용자 규칙인 **모호하면 질문**, **기능 코드 요청 시 테스트 먼저**는 공통 AGENTS.md에 둔다. 워커 질문은 로컬 사용자 프롬프트가 아니라 코디네이터가 받을 수 있는 Orca ask 경로로 보낸다.

작업 명세는 Orca 가이드의 다섯 항목을 기본으로 하고 결정된 인터페이스와 실행 위치를 덧붙인다.

```text
Target: 저장소·작업 디렉터리·기준 revision·대상 기능
Change: 구체적인 입력→출력 변화와 기대 산출물
Constraints: 호환성·금지 변경·관련 규칙과 참조 문서
Ownership: 수정 가능한 파일 목록, 공유 파일 담당자
Observable acceptance: 실패 테스트→구현→통과할 명령과 기대 결과
Context: 상위 결정·API 계약·선행 산출물·알려진 실패
Report: 변경 파일·검증 증거·미해결점·질문 경로
```

- **파일 소유권:** 한 파일의 쓰기 담당자는 한 워커로 제한한다. 공통 스키마·락파일·설정은 상위나 전담 통합 담당자가 수정한다. 필요하면 별도 worktree로 분리하고 통합 책임자를 지정한다.
- **검증 게이트:** 워커의 완료 선언만으로 통합하지 않는다. 명세·diff·테스트 실행 결과를 확인하고, 의존 작업을 합친 뒤 통합 검증을 수행한다. 실제 미실행 테스트는 통과로 기록하지 않는다.
- **컨텍스트 인계:** 전체 대화 대신 승인된 결정, 경로, 인터페이스, 수용 조건과 증거 위치를 전달한다. 새 워커가 이전 워커의 대화를 알고 있다고 가정하지 않는다.
- **실패 처리:** 명세 불명확·권한 문제·검증 실패를 분류해 상위로 보고한다. 재시도는 Task를 유지하고 새 Dispatch를 구분한다. 연락 두절만으로 실패 확정·중복 편집 워커 실행을 하지 않는다.
- **비용 관리:** 고난도 설계·판정은 상위에 두되 워커에 판단 가능한 범위를 준다. 모든 작업을 병렬화하지 말고 독립적인 조사·테스트·파일 단위 구현부터 분리한다.

## 4. 로컬 Orca CLI 사실 확인

직접 읽은 출력: `orca --version` → **1.4.219**, `orca orchestration worker-start --help`, `orca skills get orchestration`. 웹 자료가 아닌 이 머신의 CLI 출력이다. 연구 확인을 위해 run-create나 worker-start는 실행하지 않았다. 본 작업의 이미 배정된 Dispatch에 대한 check·최종 보고는 작업 수명주기 처리로 별도 수행한다.

### 모델·effort를 지정하는 정확한 형식

다음은 **실행하지 않은 명령 예시**다. `--task` 값은 실제 생성된 Task ID로 바꿔야 한다.

```sh
orca orchestration worker-start \
  --task '<실제-task-id>' \
  --worktree current \
  --agent codex \
  --model gpt-6.1-sol \
  --effort medium \
  --json
```

새 Task와 Dispatch를 함께 만들려면 `--task` 대신 `--spec '<자기완결적 작업 명세>'`를 사용한다. 실행 전 Run 바인딩 등 운영 전제는 해당 코디네이터가 확인해야 한다.

- `--agent codex`는 해당 worker server에서 활성화된 Orca agent ID를 선택한다.
- `--model`은 provider 모델 ID, `--effort`는 그 모델의 reasoning effort이며 **effort는 model을 요구**한다.
- 둘 다 기존 터미널을 재사용하는 `--terminal`과 함께 쓸 수 없다. 따라서 이 형식은 새 agent launch용이다.
- current·기존 worktree는 setup을 다시 실행하지 않는다. current에서 여러 워커를 띄우면 파일 공간을 공유하므로 소유권 규칙이 필요하다.
- 성공 종료코드 0은 ready일 때뿐이다. 실패/상태 불명은 receipt의 stage·잔여 리소스·복구 명령을 확인하며 즉시 중복 실행하지 않는다.
- 도움말은 provider ID의 문법을 허용한다는 근거이며 계정의 모델 접근·실제 실행 성공 증거는 아니다.

### worker_done 보고 규약

로컬 가이드와 이번 Dispatch preamble 기준:

1. 배정된 terminal handle, Task ID, Dispatch ID를 그대로 사용한다. 늦게 온 이전 시도의 보고가 현재 작업을 완료시키지 않도록 둘 다 전달한다.
2. **정확히 한 번**, `--outcome succeeded` 또는 `failed`를 명시하고 body를 **수행·발견·남은 일의 3문장**으로 쓴다.
3. 변경 파일이 있으면 `--files-modified`, 영속 보고서가 있으면 `--report-path`에 실제 값을 넣는다.
4. 자연스러운 체크포인트와 완료 직전 `check --terminal ... --json`으로 후속 지시를 읽는다. 이번 preamble은 활동 중 5분마다 heartbeat를 요구한다.
5. 질문은 `ask`로 전달하고 timeout이면 같은 메시지 ID로 재개한다. worker_done 후에는 추가 작업·폴링을 멈춘다.
6. 코디네이터는 활성 Dispatch와 증거를 검증하고 재사용·보존·release 중 하나를 결정한다. 유효한 worker_done은 Task·Dispatch를 자동 정산하므로 별도의 완료 상태 갱신은 필요하지 않다.

가이드의 핵심 구분: **Run은 조정 네임스페이스, Task는 작업, Dispatch는 권위 있는 한 번의 시도**다. 전송 성공은 durable enqueue이며 수신자가 읽고 수용했다는 뜻은 아니다.

## 5. 프로젝트 권장 파일 배치

아래는 제안이며 이 조사에서 실제 만든 것은 본 리포트 하나뿐이다.

| 경로 | 둘 내용·책임 |
| --- | --- |
| `/AGENTS.md` | 공통 규칙 원본: 모호함 질문, 테스트 우선, 실행·검증 명령, 금지 범위, 파일 소유권·보고 규약 |
| `/CLAUDE.md` | 첫 줄 `@AGENTS.md`; Claude의 계획·분할·통합 책임과 Orca 운영 문서 참조 |
| `/.claude/settings.json` | 공유 permissions·hooks; 모델/effort를 저장한다면 팀 합의 값 사용 |
| `/.claude/settings.local.json` | 개인 승인·환경 예외; 버전관리 제외 |
| `/.claude/agents/integration-reviewer.md` | Claude 내부 읽기 전용 검토 역할과 Claude model 선택; Codex 실행 설정과 구분 |
| `/.claude/skills/dispatch-worker/SKILL.md` | Orca 버전 가이드 읽기, 명세 작성, 완료·실패 처리 절차; 수동 호출 전용 고려 |
| `/.claude/commands/` | 기존 커맨드 호환 용도; 새 절차는 skills에 우선 배치 |
| `/.codex/config.toml` | 신뢰된 프로젝트용 Codex model·effort·sandbox·web_search 기본값 |
| `~/.codex/recruitment-worker.config.toml` | 현재 Codex 프로필 형식의 개인 실행 차이; 저장소 밖에서 관리 |
| `/하위모듈/AGENTS.md` | 모듈별 공통 규칙; Codex의 시작 디렉터리와 Claude의 하위 로딩 차이 확인 |
| `/docs/architecture/` | API 계약·데이터 모델·상위 의사결정 근거 |
| `/docs/tasks/` | 워커별 명세·소유권·수용 조건·인계 기록; 반복 시작 시 참조 |
| `/docs/research/` | 날짜·버전·출처를 붙인 조사 자료; 항상 전부 임포트하지 않음 |

모델·effort의 최종 실행 값은 Orca 시작 receipt와 agent 상태에서 확인한다. 문서와 설정 파일에 값이 있다는 것만으로 실제 활성 모델이 보장되지는 않는다.

## 6. 출처 목록

모든 웹 출처는 2026-10-17 열람한 1차 출처다. OpenAI 문서 도구는 일부 developers.openai.com 경로의 내용을 learn.chatgpt.com 문서로 안내했으며, 프로필 변경은 반환된 현행 문서에 따른다.

| 제목 | URL |
| --- | --- |
| How Claude remembers your project | https://code.claude.com/docs/en/memory |
| Settings files and precedence | https://code.claude.com/docs/en/settings |
| Configure permissions | https://code.claude.com/docs/en/permissions |
| Hooks reference | https://code.claude.com/docs/en/hooks |
| Automate actions with hooks | https://code.claude.com/docs/en/hooks-guide |
| Create custom subagents | https://code.claude.com/docs/en/sub-agents |
| Extend Claude with skills | https://code.claude.com/docs/en/skills |
| Model configuration | https://code.claude.com/docs/en/model-config |
| How we built our multi-agent research system | https://www.anthropic.com/engineering/multi-agent-research-system |
| Custom instructions with AGENTS.md | https://developers.openai.com/codex/guides/agents-md |
| Config basics | https://developers.openai.com/codex/config-basic |
| Configuration Reference | https://developers.openai.com/codex/config-reference |
| Advanced Config — Profiles | https://learn.chatgpt.com/docs/config-file/config-advanced#profiles |
| Subagents | https://developers.openai.com/codex/multi-agent |

로컬 1차 출처: Orca CLI 1.4.219의 `worker-start --help`, `skills get orchestration` 출력 및 이 작업의 Dispatch preamble. 공개 문서 URL은 **확인 못 함**.
