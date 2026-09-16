# 청주시의회 회의록

청주시의회 **제3대·제4대 공개 회의록**을 Markdown으로 보관하는 비공식 공개 자료 저장소입니다. 사람이 원문을 읽거나, AI에게 저장소를 읽혀 발언·쟁점·후속 조치를 출처와 함께 검색할 수 있도록 구성했습니다.

<!-- archive-status -->
최종 확인: **2026-09-16** · **888건** (제3대 855건 / 제4대 33건). 임시회의록 19건 포함. 가장 최근 회의일: 2026-09-09.
<!-- /archive-status -->

## 먼저 찾아보기

- [연도별 회의록](indexes/years/README.md)
- [대수별 회의록](indexes/terms/README.md)
- [위원회 코드별 회의록](indexes/committees/README.md): 각 목록에서 당시 회의명을 확인할 수 있습니다.
- [전체 회의록 목록과 공식 원문 주소](indexes/meetings.json)
- [발언자 검색용 명단](indexes/speakers.json): 의원·공무원 등이 함께 포함된 원문 표기 기반 색인입니다.
- [AI에게 읽힐 안내](AI_INSTRUCTIONS.md)
- [수집 범위·미확보 내역](manifest.json)

## AI로 이용하기

코드나 저장소를 읽을 수 있는 AI에게 이 저장소를 연결하고 다음과 같이 요청하세요.

> AI_INSTRUCTIONS.md를 먼저 읽고, 2024~2026년 회의록에서 어린이 물놀이장을 검색해 주세요. 의원의 질문과 공무원의 답변을 구분하고 회의일, 발언자, 회의록 ID, 정확한 인용문, 공식 원문 링크를 붙여 주세요.

> 김준석 의원의 공원관리과 관련 발언을 검색해 반복 쟁점을 정리하고, 이를 근거로 2026년 행정사무감사 예상질의 5개를 만들어 주세요. 과거에 실제 한 질문과 앞으로 나올 수 있는 질문을 구분해 주세요. 확인되지 않은 사실은 만들지 마세요.

저장소 링크만 전달했다고 AI가 모든 회의록을 읽은 것은 아닙니다. 도구 사용과 파일 접근이 가능한 AI에서는 아래 검색기를 실행하고, 검색 결과의 회의록 본문을 열어 문맥을 확인하게 하세요. 일반 웹 대화에서는 관련 Markdown 파일을 내려받아 첨부할 수 있습니다. 이 저장소 자체는 AI 서비스·로그인·API 키·유료 호출을 제공하지 않습니다.

## 내 컴퓨터에서 검색하기

GitHub의 초록색 **Code → Download ZIP**으로 내려받거나 `git clone https://github.com/nankjh0110/cheongju-council-minutes.git`로 복제하세요. Python 3.10 이상이면 별도 패키지 설치 없이 실행됩니다.

```bash
# 여러 연도에서 해당 문구가 포함된 회의록 검색
python3 scripts/search.py '어린이 물놀이장' --years 2024 2025 2026

# 특정 의원이 직접 말한 구간 검색
python3 scripts/search.py '물놀이장' --speaker 김준석 --years 2024 2025 2026

# 당시 위원회 회의명으로 범위 제한
python3 scripts/search.py '공원관리과' --committee 농업정책위원회 --term 4

# AI·다른 프로그램에 넘길 JSON과 다음 검색 결과
python3 scripts/search.py '안전' --years 2025 --json --limit 20 --offset 20

# 데이터 무결성 확인
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

검색은 문구 기반이며 띄어쓰기 차이를 일부 허용합니다. 동의어·의미 검색은 AI가 검색어를 바꾸어 수행해야 합니다. 일반 검색의 건수는 회의록 수, `--speaker` 검색의 건수는 일치하는 발언 표기 구간 수입니다. 질문 개수나 관심도의 확률로 해석하지 마세요. `--offset`으로 다음 결과를 조회할 수 있습니다.

## 저장 형식

- `minutes/term-3/2022/minutes-XXXX.md`: 회의록 1건당 Markdown 파일 1개
- `minutes/term-4/2026/…`: 제4대 회의록
- `indexes/meetings.json`: 날짜·대수·위원회 코드·공식 URL·파일 경로·SHA-256
- `indexes/turns/연도.jsonl`: 원문 발언 표기 구간과 시작·끝 줄, 발언자 표기
- `indexes/speakers.json`: 원문에서 식별한 발언자 목록
- `manifest.json`: 수집 기준일·건수·범위

각 Markdown의 YAML 머리말에는 `id`, `title`, `date`, `year`, `term`, `committee`, `url`, `source_sha256`가 있습니다. 머리말 다음은 기존에 수집한 Markdown을 바이트 단위로 보존했습니다. HTML·사진판 PDF 원본 파일 자체를 포함한 것은 아니며 공식 원문 주소를 제공합니다.

## 정확성과 변경 이력

공식 출처는 [청주시의회 회의록 시스템](https://councilrec.cheongju.go.kr/)입니다. 원문이 정정되거나 색인에 오류가 있으면 공식 원문을 우선 확인하세요. 이 저장소는 청주시·청주시의회의 공식 서비스가 아닙니다.

회의일은 문서 메타데이터에 기록합니다. Git 커밋 날짜는 실제 반영 시점이며 회의가 열린 날짜로 소급하지 않습니다. 앞으로 수정된 문서를 반영하면 `git diff`와 `git log`로 변경 내역을 확인할 수 있습니다. 현재는 수집 기준일의 스냅샷으로, 최초 공개부터의 모든 교정 이력을 재구성하지 않았습니다. 매일 한국시간 오전 7시 17분에 신규·임시 회의록을 확인하며, 월요일에는 기존 본문 전체도 다시 확인합니다. GitHub 사정에 따라 실행이 늦어질 수 있습니다. [실행 현황](https://github.com/nankjh0110/cheongju-council-minutes/actions/workflows/sync.yml)에서 확인하세요.

발언자 색인은 `○` 표기와 직위·이름을 규칙으로 분리한 보조 자료입니다. 일부 표기나 동명이인을 완전히 판별하지 못할 수 있습니다. 원문 문맥과 출석 명단을 확인해야 하며 현 위원회 소속을 과거 시점에 그대로 적용하지 마세요. 과거 발언에 없는 개인적 성향·의도·미래 발언을 단정해서는 안 됩니다.

## 갱신·오류 신고

[데이터 구조와 갱신 방법](docs/MAINTENANCE.md)을 참고하세요. 오류를 발견하면 회의록 ID, 공식 원문 주소와 해당 구절을 첨부해 Issue 또는 Pull Request로 제안해 주세요. 개인 보충자료, 인증정보, API 키는 올리지 마세요.

원문과 제3자 내용에 저장소 코드의 MIT 라이선스를 일괄 적용하지 않습니다. 출처와 이용 조건은 [NOTICE](NOTICE.md)를 확인하세요. 검색·검증 스크립트는 [MIT](LICENSE-CODE)입니다.

구성에 참고한 프로젝트: [대한민국 법령 저장소 legalize-kr](https://github.com/legalize-kr/legalize-kr). 해당 프로젝트의 코드나 법령 데이터는 이 저장소에 복사하지 않았습니다.
