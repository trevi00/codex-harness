# 구현 및 검증 상태

## 구현

- 3계층 조직, 육하원칙 JSON, 상하 관계 권한, 중복 방지 outbox/ACK/회수/dead-letter.
- PostgreSQL 영속 작업, 선행 조건, 기한, lease/generation, 취소·실패·정체·재시도 예산.
- Codex App Server 실행, 현재 토큰 70% 안전 지점 인계, 진행 결과 저널·그래프 체크포인트.
- Docker 에이전트, 1시간 유휴 종료, 메시지·작업 기반 기동, 동시 실행 2개 제한.
- GitHub Trending·GeekNews 주기 수집, 원본 커밋·라이선스·README 보존, 토픽 중복 방지.
- 연구·승인·계획·구현·독립 검수·PR·기존 기준 테스트·CLI 카나리아·병합·배포 연결.
- main 변경 시 rebase 및 재검수, 이미지 ID 고정, 이전 배포 보관, 외부 감시·롤백.
- 독립 사건 2회에 필수 네이티브 훅, 재현·정상 사례, 코드 해시·커밋 결합 검수와 활성화.
- 활성 훅 재발 시 개선 작업, 검증 중 이전 버전 유지, 훅·배포 롤백 연결.
- Tree-sitter Python 심볼/import/보수적 호출, 운영 그래프, pgvector 다국어 ONNX 검색.
- 외부 자료·범위 조회·RLM 분석, 결정론적 컨텍스트 편성, 원본 버전 검사.
- 메시지 정리, 참조 증거를 보존하는 자료 회수, Windows/Linux 가상 환경 분리.

## 실제 증거

