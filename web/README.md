# 웹 프론트엔드

React + TypeScript + Vite 기반의 최소 앱이다. 현재 제목과 결과 / 조건 승인 / 실행 기록 메뉴 자리만 표시한다.

## 실행

저장소 루트에서 실행한다. pnpm 10.x를 사용하며, 검증 환경은 Node 25.3.0 / pnpm 10.34.5다.

```sh
pnpm -C web install --frozen-lockfile
pnpm -C web dev
```

API 기본 주소는 `src/config.ts`의 `API_BASE_URL`을 사용한다. `import.meta.env.VITE_API_BASE_URL`에서 읽고 미설정 시 `/api`를 쓴다. 값은 Vite 실행 또는 빌드 시 환경변수로 전달한다. 현재 앱은 API를 호출하지 않는다.

개발 서버는 `/api` 요청을 `http://127.0.0.1:8000`으로 보내며 `/api` 접두사를 제거한다. 예를 들어 `/api/runs`는 백엔드의 `/runs`에 전달된다. 개발 프록시는 배포 빌드와 preview 서버에는 적용되지 않는다.

```sh
pnpm -C web lint
pnpm -C web typecheck
pnpm -C web test
pnpm -C web build
pnpm -C web preview
```

프록시 설정은 [Vite 공식 문서](https://vite.dev/config/server-options#server-proxy)를 따른다.

## H-0b 검증 기록 (2026-10-17)

- 테스트를 먼저 작성하고 App 모듈이 없는 상태에서 `pnpm -C web test` 실행: 종료 코드 1, `Failed to resolve import "./App"`.
- 빈 App 스텁으로 같은 명령 실행: 종료 코드 1, `Tests 1 failed (1)`, 제목 `공채 모아보기`를 찾지 못함. 빈 테스트 묶음이 아니라 렌더링 검증이 실제 실행되었음을 확인했다.
- 구현 후 아래 전체 명령 실행: 종료 코드 0, lint 및 타입 검사 성공, `Tests 1 passed (1)`, Vite 빌드 `16 modules transformed` / `built in 513ms`.

```sh
pnpm -C web install --frozen-lockfile && pnpm -C web lint && pnpm -C web typecheck && pnpm -C web test && pnpm -C web build
```

- App 테스트 제목 기대값을 `의도적으로 틀린 제목`으로 바꾸고 `pnpm -C web test` 실행: 종료 코드 1, `Tests 1 failed (1)`, 해당 제목을 찾지 못함.
- 올바른 기대값으로 원복하고 `pnpm -C web test` 실행: 종료 코드 0, `Tests 1 passed (1)`.
- 최초 의존성 설치에서 TypeScript 7과 typescript-eslint의 peer 범위 충돌 경고가 나와 TypeScript 5.9.3으로 맞췄다. 이후 설치는 충돌 경고 없이 통과했다.

생성 파일:

- `package.json`, `pnpm-lock.yaml`
- `index.html`, `vite.config.ts`, `eslint.config.js`
- `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`
- `src/App.tsx`, `src/App.test.tsx`, `src/main.tsx`, `src/index.css`
- `src/config.ts`, `src/vite-env.d.ts`, `src/test/setup.ts`
- `README.md`

작업 범위는 `web/**`다. 남은 프론트엔드 툴체인 문제는 없으며, 다음은 코디네이터의 루트 `make check` 통합 검증이다.
