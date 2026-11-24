# 의약품 등 민간 시험검사기관 조회

## 설치 (GitHub Pages)
1. 기관의 외부 공개 및 자동 수집 승인, 식약처 이용조건을 확인합니다. 공개 저장소와 Pages는 누구나 열 수 있습니다. 내부용 자료는 올리지 않습니다.
2. ZIP을 압축 해제합니다. lab-search 폴더 안의 site 폴더, update.py, requirements.txt, README.md를 GitHub 저장소 main 브랜치의 루트에 올립니다 (Add file > Upload files > Commit changes). 기존 README는 이 파일로 교체 가능합니다.
3. 숨김 폴더 .github가 업로드에서 빠질 수 있으므로 Add file > Create new file에서 이름을 `.github/workflows/update.yml`로 입력하고 압축 파일 내 동일 파일의 내용을 전부 복사해 Commit changes 합니다. 이미 올렸으면 생략합니다.
4. Settings > Pages > Build and deployment > Source를 GitHub Actions로 지정합니다. Deploy from a branch가 아닙니다.
5. Settings > Actions > General에서 Actions 허용 여부와 Workflow permissions를 확인합니다. 저장소 정책에서 허용하면 Read and write permissions를 선택합니다. 환경 승인이나 브랜치 보호가 있으면 관리자 협의가 필요합니다.
6. Actions > Update and publish lab search > Run workflow > main > Run workflow. 로그에서 수집, 저장, 배포 결과를 확인합니다. 수집 실패는 기존 데이터와 실패 상태를 게시하도록 구성되어 있습니다. 실패 로그를 무시하지 마세요.
7. Settings > Pages에서 실제 웹 주소를 확인합니다. 예: https://아이디.github.io/lab-search/ . 직원에게 URL을 공유합니다.

## 운영
- 매일 09:00 KST 목표(UTC 00:00). GitHub 예약 실행은 지연될 수 있습니다. 공개 저장소에서 장기간 활동이 없으면 예약 실행이 비활성화될 수 있으므로 Actions 확인이 필요합니다.
- 최신 자료 확인 버튼은 이미 배포된 공동 데이터만 다시 읽습니다. 식약처 즉시 조회는 관리자가 Actions에서 Run workflow를 누릅니다. 브라우저에 GitHub 토큰을 넣지 마세요.
- 수동 파일올리기는 해당 브라우저 세션의 데이터만 바꿉니다. 공동 자료에는 반영되지 않습니다. 새로고침 시 공동 자료로 돌아갑니다. PDF.js CDN 사용(인터넷 필요), 파일 자체는 브라우저에서 처리.
- 수집 프로그램은 식약처 게시판 첫 5페이지의 두 분야 최신 게시글을 탐색하고 상세 페이지의 PDF 링크만 읽습니다. HWPX는 지원하지 않습니다. 동일 파일은 SHA-256으로 판별합니다. 형식, 개수, 기관 연결, 시험항목 번호 및 급격한 감소를 검사합니다. 오류 분야 기존 자료 유지. 검증은 구조 검사이며 시험 적합성이나 모든 문자의 정확성을 보증하지 않습니다.
- 최초 자료는 기존 웹앱 데이터(의약품 등 33, 화장품 19)를 유지합니다. 제공 PDF로 별도 서버 파서의 기관 수 추출을 테스트했습니다(33, 19). 실제 식약처 서버 HTTP 다운로드와 GitHub 실행은 이 환경에서 검증하지 못했습니다. 첫 실행에서 로그와 원문 대조가 필수입니다. PDF 양식 변경 시 파서 수정 필요.
- data.json, changes.json, status.json은 자동 커밋됩니다. 이전 정상 버전 복구는 저장소 커밋 이력을 사용합니다. changes.json은 최근 100건의 갱신 이벤트를 보관합니다. 원문 페이지 변동 및 공백 차이가 변경으로 나타날 수 있습니다.
- 수집 실패 또는 검증 실패: Actions 실행 로그를 확인하고 원문과 대조합니다. 기존 자료는 유지되지만 최신 여부는 확인 필요입니다. 관리자만 검토 후 데이터를 교체합니다.
- 개인정보 입력은 없지만 GitHub/CDN은 일반적인 접속 로그를 처리할 수 있습니다. 공개 서비스 이용 승인 후 사용하십시오.

## 파일 구성
- site/index.html : 기존 검색 화면, 공동 자료 새로 읽기, 파일올리기, 변경 이력
- site/data.json : 기준 자료와 기관 목록
- site/status.json : 마지막 자동 확인 상태
- site/changes.json : 변경 이력
- update.py : 게시판 수집 및 PDF 파서
- requirements.txt : Python 의존성
- .github/workflows/update.yml : 예약 실행, 커밋, Pages 배포

공식 게시판: https://www.mfds.go.kr/brd/m_627/list.do
GitHub Pages 안내: https://docs.github.com/en/pages
