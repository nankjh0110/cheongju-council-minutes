# 자동 최신화와 관리

## 예약 실행

GitHub Actions의 **Update minutes**가 매일 한국시간 오전 7시 17분(UTC 22:17)에 실행됩니다. 월요일은 전체 본문을 재확인하고 나머지 날은 신규·임시본 및 공개 상태가 달라진 자료를 확인합니다. 첫 갱신 때 상태 정보가 없는 기존 자료도 확인합니다.

공식 연도별·대수별 목록을 함께 조회합니다. 한쪽 목록에만 있는 회의록도 수집하며 차이를 `reports/latest-sync.json`에 기록합니다. 수집 범위는 2022-07-01부터 제4대 임기 종료까지의 공개 자료입니다. 현재 날짜 이후 자료는 포함하지 않습니다. 임시회의록은 제외하지 않고 `publication_status: provisional`로 구분합니다.

네트워크 요청, Markdown 변환, 전체 해시·날짜·발언 색인 검증이 성공한 경우에만 봇이 커밋합니다. 빈 목록, 기존 ID의 양쪽 목록에서의 소실, 목록 간 충돌, 원문 형식 변경은 실패로 처리합니다. 실패 시 기존 공개 자료는 유지되며 삭제하지 않습니다. 실패한 실행의 Actions 로그를 확인하고 원인을 해결한 뒤 다시 실행하세요.

## 지금 갱신하기

1. 저장소의 **Actions**를 엽니다.
2. 왼쪽 **Update minutes**를 선택합니다.
3. **Run workflow**에서 `main`과 `incremental`(신규·임시본) 또는 `full`(전체 본문)을 선택합니다.
4. 초록색 성공 표시와 실행 요약을 확인합니다.

CLI로도 실행할 수 있습니다.

```bash
gh workflow run sync.yml --repo nankjh0110/cheongju-council-minutes -f mode=full
gh run list --repo nankjh0110/cheongju-council-minutes --workflow sync.yml
```

예약 중단은 해당 워크플로의 메뉴에서 **Disable workflow**, 재개는 **Enable workflow**입니다. 시간 변경은 `.github/workflows/sync.yml`의 cron 값을 수정합니다. GitHub 예약 실행은 지연되거나 누락될 수 있으며 공개 저장소가 60일 동안 활동이 없으면 비활성화될 수 있습니다. 마지막 성공 여부는 Actions 및 `manifest.json`의 `checkedAt`을 확인하세요. 실패 알림은 GitHub 계정의 Actions 알림 설정에서 켤 수 있습니다.

별도 서버·OpenAI API 키·개인 GitHub 토큰이 필요하지 않습니다. 해당 저장소에 쓰기 권한이 있는 실행용 `GITHUB_TOKEN`만 사용합니다. 공식 공개 회의록만 수집하며 개인 업로드 자료는 접근하지 않습니다. 감사 대비 웹사이트의 자료는 별도로 연동해야 합니다.

## 로컬 실행

Python 3.10 이상, 외부 패키지 없이 실행합니다.

```bash
python3 scripts/sync.py --mode incremental
python3 scripts/sync.py --mode full
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

`build.py --source`는 최초 기존 앱 수집본 가져오기용입니다. 최신화된 저장소를 이전 수집본으로 덮어쓰지 마세요. 이미 보관한 Markdown의 색인만 재생성하려면 `python3 scripts/build.py`를 사용합니다.

## 데이터 구조

- `indexes/meetings.json`: id, title, date, year, term, committee, url, source_sha256, path, sha256, bytes, body_start_line. 자동 수집 후 publication_status, content_sha256, body_checked_at이 추가됩니다. 공개 상태는 공식 목록 표기이며 내용의 정확성을 보증하지 않습니다.
- `manifest.json`: 전체 수집 범위·확인 시각·대수별/연도별 건수·임시본 수.
- `reports/latest-sync.json`: 실행 모드, 신규/본문 변경 ID, 본문 확인 수, 연도별·대수별 목록 차이. 이전 보고서는 Git 이력에서 확인합니다.
- `indexes/turns/*.jsonl`: 발언 표기 구간의 1부터 시작하는 줄 번호. 일부 부록도 후보 구간에 포함되므로 질문 횟수로 해석하지 않습니다.

원문 정정은 후속 커밋에 보존합니다. 커밋 날짜를 회의일로 소급하지 않습니다. 최초 수집 이전의 모든 교정 이력을 재구성하지 않습니다. 첨부파일·사진판 PDF·동영상 전체 수집은 지원하지 않습니다.
