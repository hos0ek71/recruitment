#!/usr/bin/env python3
"""PreToolUse hook: CLAUDE.md의 AI 오케스트레이션 규칙을 기계적으로 강제한다.

- 하위 에이전트는 Orca codex 워커(gpt-6.1-sol, effort medium)로만 띄운다.
- Claude 서브에이전트(Agent/Task)와 Workflow 도구는 막는다.
- `orca orchestration worker-start`는 --agent codex --model gpt-6.1-sol --effort medium 이 모두 있어야 한다.
  (--terminal 로 이미 띄운 워커 터미널을 재사용할 때는 모델 플래그를 줄 수 없으므로 통과시킨다.)
"""
import json
import re
import sys

WORKER_AGENT = "codex"
WORKER_MODEL = "gpt-6.1-sol"
WORKER_EFFORT = "medium"
WORKER_FLAGS = f"--agent {WORKER_AGENT} --model {WORKER_MODEL} --effort {WORKER_EFFORT}"


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    sys.exit(0)


def has_flag(command: str, flag: str, value: str) -> bool:
    return re.search(rf"{flag}(?:\s+|=)['\"]?{re.escape(value)}['\"]?(?=\s|$)", command) is not None


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if tool in ("Agent", "Task", "Workflow"):
        deny(
            "이 프로젝트의 하위 에이전트는 Claude 서브에이전트가 아니라 Orca codex 워커"
            f"({WORKER_MODEL}, effort {WORKER_EFFORT})로만 띄운다. "
            f"`orca orchestration worker-start --spec ... --worktree current {WORKER_FLAGS} --json`을 쓴다 (CLAUDE.md 참고)."
        )

    if tool == "Bash":
        command = tool_input.get("command", "")
        if not re.search(r"\borchestration\s+worker-start\b", command):
            sys.exit(0)
        if re.search(r"--terminal(?:\s|=)", command):
            sys.exit(0)
        missing = [
            f"{flag} {value}"
            for flag, value in (("--agent", WORKER_AGENT), ("--model", WORKER_MODEL), ("--effort", WORKER_EFFORT))
            if not has_flag(command, flag, value)
        ]
        if missing:
            deny(
                "worker-start는 워커 모델 규칙을 지켜야 한다: "
                f"`{WORKER_FLAGS}`가 필요하다 (빠진 것: {', '.join(missing)}). CLAUDE.md 참고."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
