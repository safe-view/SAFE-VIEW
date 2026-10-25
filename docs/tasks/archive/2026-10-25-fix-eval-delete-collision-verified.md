# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `76d5ea90ea1c73770de7ceec61618593f06447e4`
**승인 필요:** 아니오 (데이터 손상을 일으키는 버그 수정 — 사용자가 직접 겪은 사고 원인이고, 고치자고 명시적으로 동의함, 2026-10-25)
**최종 갱신:** 사용자 실사용 확인 완료 (추가·삭제 모두 정상 동작), 2026-10-25

이 작업은 "성능평가 기록 삭제 버그 수정"이다. 사용자가 성능평가 페이지의 "기록 삭제" 기능으로 기록 1~2건을 지우려다, 같은 타임스탬프를 가진 2026-09-07 수동 기록 8건이 전부 사라지는 사고를 겪었다(`docs/tasks/archive/2026-10-25-auto-performance-eval-verified.md`의 성능평가 자동화 작업 중 발견). 원인은 `core/performance_eval.py`의 `delete_record(timestamp)`가 **타임스탬프 문자열이 같은 행을 전부** 지우는 구조였기 때문 — 당시 8건이 한 스크립트 실행으로 한꺼번에 기록돼 타임스탬프(초 단위)가 전부 똑같았다.

## 1. 목표

평가 기록 각 행에 **고유 ID**를 부여해, 삭제가 "그 ID를 가진 딱 한 행만" 지우도록 바꾼다. 같은 타임스탬프(초 단위까지 동일)를 가진 기록이 여러 개 있어도 하나만 선택해서 안전하게 지울 수 있어야 한다. 기존에 ID 없이 저장된 레거시 CSV(팀원 각자 PC에 로컬로 쌓여 있을 수 있음 — `logs/`는 `.gitignore`에 있어 git으로 공유되지 않는다)를 열었을 때도 깨지지 않고, ID를 자동으로 채워 넣은 뒤 정상 동작해야 한다.

## 2. 현재 상태

- `core/performance_eval.py`:
  - CSV 헤더: `timestamp, scenario, source, result, response_time_sec, notes` (ID 없음).
  - `add_record()`: `datetime.now().strftime("%Y-%m-%d %H:%M:%S")`를 타임스탬프로 써서 한 행 추가 — **초 단위까지만** 기록하므로, 같은 초에 여러 행이 생기면 타임스탬프가 완전히 똑같아진다(사고의 원인).
  - `delete_record(timestamp: str) -> bool`:
    ```python
    def delete_record(timestamp: str) -> bool:
        records = load_records()
        if not records:
            return False
        filtered = [r for r in records if r.get("timestamp") != timestamp]
        if len(filtered) == len(records):
            return False
        ...  # filtered 를 그대로 다시 씀
    ```
    `!=` 비교라서 같은 타임스탬프를 가진 행이 여러 개면 **전부** 걸러져서 사라진다.
  - `load_records()`: CSV를 그대로 `csv.DictReader`로 읽어 리스트로 반환.
- `pages/4_성능_평가.py` 123~135행: "기록 삭제" expander. `st.selectbox`로 `f"{timestamp} | {scenario}"` 문자열 목록을 보여주고, 선택한 문자열에서 타임스탬프만 잘라내 `delete_record(timestamp_to_del)`을 호출한다. 이 UI도 "타임스탬프가 유일한 식별자"라는 잘못된 전제 위에 있다.
- `tools/auto_eval.py`(별도 브랜치 `김영민/auto-performance-eval`, 아직 main에 머지 전)의 `remove_previous_auto_records()`는 바로 이 버그를 우회하려고 "지우려는 타임스탬프를 다른 무관한 기록도 쓰고 있으면 중단"하는 방어 코드를 넣어뒀다 — 이번 수정으로 ID가 생기면 그 방어 코드는 더 이상 필요 없어지지만, **이번 작업에서는 그 파일을 건드리지 않는다**(아직 머지 안 된 별도 브랜치라 베이스가 다름 — 충돌 방지). 두 브랜치가 머지된 뒤 별도로 단순화하면 된다(7번 참고).

## 3. 구현 계획

