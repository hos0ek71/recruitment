#!/usr/bin/env python3
"""SessionStart hook: 세션을 시작할 때 하네스 상태를 짧게 컨텍스트에 넣는다.

출력은 Claude 컨텍스트에 추가된다. 어떤 오류가 나도 세션 시작을 막지 않는다.
"""
import json
import os
import sys
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))


def main() -> None:
    lines = ["[하네스] 최상위=Opus 5.5 high, 워커=Orca codex gpt-6.1-sol medium (CLAUDE.md)."]
    try:
        data = json.loads((root / "docs/harness/features.json").read_text(encoding="utf-8"))
        features = data.get("features", [])
        done = sum(1 for f in features if f.get("passes"))
        lines.append(f"[하네스] 기능 {done}/{len(features)}개 통과.")
        pending = [f for f in features if not f.get("passes")]
        if pending:
            nxt = pending[0]
            lines.append(f"[하네스] 다음 미통과 기능: {nxt['id']} {nxt['title']} (단계 {nxt['stage']}).")
    except Exception as exc:  # noqa: BLE001 - 세션 시작을 막지 않는다
        lines.append(f"[하네스] features.json을 읽지 못함: {exc}")
    lines.append("[하네스] 작업 전에 docs/harness/progress.md 최신 항목을 읽는다.")
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit(0)
