# 데이터 구조와 갱신

현재 자료는 기존 audit-game 프로젝트에서 이미 수집한 공식 공개 회의록만 내보낸 것입니다. 로그인 데이터, R2, 업로드 자료, 환경변수, 개인 메모는 읽거나 복사하지 않습니다.

## 기존 수집본을 다시 반영하기

```bash
python3 scripts/build.py --source /path/to/audit-game
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

build.py는 data/council-corpus.json과 data/catalog.json을 읽어 허용된 공개 minutes-숫자.md.bin만 해제합니다. 카탈로그의 원문 SHA-256과 대조하며, 원문을 고치지 않고 YAML 머리말을 붙입니다. 공개 출처 URL을 검사합니다. 갱신 전에 기존 수집 프로젝트에서 공식 목록과 원문을 수집해야 하며 이 저장소만으로 실시간 수집하지 않습니다.

이미 내보낸 Markdown에서 발언자·연도별 색인만 다시 만들려면 `python3 scripts/build.py`를 실행합니다. 원문을 수정했다면 회의록 색인의 해시도 기존 공식 수집본을 통해 갱신해야 합니다. validate.py는 임의 변경을 실패로 처리합니다.

## 스키마

meetings.json의 각 항목: id, title, date, year, term, committee, url, source_sha256, path, sha256, bytes, body_start_line.

turns/*.jsonl의 각 항목: id, meeting_id, path, date, term, committee, speaker, role, label, start_line, end_line. 줄 번호는 1부터 시작하고 끝 줄을 포함합니다. 식별하지 못한 발언자 표기는 speaker가 빈 문자열입니다. ○로 시작하는 일부 부록 표기도 후보 구간에 포함될 수 있습니다. 통계는 발언·질문 횟수의 공식 집계가 아닙니다.

speakers.json은 이름 문자열별 보조 집계이며 동명이인 분리 식별자는 아닙니다. 현재 명단에 없는 과거 의원·공무원도 포함됩니다.

## 게시 이력

첫 반영은 공개 수집본 일괄 가져오기입니다. 과거 회의일로 커밋을 소급하지 않고 원문 정정은 후속 커밋으로 보존합니다. 기준일·누락·제외 범위를 manifest.json과 README에 함께 갱신하세요. GitHub Actions는 push/PR 시 무결성과 합성 검색 테스트만 수행하며 자동 수집·API 분석은 하지 않습니다.