1. **CSV에 `id` 컬럼 추가**(맨 앞): `id, timestamp, scenario, source, result, response_time_sec, notes`.
2. **`add_record()`**: 각 행에 고유 ID를 생성해 같이 쓴다 — `uuid.uuid4().hex[:12]` 정도의 짧은 16진 문자열이면 충분하다(프로젝트에서 이미 디버그 식별자로 `uuid.uuid4().hex[:4]`를 쓴 전례가 있다 — 비슷한 패턴).
3. **`load_records()`에 1회성 마이그레이션 추가**: CSV를 읽었을 때 헤더에 `id` 컬럼이 없으면(레거시 파일), 기존 행마다 새 ID를 채워 넣고 **그 결과를 즉시 파일에 다시 써서 영구 반영**한다(다음에 또 열어도 마이그레이션이 반복되지 않도록). 이러면 과거에 쌓인 로컬 기록도 삭제 버그로부터 안전해진다. 빈 파일/헤더만 있는 파일은 그대로 둔다.
4. **`delete_record()`의 시그니처를 `delete_record(record_id: str) -> bool`로 변경**: `r.get("id") != record_id`로 필터링 — 정확히 그 ID를 가진 한 행만 지워진다.
5. **`pages/4_성능_평가.py`의 삭제 UI 수정**: `st.selectbox`에 `format_func`를 써서, 내부적으로는 각 행의 `id`를 값으로 쓰고 화면에는 지금처럼 `"{timestamp} | {scenario}"`를 보여준다. 선택된 `id`를 그대로 `delete_record(id)`에 넘긴다. 사용자가 보는 화면은 바뀌지 않는다 — 내부 식별 방식만 안전해진다.
6. **`compute_metrics()`, `load_records()`의 다른 호출자**는 `id` 컬럼이 추가돼도 그냥 무시하면 되므로 변경 불필요.

## 4. 수용 기준

- [ ] 새로 `add_record()`로 추가한 기록에는 `id` 값이 들어 있다.
- [ ] 같은 초에 연속으로 `add_record()`를 여러 번 호출해(타임스탬프가 완전히 같아도) 각 행의 `id`는 서로 다르다.
- [ ] `delete_record(id)`로 그 ID를 가진 행 하나만 지워지고, 같은 타임스탬프를 가진 다른 행은 그대로 남는다(사고 재현 시나리오로 직접 검증).
- [ ] `id` 컬럼이 없는 레거시 CSV(헤더가 `timestamp,scenario,source,result,response_time_sec,notes`뿐인 파일)를 `load_records()`로 읽으면, 각 행에 ID가 자동 생성되고 파일에도 영구 반영된다(다시 읽어도 같은 ID 유지) — 데이터(행 내용)는 하나도 바뀌지 않는다.
- [ ] 빈 CSV(헤더만 있거나 파일이 아예 없음)에서도 `load_records()`/`add_record()`/`delete_record()`가 에러 없이 동작한다.
- [ ] `pages/4_성능_평가.py`의 "기록 삭제" UI는 화면에 보이는 목록·문구가 기존과 동일하고, 삭제도 똑같이 동작하되 내부적으로 `id` 기반으로 바뀌었다.
- [ ] `pages/4_성능_평가.py`의 지표 계산(`compute_metrics`)·전체 목록 표시는 `id` 컬럼이 추가돼도 변화 없다(그 컬럼을 그냥 무시).
- [ ] `tools/auto_eval.py`는 이번 작업에서 건드리지 않는다(별도 브랜치, 머지 순서 충돌 방지).

## 5. 예상 변경 파일

- `core/performance_eval.py`
- `pages/4_성능_평가.py`
- `docs/tasks/current.md`
- `roi_configs/18초까지_정면_갑툭튀_야간_2.json`, `roi_configs/GTA__비__주간__2.json`, `roi_configs/같은_장소_비_2_야간.json`, `roi_configs/눈_배회.json`, `roi_configs/전체_측면_배회_야간_1.json` (이번 작업과 무관하게 이전부터 존재하던 사용자 테스트 데이터 — 그대로 둠)

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `core/performance_eval.py` | Codex (구현/테스트) | 착수 가능 |
| `pages/4_성능_평가.py` | Codex (구현/테스트) | 착수 가능 |
| `docs/tasks/current.md` | Claude (계획/리뷰) | 계획 작성 완료 |

## 7. 위험 요소 또는 주의사항

