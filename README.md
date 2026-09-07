# Codex Self Harness

자신의 실행 경험과 오픈소스 연구로 코드를 개선하는 Codex 조직입니다.
지휘자 → 연구·고도화 팀장 → 전문 팀원이 육하원칙 JSON으로 협업합니다.
판단은 독립 Codex 세션이, 수집·저장·스케줄링·검증·배포는 Python 스크립트가 처리합니다.

첫 실제 자기 개선은 [PR #1](https://github.com/trevi00/codex-harness/pull/1)입니다.
팀원이 Redis Streams 정리를 구현하고, 팀장·지휘자가 각각 실제 Codex로 검수했습니다.
기존 평가 기준의 통합 테스트와 Docker 안의 실제 Codex 파일 작업 카나리아를 통과한 커밋을 병합·반영했습니다.
`harness demo`는 별도의 고정 fixture이며 이 실제 검증과 구분합니다.

## 실행

필요: Python 3.12+, uv, Docker Desktop, 로그인된 Codex CLI 및 GitHub CLI.

```powershell
uv sync --frozen
uv run python scripts/setup.py
docker compose up -d --wait postgres redis
uv run harness init-db
uv run harness doctor
docker compose --profile agents build conductor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start_supervisor.ps1 -InstallStartup
uv run harness status
```

`.env`의 `HARNESS_GITHUB_REPO=owner/repository`가 PR 대상입니다.
DB와 Redis는 localhost의 55432, 56379 포트를 사용합니다. 인증·실행 기록은 Git에 넣지 않습니다.
Windows 호스트 `.venv`와 컨테이너 `/repository/.venv`는 별도 볼륨으로 분리합니다.
supervisor는 호스트에서 실행되며 에이전트에 Docker 소켓을 노출하지 않습니다.
`-InstallStartup`은 현재 사용자의 로그인 시 supervisor를 시작하도록 등록합니다.

## 자동 운영

GitHub Trending·GeekNews를 6시간마다 수집합니다. 팀원은 한 토픽을 선택하고 연구 팀장과 지휘자가
출처·기존 그래프·Google SRE·arc42 관점에서 검토합니다. 승인된 토픽은 고도화 팀장 계획,
독립 구현 checkout, 팀장 검수, 지휘자 검수, PR·카나리아·병합 순서로 진행됩니다.
main이 바뀌면 자동 rebase 작업을 만들고 새 커밋을 다시 심사합니다.

```powershell
uv run harness research github
uv run harness research geeknews
uv run harness improve "개선 목표" --acceptance "측정 가능한 완료 조건"
uv run harness inspect tasks
uv run harness inspect releases
```

동시에 실행하는 Codex 작업은 최대 2개입니다. 같은 원인·범위의 독립 사건이 두 번 확인되면
실행 가능한 필수 훅 작업을 만듭니다. 재발하면 같은 훅을 개선하며 새 검증이 끝날 때까지 이전 버전을 유지합니다.
재시도·재작업·RLM 호출에는 예산이 있고, 차단·실패·정체·취소를 성공으로 기록하지 않습니다.

Codex App Server의 현재 컨텍스트 사용량이 70%에 도달하면 진행 중인 도구가 끝나는 지점에서
작업·그래프·출처·도구 결과를 저장하고 새 세션에 인계합니다. 오래된 실행의 저장은 lease와 generation으로 거부합니다.
1시간 동안 일이 없는 에이전트 컨테이너는 종료하고, supervisor가 메시지나 영속 작업을 발견하면 다시 기동합니다.

## 컨텍스트와 SSOT

Git은 조직·정책·스키마·코드 정의의 SSOT이고 PostgreSQL은 작업·사건·검수·세션·배포 사실의 SSOT입니다.
GraphRAG는 이 사실에서 파생합니다. Tree-sitter Python 심볼·import·보수적인 호출 관계와 조직·작업 그래프를 색인합니다.
다국어 로컬 ONNX 임베딩, pgvector, 키워드 검색과 그래프 확장을 함께 사용합니다.

```powershell
uv run harness index .
uv run harness project-graph
uv run harness embed --limit 200
uv run harness query "세션 인계" --semantic
uv run harness context "세션 인계" --budget 12000
uv run harness rlm sha256:ARTIFACT_HASH "자료에서 확인할 질문" --max-calls 8
uv run harness cleanup
```

큰 자료는 내용 주소로 외부에 보존하고 필요한 범위만 읽습니다. RLM은 범위별 분석과 결과 통합을
깊이·호출 예산 안에서 수행합니다. 컨텍스트 편성의 바이트 예산과 Codex의 실제 토큰 사용량은 구분합니다.
supervisor는 미확인 메시지를 보존하며 스트림을 정리하고, 7일이 지난 미참조 자료만 참조 그래프를 확인해 회수합니다.

## 검증

```powershell
uv run python scripts/check.py --integration
uv run python scripts/verify_runtime.py
uv run python scripts/verify_failed_canary.py
uv run python scripts/verify_rlm.py
```

실제 모델 카나리아는 계정 할당량을 사용합니다. 정상 파일 작업, 네이티브 훅 실행,
새 세션 인계와 제한된 테스트 컨텍스트에서의 70% 감지를 검증합니다.
실패 카나리아는 Codex 실행 파일을 제거한 별도 이미지로 배포 거부와 외부 컨트롤러 롤백을 확인합니다.
운영 배포 포인터는 이 장애 주입 테스트에서 바꾸지 않습니다.

## 구조

로컬 운영 모니터: [http://127.0.0.1:8787](http://127.0.0.1:8787).
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start_monitor.ps1 -InstallStartup`
로 수집기와 웹 서버를 시작하고 사용자 로그인 시 자동 시작을 등록합니다.
웹 서버는 정제된 스냅샷만 읽습니다. 조직·작업·검수·세션·배포·훅·Docker·Redis 상태를
확인할 수 있고 출처별 수집 실패와 오래된 관측값을 표시합니다. 조회 외 조작 API는 없습니다.
5초 갱신 주기는 수집 시간 때문에 더 길어질 수 있습니다.
첫 화면인 **진행 점검**에서는 목표별 계획·구현·독립 검수·카나리아·운영 반영 기록,
마지막 활동 시각, 차단 이유와 참고 저장소 분석 상태를 확인합니다. 단계별 최근 기록을
보여주므로 재작업 시 후보가 다를 수 있습니다. 버튼의 상세 근거와 커밋을 확인하세요.
최근 활동 관측은 성과 검증이 아니며, 구현 완료도 운영 반영 완료를 뜻하지 않습니다.

호스트 MCP는 Playwright 확장 연결과 Context7 로컬 stdio를 사용합니다. Context7 OAuth
콜백 오류는 로컬 stdio 연결로 해소했고 문서 검색을 실측했습니다. Chrome 탭 할당은 확장
연결 시 사용자가 선택해야 합니다. 호스트 MCP 설정은 Docker 에이전트로 자동 전파되지 않습니다.
외부 기능의 채택 기준은 [리서치 검증 계약](docs/research-standard.md)을 따릅니다.

`domain/`은 순수 규칙, `application/`은 상태 전이와 유스케이스, `ports.py`는 내부 계약,
`adapters/`는 Codex·GitHub·Docker·저장소·GraphRAG 구현입니다.
`resources/`에는 조직 JSON, 메시지 Schema, DB 초기 스키마가 있고 `scripts/`는 운영 진입점입니다.

- [전체 설계](docs/design.md)
- [불변 조건·주석·SSOT](docs/contracts.md)
- [검증 범위와 한계](docs/status.md)
- [참고 출처](docs/references.md)