- 2026-09-07: [PR #1](https://github.com/trevi00/codex-harness/pull/1) 실제 생성·병합.
  팀원 구현 → 독립 팀장 검수 → 독립 지휘자 검수 → 당시 58개 통합 테스트 → 후보 Docker CLI 파일 작업 → 배포.
  후보 `2883db0158d8036f0d6dbb5411f1af6972b8950f`, 병합 `600aecef31aff706ffb9bb6a565c2852042ff936`.
- 이후 확장판은 64개 테스트와 Ruff를 통과했다. 실제 PostgreSQL·Redis 통합 테스트 포함.
- 호스트 및 Docker에서 실제 Codex 파일 작업, 네이티브 훅, 새 스레드 인계, 토큰 관측을 확인했다.
- 70% 감지는 실제 App Server를 제한된 테스트 컨텍스트 창으로 실행한 검증이다. 전체 모델 창 부하 시험은 아니다.
- CLI가 없는 별도 Docker 이미지에서 실패·승격 거부·외부 컨트롤러 롤백을 확인했다.
  승인/배포 상태는 격리 fixture이고 실제 운영 포인터는 유지했다.
- 실제 GitHub·GeekNews 수집과 로컬 다국어 ONNX 임베딩 생성·저장을 확인했다.
- RLM은 명시적인 합성 자료를 실제 Codex 3회 호출로 분할 분석·통합하는 검증을 통과했다.
- 최신 진행 상태·검수·배포 증거의 원본은 PostgreSQL과 `.runtime/artifacts`다.

## 명확한 범위

- 장기 무인 운영과 최대 컨텍스트 부하 신뢰도는 앞으로 누적할 측정이다. 소수 테스트를 SLO 달성으로 해석하지 않는다.
- SRE/arc42는 검수 관점이다. 인증이나 모든 체크리스트의 형식적 증명은 아니다.
- Tree-sitter 자동 추출은 Python이다. 동적 호출은 `may_call`이며 전체 호출 그래프라고 주장하지 않는다.
- 그래프는 파생 자료이며 모든 OS 도구 부작용을 분산 트랜잭션으로 되돌리지는 않는다.
- 로컬 실행 주체를 신뢰한다. Schema/조직 검사는 암호학적 인증이나 적대적 에이전트 격리가 아니다.
- DB는 JSONB와 전역 트랜잭션 잠금을 사용한다. 파괴적 DB 스키마 변경의 자동 downgrade는 지원하지 않는다.
- 충돌 있는 rebase, 검증 환경 차단, 예산 소진은 명시적으로 남긴다. 성공으로 바꾸거나 무한 재시도하지 않는다.
- 참고 저장소는 선택한 설계·자가개선 경로를 조사했다. 전체 파일 전수 감사는 아니다.

## Output-schema recurrence candidate (2026-09-07)

Baseline: `7b09e1c70b8288f984b65794828d5ac21425cd7b`; supplied plan artifact
`sha256:bdc33853e3c340f8b50c7ea8da3c8c570b700150636a7332f61abf2f69eb2f86`
was read and hash-verified. Read-only PostgreSQL inspection succeeded: the required
hook record matches the supplied version 3 record, including all nine incident IDs
and 18 evidence references. The previous active revision is
`a8a9aae40ae088e89a80b93c5e9e1e3270bd14f3`, script hash
`4630179b05ca0e255fbf95b21bc4af310d1bc655ded9547ff35e61928147f4ee`.
The local incumbent policy digest matches the supplied runtime policy:
`5642c13028e0f71ecd25a866a2aa37b81f228dd1dc4d68f8db2c0f9d95f3b7a3`.
No runtime records or installed hook configuration were changed.

All 18 referenced artifacts were retrieved from `/runtime/artifacts` and their exact
bytes hash-verified: nine failure receipts and nine diagnosis records. The diagnoses
refer to `09c1d58298b22337125f29842382d2aef960c7d2`; the failure receipts explicitly
report missing type at properties.version. Two receipt pairs are retries of the same
task (634a1c5b attempts 2/3; a24a84fa attempts 1/3), so nine records alone do not prove
nine independent production occurrences. Exact submitted request bytes, deployment
revision at each failure, and failure timestamps are absent from these small receipts.
The database recurrence classification is retained, not silently rewritten. There is
no evidence here that the baseline typed schema regressed. Other provider errors,
including tests_not_run.items requiring additionalProperties:false, have a separate
cause; the existing generated-schema regression covers that historical failure.

The standalone stdlib SessionStart reminder now describes hash/path/revision/provider
error preservation and cause confirmation, while retaining startup/resume/clear/compact
and silent malformed-input behavior. Its manifest hash and expected outputs are updated.
The native input/output shape was checked against the
[official hook contract](https://learn.chatgpt.com/docs/hooks#sessionstart).
Manifest reproduction is reminder replay only: SessionStart has no outputSchema to
inspect or repair. Actual missing-type reconstruction remains in
`test_baseline_reconstruction_and_semantic_preservation`, using the historical Git
schema, with both transport boundaries covered by `tests/test_output_schema.py`.
No new schema or enforcement defect was demonstrated, so resource schemas and adapter
preflight remain unchanged, preserving historical record compatibility.

New lifecycle regressions exercise active recurrence, identical message redelivery,
new-message delivery of the same occurrence, version advancement, rejected review and
canary, replacement resetting approvals, stale revision/spec evidence, previous-active
configuration retention through verification, activation and rollback through existing
application use cases. All lifecycle approvals/canaries in tests are fixtures.

Review handoff: bind the final Git commit/tree and manifest spec digest to the incumbent
policy above. A candidate proposed from the inspected runtime record would advance to
version 4; re-read PostgreSQL before any actual proposal. Independent lead review must
precede conductor review, followed by actual CLI release canaries under INV-RELEASE-001.
Required command inspection must succeed; namespace denial means inspection-blocked,
with command evidence preserved and no accepted review. No privilege changes are allowed.
Production recurrence resolution, installed lifecycle delivery and deployment remain
unverified. This candidate does not approve, activate, push, merge or deploy a release.

Validation for this candidate: `uv run ruff check .` passed; `uv run pytest -ra`
passed 285 tests, with 24 integration tests skipped because `HARNESS_INTEGRATION=1`
was unset. These skipped tests need isolated local services; the read-only production
state inspection is not a substitute. The focused schema/native suite passed 50 tests.
Existing authorization, stale-write, context-overflow, schema execution failure and
promotion-failure regressions remain in the full suite. No independent review or
actual CLI canary was run for this candidate. `scripts/verify_output_schema.py` can
collect exact-commit synthetic provider compatibility receipts after committing;
those receipts still cannot substitute for independent review or release canaries.

Candidate spec digest: `ecb916bf225e0007ddfe0007db5b821a834394daf571ebacc01acf5f6233f967`; exact UTF-8 script SHA-256:
`12ce6f8c1dc51baf58fb0249579e411fb7412bdd228e7d57a5595f506438be25`. The containing Git commit/tree binds this handoff
and the four changed files; obtain both with `git rev-parse HEAD HEAD^{tree}`.