- **마이그레이션은 되돌릴 수 없는 파일 쓰기다** — `load_records()`가 레거시 파일을 감지해 즉시 재작성하므로, 마이그레이션 로직 자체에 버그가 있으면 기존 데이터를 훼손할 수 있다. 반드시 "행 개수·내용(ID 제외 전 컬럼)이 마이그레이션 전후 동일한가"를 직접 테스트로 확인해야 한다.
- 이번 수정은 **향후 사고를 막는 것**이지, 이미 사라진 9월 7일 기록 8건을 복구하는 게 아니다(복구 불가능은 이미 확인됨).
- `tools/auto_eval.py`(다른 브랜치)는 건드리지 않지만, 그 브랜치가 머지된 뒤에는 `remove_previous_auto_records()`의 타임스탬프 충돌 방어 코드가 불필요해진다 — 이번 작업이 머지된 다음에 별도로 정리하는 게 좋다(지금 당장 처리할 필요는 없음, 방어 코드가 있어도 틀리게 동작하진 않는다).
- 헤드리스 Chrome/Playwright/Selenium 등으로 실제 브라우저를 띄워 검증을 시도하지 마라(영구 금지 사항). `core/performance_eval.py`의 함수들은 Streamlit과 무관하게 직접 호출해서 테스트할 수 있다 — 임시 CSV 파일로 격리해서 확인하고, 실제 `logs/performance_eval.csv`를 테스트 중에 훼손하지 않는다.

## 구현 결과
- 실제 변경 파일: `core/performance_eval.py`, `pages/4_성능_평가.py`, `docs/tasks/current.md`
- 계획 대비 변경 요약: CSV 스키마 맨 앞에 `id` 컬럼을 추가하고 새 기록 및 레거시 기록에 12자리 UUID 기반 ID를 부여했다. 레거시 CSV는 첫 로드 시 ID를 채워 영구 재작성하며, 삭제 함수와 삭제 UI는 타임스탬프 대신 ID를 전달한다. 평가 목록에서는 `id` 컬럼을 제외해 기존 표시를 유지했다.
- 계획 이탈 사항: 구현 범위 이탈은 없음. 첫 격리 테스트에서 Python `TemporaryDirectory`가 만든 빈 디렉터리 `tmpa53eao58/`는 Windows 샌드박스 ACL로 접근·삭제가 거부되어 남았다. Git에는 추적되지 않으며 실제 로그와 무관하다.
- 종료 시점 git 상태 (`git -c core.quotepath=false status --porcelain`):
  ```text
   M core/performance_eval.py
   M docs/tasks/current.md
   M pages/4_성능_평가.py
  ?? roi_configs/18초까지_정면_갑툭튀_야간_2.json
  ?? roi_configs/GTA__비__주간__2.json
  ?? roi_configs/같은_장소_비_2_야간.json
  ?? roi_configs/눈_배회.json
  ?? roi_configs/전체_측면_배회_야간_1.json
  ```

## 테스트 결과
- 실행 명령/검증:
  - `python -m py_compile core/performance_eval.py 'pages/4_성능_평가.py'` — PASS
  - `git diff --check` — PASS (오류 없음; Git의 기존 LF→CRLF 경고만 출력)
  - 작업공간 루트의 단일 임시 CSV로 `core.performance_eval`의 파일 경로를 격리한 Python 검증 — PASS: 파일 없음, 동일 타임스탬프 3건 추가/고유 ID, ID 1건 삭제 후 나머지 2건 보존, 레거시 2행 마이그레이션 전후 비-ID 데이터 동일, 재로드 시 ID 유지, 새 스키마 헤더 전용 파일의 로드/추가/삭제, `compute_metrics()`를 확인했다. 임시 CSV는 검증 종료 시 삭제했다.
  - 참고: 앞선 `TemporaryDirectory` 기반 시도는 Windows 샌드박스가 생성 직후 해당 디렉터리 접근을 거부해 코드 검증 전에 중단됐다. 이후 단일 임시 CSV 방식으로 같은 검증 범위를 성공적으로 재실행했다.
  - `rg -n "delete_record\\(" ...` 및 변경 diff 정적 검토 — PASS: 삭제 호출자는 페이지 한 곳뿐이며 선택값 ID를 그대로 전달한다. `format_func`의 표시 문자열은 기존 `timestamp | scenario`와 동일하고, DataFrame은 `id`를 제외한다. `tools/auto_eval.py` 변경 없음.
