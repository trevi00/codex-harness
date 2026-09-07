# Codex Self Harness

자신의 실행 경험과 오픈소스 연구로 발전하는 Codex 조직의 **0.1 실행 기반**입니다.
지휘자·팀장·팀원, 육하원칙 JSON, 헥사고날 구조, 프로그램으로 구성하는 컨텍스트를 사용합니다.

현재 코드는 실제 PostgreSQL/Redis 연결과 작은 자기 개선 경로를 검증합니다.
자율 연구→코드 PR→독립 에이전트 심사→운영 배포 전체가 완성된 버전은 아닙니다.

## 시작

필요: Python 3.12+, uv, Docker Compose. 실제 모델 검증에는 로그인된 Codex CLI가 필요합니다.

```powershell
cd C:\Users\rudtn\codex-harness
uv sync --frozen
python scripts/setup.py
docker compose up -d --wait postgres redis
uv run harness init-db
uv run harness doctor
python scripts/check.py --integration
```

DB: `127.0.0.1:55432`, Redis: `127.0.0.1:56379`. `.env`는 자동 생성한 로컬 비밀번호이며 Git에 포함하지 않습니다.
볼륨은 `codex-harness` Compose 프로젝트 소유입니다. 중지에는 `docker compose stop`을 사용합니다.

## 첫 자기 개선 경로

```powershell
uv run harness demo
uv run harness run-command -- codex.ps1 --version
uv run harness inspect hooks
uv run harness inspect sessions
```

`demo`는 **고정된 재현 fixture와 스크립트 검수**로 두 사건→훅 필요→후보→팀장/지휘자 검수 기록→시작 카나리아→활성화를 실행합니다.
Windows의 `codex.ps1` 대신 `codex.cmd`를 선택하는 선언형 훅을 DB에 저장합니다.
`run-command`가 활성 훅을 실제 argv에 적용하고 실행합니다. 정상 명령은 그대로 유지합니다.
모델이 PR을 읽고 검수했다고 기록하지 않으며 GitHub에 PR을 생성하거나 운영 코드를 배포하지 않습니다.
같은 scope에서 재실행하면 기존 활성 훅을 유지합니다. 다른 실험은 `demo --scope experiment-name`으로 분리합니다.

## 메시지와 컨테이너

```powershell
uv run harness organization
uv run harness validate examples/incident.json
docker compose --profile agents build conductor
docker compose --profile agents up -d --no-build
uv run harness send examples/incident.json
uv run harness flush
uv run harness inspect deliveries
```

발신자·수신자는 조직 그래프를 따라야 합니다. `who/what/why/when/where/how`는 모두 필수입니다.
예시는 동일 occurrence ID를 사용하므로 반복 전송해도 두 사건으로 세지 않습니다.
팀장 컨테이너는 사건을 처리하고, 두 번째 독립 사건에서 outbox를 통해 지휘자에게 `hook.required`를 보냅니다.
아직 구현하지 않은 메시지 작업은 `awaiting_handler`로 보존합니다. 수신을 작업 완료로 표시하지 않습니다.
잘못된 메시지는 dead-letter로 이동합니다. 중단된 소비자의 미확인 메시지는 재회수합니다.

```powershell
uv run python scripts/supervise.py --once
# 계속 운영할 때: uv run python scripts/supervise.py
```

외부 supervisor는 대기 메시지가 있는 설정된 소비자 컨테이너를 깨웁니다.
소비자는 1시간 동안 처리할 메시지가 없으면 종료합니다. supervisor는 아직 상주 등록하지 않았습니다.
현재는 메시지 소비자 수명 관리이며 실제 Codex 스트림의 70% 감지·중단/인계는 후속 연결 대상입니다.
세션 체크포인트의 generation 검사와 70%/1시간 판단 함수는 구현·테스트되어 있습니다.

## 코드 그래프와 컨텍스트

```powershell
uv run harness index .
uv run harness query record_incident
uv run harness context record_incident --budget 12000
```

Tree-sitter Python으로 파일·클래스·함수·불변 조건 주석을 추출하고 관계를 PostgreSQL에 저장합니다.
각 항목에 원본 위치와 파일 내용 해시를 보관합니다. 파싱 실패 시 이전 인덱스를 유지합니다.
현재 검색은 키워드+제한된 그래프 확장입니다. pgvector 저장·검색 어댑터는 통합 검증했으나
실제 임베딩 모델 선택·자동 생성·하이브리드 랭킹은 아직 연결하지 않았습니다.
전체 언어의 import/call 관계나 운영 조직 그래프를 자동 추출한다고 주장하지 않습니다.

컨텍스트는 필수 계약과 선택 근거로 구성하고, 제외한 항목의 이유도 남깁니다.
UTF-8 바이트 수로 보수적인 예산을 계산합니다. 모델 토큰 측정값과 혼동하지 않습니다.
필수 계약이 넘치면 오류로 반환해 작업 분해를 요청합니다.

## Codex 검증

```powershell
uv run harness canary
uv run harness canary --live
```

기본은 CLI 시작 검사입니다. `--live`는 실제 계정 할당량을 사용해 임시 파일 읽기·쓰기·JSON 응답을 검증합니다.
운영 인증 파일은 이미지에 포함하지 않습니다. 컨테이너의 실제 모델 실행에는 별도 런타임 인증 연결이 필요합니다.
명령은 argv와 stdin으로 전달하고, 시간 초과 시 생성한 프로세스 트리를 종료합니다.

## 구조와 문서

```text
src/codex_harness/
  domain/        순수 조직·사건·컨텍스트·세션·훅 규칙
  application/   사건 기록·후보·검수·카나리아·활성화·인계 유스케이스
  ports.py       저장·메시지·지식·실행 계약
  adapters/      PostgreSQL·Redis·Tree-sitter·Codex·프로세스 실행
  resources/     조직 JSON·메시지 JSON Schema·DB 초기 스키마
  bootstrap.py   실제 어댑터 조립
  cli.py         CLI 및 메시지 소비 진입점
scripts/         설정·검증·컨테이너 호출 자동화
tests/           순수 규칙·의존 경계·실제 DB/Redis 통합 테스트
```

- [전체 설계](docs/design.md)
- [불변 조건과 SSOT](docs/contracts.md)
- [현재 구현 범위와 후속 작업](docs/status.md)
- [참고 출처](docs/references.md)
