# notion_boanNews_crawling

# 크롤링 및 자동화 스크립트 매뉴얼

이 스크립트는 특정 보안 뉴스 및 공지사항 데이터를 크롤링하고 이를 Notion 데이터베이스에 저장하거나 관리하는 기능을 제공합니다. 아래는 주요 기능 및 사용법에 대한 설명입니다.

---

## 주요 기능
1. **보안 관련 뉴스 크롤링**
   - `dailysecu_crawling`: 데일리시큐 RSS 피드에서 보안 뉴스를 가져옵니다.
   - `securityNotice_crawling`: KRCERT RSS 피드에서 보안 공지를 가져옵니다.
   - `boanNews_crawling`: 보안뉴스 RSS 피드에서 데이터를 가져옵니다.
   - `crawl_ncsc_page`: NCSC(국가사이버안보센터) 웹사이트에서 최신 게시물을 가져옵니다.

2. **Notion 데이터베이스 연동**
   - 크롤링한 데이터를 Notion API를 통해 데이터베이스에 저장합니다.
   - `create_notion_page` 함수는 제목, 내용, URL, 날짜, 카테고리 정보를 기반으로 Notion 페이지를 생성합니다.

3. **중복 방지**
   - `Duplicate_check` 함수는 URL을 기준으로 데이터베이스에 중복된 항목이 있는지 확인합니다.

4. **오래된 항목 삭제**
   - `delete_old_entries` 함수는 90일 이전의 데이터를 Notion에서 삭제합니다.

5. **스케줄링**
   - `schedule` 라이브러리를 사용하여 1시간마다 크롤링 및 데이터를 업데이트합니다.

---

## 파일의 주요 구성
### 1. **라이브러리**
   - 주요 사용 라이브러리:
     - `requests`: HTTP 요청 처리.
     - `schedule`: 작업 스케줄링.
     - `BeautifulSoup`: HTML 파싱.
     - `selenium`: 동적 웹 페이지 처리.
     - `urllib`: RSS 피드 데이터 처리.
     - `xml.etree.ElementTree`: XML 데이터 파싱.
     - `datetime`: 날짜 및 시간 처리.
     - `json`: JSON 데이터 처리.

### 2. **환경 설정**
   - **SSL 인증서 검증 비활성화**: `ssl.create_default_context`로 HTTPS 인증 문제를 방지.
   - **Notion API 정보**: `NOTION_API_TOKEN` 및 `DATABASE_ID`를 통해 API와 데이터베이스 연동.

### 3. **주요 함수**
#### (1) 크롤링 함수
- `dailysecu_crawling`: 데일리시큐 RSS 피드에서 제목, URL, 내용, 날짜 정보를 가져와 Notion에 저장.
- `securityNotice_crawling`: KRCERT RSS 피드를 통해 공지사항 데이터 저장.
- `boanNews_crawling`: 보안뉴스의 RSS 데이터를 저장.
- `crawl_ncsc_page`: Selenium을 사용해 NCSC 웹사이트에서 게시물을 크롤링.

#### (2) Notion 데이터 처리
- `create_notion_page`: 크롤링한 데이터를 Notion 페이지로 생성.
- `Duplicate_check`: URL 중복 여부 확인.
- `delete_old_entries`: 90일 이전의 데이터를 Notion에서 삭제.

#### (3) 기타 함수
- `date_re`: 다양한 날짜 형식을 `YYYY-MM-DD`로 변환.

---

## 실행 방법
1. **사전 준비**
   - Python 환경에 필요한 라이브러리 설치:
     ```bash
     pip install requests schedule selenium beautifulsoup4 webdriver-manager
     ```
   - Selenium 실행을 위한 ChromeDriver 설치:
     ```bash
     pip install webdriver-manager
     ```

2. **환경 변수 설정**
   - 스크립트 내 `NOTION_API_TOKEN`과 `DATABASE_ID`에 적절한 값을 입력.

3. **스크립트 실행**
   - 실행 시, 즉시 크롤링 작업이 시작됩니다:
     ```bash
     python script_name.py
     ```

4. **스케줄링**
   - 1시간마다 자동으로 크롤링 및 데이터 업데이트가 수행됩니다.

---

## 예외 처리
- 잘못된 날짜 형식, 연결 오류, API 호출 오류 등에 대해 로그로 표시됩니다.
- 크롤링 중 문제가 발생해도 다른 작업은 계속 수행됩니다.

---

## 데이터 흐름
1. RSS 또는 웹 페이지에서 데이터를 가져옵니다.
2. 중복 여부를 확인합니다.
3. Notion 데이터베이스에 새 데이터를 추가하거나 오래된 데이터를 삭제합니다.

---

## 활용 시 주의 사항
- 크롤링 대상 웹사이트에서의 과도한 요청을 방지하기 위해 `time.sleep`으로 대기 시간을 설정했습니다.
- Notion API 호출 횟수 제한을 준수하세요.
- SSL 인증이 비활성화되어 있으므로, 중요한 데이터에는 사용하지 않는 것이 좋습니다.

---

이 스크립트는 보안 정보를 효율적으로 관리하고 자동화하는 데 적합하며, Notion API를 활용한 데이터베이스와의 통합을 통해 생산성을 높일 수 있습니다.