- 수용 기준 체크리스트:
  - [x] PASS — 새로 `add_record()`로 추가한 기록에는 `id` 값이 들어 있다.
  - [x] PASS — 같은 초에 연속으로 `add_record()`를 여러 번 호출해(타임스탬프가 완전히 같아도) 각 행의 `id`는 서로 다르다.
  - [x] PASS — `delete_record(id)`로 그 ID를 가진 행 하나만 지워지고, 같은 타임스탬프를 가진 다른 행은 그대로 남는다(사고 재현 시나리오로 직접 검증).
  - [x] PASS — `id` 컬럼이 없는 레거시 CSV(헤더가 `timestamp,scenario,source,result,response_time_sec,notes`뿐인 파일)를 `load_records()`로 읽으면, 각 행에 ID가 자동 생성되고 파일에도 영구 반영된다(다시 읽어도 같은 ID 유지) — 데이터(행 내용)는 하나도 바뀌지 않는다.
  - [x] PASS — 빈 CSV(헤더만 있거나 파일이 아예 없음)에서도 `load_records()`/`add_record()`/`delete_record()`가 에러 없이 동작한다.
  - [x] PASS — `pages/4_성능_평가.py`의 "기록 삭제" UI는 화면에 보이는 목록·문구가 기존과 동일하고, 삭제도 똑같이 동작하되 내부적으로 `id` 기반으로 바뀌었다.
  - [x] PASS — `pages/4_성능_평가.py`의 지표 계산(`compute_metrics`)·전체 목록 표시는 `id` 컬럼이 추가돼도 변화 없다(그 컬럼을 그냥 무시).
  - [x] PASS — `tools/auto_eval.py`는 이번 작업에서 건드리지 않는다(별도 브랜치, 머지 순서 충돌 방지).
- 미실행 항목과 사유: 실제 브라우저 UI 조작은 계획의 헤드리스 Chrome/Playwright/Selenium 영구 금지 조건에 따라 미실행했다. 해당 수용 기준은 Python 구문 검사와 UI 코드 경로 정적 검토로 확인했다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 구현이 계획과 정확히 일치한다. UUID 기반 12자리 ID 도입으로 동일 타임스탬프 다중 행 일괄 삭제 버그가 근본적으로 해결됐고, 레거시 CSV 마이그레이션 로직(첫 로드 시 감지 → ID 채워 영구 재작성)도 올바르게 구현됐다. 변경 범위는 계획한 두 파일로 한정됐으며 tools/auto_eval.py는 건드리지 않았다.
- scope_ok: True
- 수용 기준 판정:
  - [pass] 새로 add_record()로 추가한 기록에는 id 값이 들어 있다
  - [pass] 같은 초에 연속으로 add_record()를 여러 번 호출해도 각 행의 id는 서로 다르다
  - [pass] delete_record(id)로 그 ID를 가진 행 하나만 지워지고, 같은 타임스탬프를 가진 다른 행은 그대로 남는다
  - [pass] id 컬럼이 없는 레거시 CSV를 load_records()로 읽으면 ID가 자동 생성되고 파일에도 영구 반영된다
  - [pass] 빈 CSV(헤더만 있거나 파일 없음)에서도 load_records()/add_record()/delete_record()가 에러 없이 동작한다
  - [pass] pages/4_성능_평가.py의 삭제 UI 화면에 보이는 목록·문구가 기존과 동일하고, 내부적으로 id 기반으로 바뀌었다
  - [pass] pages/4_성능_평가.py의 지표 계산(compute_metrics)·전체 목록 표시는 id 컬럼 추가돼도 변화 없다
  - [pass] tools/auto_eval.py는 이번 작업에서 건드리지 않는다
- 남은 위험/후속 작업:
  - _write_records()에 extrasaction 미지정(기본값 'raise') — 현재 포맷은 add_record()/마이그레이션만 쓰므로 실질 위험 없음, 향후 컬럼 추가 시 extrasaction='ignore' 또는 명시적 필드 제한 고려 필요
  - tools/auto_eval.py의 remove_previous_auto_records() 내 타임스탬프 충돌 방어 코드는 이번 수정 머지 후 불필요해짐 — 두 브랜치 머지 완료 후 별도로 단순화 권장(계획 7번 참고)
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

