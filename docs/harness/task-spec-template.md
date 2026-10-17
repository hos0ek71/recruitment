# 워커 작업 명세 템플릿

Orca `worker-start --spec`에 넣는 명세다. 워커는 이전 대화를 모른다. 명세만 읽고 끝까지 할 수 있게 쓴다.
명세 하나에는 기능(`features.json`의 ID) 하나만 담는다.

```text
[기능 ID] 한 줄 제목

Target: 저장소 경로, 기준 커밋, 대상 기능 ID와 관련 설계 문서 섹션
Change: 구체적인 입력 → 출력 변화와 만들 산출물
Constraints: 지켜야 할 불변식 (AGENTS.md "제품 불변식"과 "아키텍처 경계" 중 관련 항목),
             바꾸면 안 되는 인터페이스, 금지 사항 (실제 외부 API 호출 금지 등)
Ownership: 만들거나 고칠 수 있는 파일과 디렉터리 목록. 이 밖은 손대지 않는다.
           공유 파일(스키마, 락파일, 설정)의 담당자
Context: 이미 정해진 결정, API 계약, 앞선 작업의 산출물 경로, 알려진 실패
Observable acceptance: features.json acceptance를 그대로 옮긴다.
           실패 테스트 → 구현 → 통과를 보여 줄 명령과 기대 결과
           병렬 웨이브라면 자기 범위 명령으로 쓴다(전체 make check는 코디네이터가 웨이브 끝에 실행)
Report: worker_done 본문은 3문장(한 일, 발견한 것, 남은 일).
        --files-modified와 --report-path에는 실제 값만 넣는다.
        질문은 preamble의 ask 명령으로 한다.
```

## 코디네이터 체크리스트

- [ ] 동시에 도는 다른 워커와 Ownership이 겹치지 않는다
- [ ] 수용 기준이 관찰 가능한 명령과 결과로 적혀 있다
- [ ] 결정이 필요한 모호한 점은 명세 전에 사용자에게 물었다
- [ ] 시작 명령에 `--agent codex --model gpt-6.1-sol --effort medium`이 있다 (CLAUDE.md)
