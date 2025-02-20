# -*- coding: utf-8 -*-
import requests
import json
import schedule
import time
import urllib.request
import xml.etree.ElementTree as ET
import re
import os
import ssl
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from google import genai


# SSL 인증서 검증 비활성화
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Gemini API 키 설정
GEMINI_API_KEY = "GEMINI_API_KEY"  # 여기에 실제 API 키를 넣으세요.



# Notion API 토큰 및 데이터베이스 ID
NOTION_API_TOKEN = "NOTION_API_TOKEN"
DATABASE_ID = "DATABASE_ID"

# 슬랙 Webhook URL
SLACK_WEBHOOK_URL = "SLACK_WEBHOOK_URL"  # 여기에 슬랙 Webhook URL을 넣으세요.

def send_slack_message(message):
    """슬랙으로 메시지 보내기"""
    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        print("슬랙 메시지 전송 성공!")
    except requests.exceptions.RequestException as e:
        print(f"슬랙 메시지 전송 실패: {e}")

def summarize_text(text):
    try:
        # Gemini 클라이언트 생성
        client = genai.Client(api_key=GEMINI_API_KEY)

        # 텍스트 요약 요청
        response = client.models.generate_content(
            model="gemini-pro",  # 또는 "gemini-2.0-flash"와 같은 다른 Gemini 모델
            contents=[f"""
너는 뉴스 요약 Assistant입니다.
\n뉴스 텍스트를 제시하겠습니다. 텍스트를 참고하여, 주제를 다른 사람이 이해할 수 있게 설명하는 역할을 합니다.
\n우선 단계별로 생각하세요. 뉴스에 내용을 어떻게 요약하여 전달할지 생각합니다.
\n중복되는 내용은 생략하되, 중복되는 내용의 요약 비중을 높입니다.
\n사례보다는 개념과 논거를 강조하여 요약하세요.
\n단락에는 친근한 어투를 사용하세요, 너무 어렵거나 전문적인 용어만 사용하지 마세요. 가급적 능동태를 이용하세요, 수동태를 이용하지마세요.
\n문제나 도전에 직면했을 때 긍정적인 상황으로 전환하려는 태도를 보이세요, 거리감을 만들어내는 공식적이거나 냉담한 어투를 피하세요.
\n300글자 이내로 요약하세요:
\n뉴스본문:\n{text}"""]
        )


        # 응답에서 요약된 텍스트 추출
        if response.candidates:
            best_candidate = response.candidates[0]  # 첫 번째 후보 선택

            if hasattr(best_candidate, "content") and hasattr(best_candidate.content, "parts"):
                summary = "".join(part.text for part in best_candidate.content.parts if hasattr(part, "text"))
                return summary.strip() if summary else "요약 실패 (내용 없음)"
            else:
                print("Gemini API: No valid content found in candidate")
                return "요약 실패 (유효한 내용 없음)"

        else:
            print("Gemini API: No candidates returned")
            return "요약 실패 (후보 없음)"

    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return "요약 실패"



def create_notion_page(title, content, url, date, category_):
    # 현재 날짜와 비교
    try:
        today = datetime.datetime.now()
        post_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        # 90일 이전 날짜인지 확인
        if post_date < (today - datetime.timedelta(days=90)):
            print(f"[SKIP] {title}은(는) 90일 이전의 항목이므로 추가하지 않습니다.")
            return
    except ValueError as e:
        print(f"[ERROR] 날짜 형식 오류: {date} - {e}")
        return

    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # content 길이 제한
    if len(content) > 2000:
        content = content[:1990] + '...(생략)'

    data = {
        "parent": {
            "database_id": DATABASE_ID
        },
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "content": {
                "rich_text": [
                    {
                        "text": {
                            "content": content
                        }
                    }
                ]
            },
            "url": {
                "url": url
            },
            "date": {
                "date": {
                    "start": date  # Assuming 'date' is already in 'YYYY-MM-DD' format
                }
            },
            "category": {
                "select": {
                    "name": category_
                }
            }
        }
    }

    response = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data), verify=True)

    if response.status_code == 200:
        print("노션 페이지가 성공적으로 생성되었습니다.")
    else:
        print(f"에러 발생: {response.status_code} - {response.text}")
        send_slack_message(f"[ERROR] 에러 발생: {response.status_code} - {response.text}")

# 중복 확인 함수 (URL 기반)
def Duplicate_check(url_to_check):
    endpoint = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2021-05-13"
    }
    response = requests.post(endpoint, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for item in data["results"]:
            # URL 속성을 기준으로 중복 확인
            if item["properties"]["url"]["url"].strip() == url_to_check.strip():
                return 1  # 중복된 경우
        return 0  # 중복되지 않은 경우
    return 0

# 날짜 포맷 변환 함수
def date_re(date_string):
    try:
        # 기존 RFC 822 형식 처리
        date_object = datetime.datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        try:
            date_object = datetime.datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            try:
                # NCSC 형식 처리 (2024.10.16 같은 형식)
                date_object = datetime.datetime.strptime(date_string, "%Y.%m.%d")
            except ValueError:
                try:
                    # 데일리시큐의 날짜 형식 처리 (2024-12-20 11:29:05)
                    date_object = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # 처리할 수 없는 형식일 경우 예외 처리
                    print(f"알 수 없는 날짜 형식: {date_string}")
                    return None
    return date_object.strftime('%Y-%m-%d')


def crawl_ncsc_page():
    try:
        options = Options()
        options.add_argument('--headless')  # 헤드리스 모드 (선택 사항)
        options.add_argument('--no-sandbox')  # sandbox 비활성화 (필요한 경우)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.get("https://www.ncsc.go.kr:4018")
        driver.execute_script("goSubMenuPage('020000','020200')")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        board_list_table = soup.find('table', class_='board_list')

        if not board_list_table:
            print("게시판 테이블을 찾을 수 없습니다.")
            return

        tr_tags = board_list_table.find('tbody').find_all('tr')
        for tr_tag in tr_tags:
            td_tags = tr_tag.find_all('td')
            number = td_tags[0].text.strip()  # 수정: td_tags[0].text로 처리
            a_tag = td_tags[1].find('a')

            if a_tag:
                driver.execute_script(a_tag['onclick'])
                time.sleep(2)
                link = driver.current_url
                title = a_tag.text.strip()
                posting_date = td_tags[2].text.strip()  # 수정: td_tags[2].text로 처리
                posting_date = date_re(posting_date)  # 형식 변환

                if Duplicate_check(link) == 0:
                    create_notion_page(title, "NCSC 게시글", link, posting_date, "NCSC")
                driver.back()
                time.sleep(2)
        driver.close()
    except Exception as e:
        print(f"NCSC 크롤링 중 오류 발생: {e}")
        send_slack_message(f"[ERROR] NCSC 크롤링 중 오류 발생: {e}")



# 기존 보안 공지 크롤링
def securityNotice_crawling():
    try:
        url = 'http://knvd.krcert.or.kr/rss/securityNotice.do'
        with urllib.request.urlopen(url, context=ssl_context) as f:
            s = f.read().decode('utf-8')
        root = ET.fromstring(s)
        channel = root[0]
        items = filter(lambda x: x.tag == 'item', channel)

        for item in items:
            title = item[0].text.strip()
            url = item[1].text
            content = item[2].text
            date = date_re(item[4].text)
            category_ = "krcert"
            if Duplicate_check(url) == 0:
                summarized_content = summarize_text(content)
                create_notion_page(title, summarized_content, url, date, category_)
    except Exception as e:
        print(f"securityNotice 크롤링 중 오류 발생: {e}")
        send_slack_message(f"[ERROR] securityNotice 크롤링 중 오류 발생: {e}")

# 기존 보안 뉴스 크롤링
def boanNews_crawling():
    try:
        # RSS URL 리스트
        urls = [
            'http://www.boannews.com/media/news_rss.xml?skind=5',  # 필터링 없음
            'http://www.boannews.com/media/news_rss.xml?skind=6',  # 필터링 없음
            'http://www.boannews.com/media/news_rss.xml?mkind=1'  # [긴급] 필터링
        ]

        for rss_url in urls:
            response = requests.get(rss_url)
            response.encoding = response.apparent_encoding
            root = ET.fromstring(response.text)
            channel = root[0]
            items = filter(lambda x: x.tag == 'item', channel)

            for item in items:
                title = item[0].text.strip()
                url = item[1].text
                content = item[2].text
                date = date_re(item[4].text)
                category_ = "보안뉴스"

                # 특정 URL에만 [긴급] 필터링 적용
                if rss_url == 'http://www.boannews.com/media/news_rss.xml?mkind=1' and "[긴급]" not in title:
                    continue

                if Duplicate_check(url) == 0:
                    summarized_content = summarize_text(content)
                    create_notion_page(title, summarized_content, url, date, category_)
    except Exception as e:
        print(f"boanNews 크롤링 중 오류 발생: {e}")
        send_slack_message(f"[ERROR] boanNews 크롤링 중 오류 발생: {e}")



# 데일리시큐 크롤링 함수
def dailysecu_crawling():
    try:
        url = 'https://www.dailysecu.com/rss/S1N2.xml'
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        root = ET.fromstring(response.text)
        channel = root[0]
        items = filter(lambda x: x.tag == 'item', channel)

        for item in items:
            title = item[0].text.strip()
            url = item[1].text
            content = item[2].text
            date = date_re(item[4].text)  # pubDate 처리
            category_ = "데일리시큐"
            if Duplicate_check(url) == 0:
                summarized_content = summarize_text(content)
                create_notion_page(title, summarized_content, url, date, category_)
    except Exception as e:
        print(f"dailysecu 크롤링 중 오류 발생: {e}")
        send_slack_message(f"[ERROR] dailysecu 크롤링 중 오류 발생: {e}")


# 오래된 항목 삭제 함수
def delete_old_entries():
    endpoint = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # API 버전 확인
    }

    # 오늘 날짜 계산 및 기준일 설정 (90일 이전)
    today = datetime.datetime.now()
    threshold_date = today - datetime.timedelta(days=90)

    # 필터링 데이터를 이용한 조회
    data = {
        "filter": {
            "property": "date",  # 날짜를 저장한 property
            "date": {
                "before": threshold_date.strftime('%Y-%m-%d')  # 기준일보다 이전 날짜
            }
        }
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(data))
        print(f"[DEBUG] Database query response: {response.status_code} - {response.text}")  # 데이터베이스 쿼리 응답 출력

        if response.status_code == 200:
            data = response.json()
            for item in data["results"]:
                try:
                    # 날짜 필드가 있는지 확인
                    if "date" in item["properties"] and item["properties"]["date"]["date"]:
                        date_str = item["properties"]["date"]["date"]["start"]
                        item_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')

                        # 기준일보다 오래된 경우 삭제
                        if item_date < threshold_date:
                            page_id = item["id"]  # 페이지 ID

                            data = {"archived": True}

                            delete_endpoint = f"https://api.notion.com/v1/pages/{page_id}"
                            delete_response = requests.patch(delete_endpoint, headers=headers, data=json.dumps(data))

                            print(f"[DEBUG] Delete request for {page_id}: {delete_response.status_code} - {delete_response.text}")  # 삭제 요청 정보 출력
                            send_slack_message(f"[DEBUG] Delete request for {page_id}: {delete_response.status_code} - {delete_response.text}")
                            if delete_response.status_code == 200:
                                print(f"[DEBUG] 오래된 항목 삭제 완료: {page_id}")
                                send_slack_message(f"[DEBUG] 오래된 항목 삭제 완료: {page_id}")
                            else:
                                print(f"[ERROR] 항목 삭제 실패: {delete_response.status_code} - {delete_response.text}")
                                send_slack_message(f"[ERROR] 항목 삭제 실패: {delete_response.status_code} - {delete_response.text}")


                            time.sleep(1)  # 1초 대기
                    else:
                        print(f"[WARNING] 날짜 정보가 없는 항목: {item['id']}")
                except Exception as e:
                    print(f"[ERROR] 항목 처리 중 오류 발생: {e}")
        else:
            print(f"[ERROR] 데이터베이스 조회 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] 오래된 항목 삭제 중 오류 발생: {e}")


# 스케줄링 함수
def start():
    try:
        print(f"[{datetime.datetime.now()}] 스케쥴링을 시작합니다")
        send_slack_message(f"[DEBUG] 보안이슈 스케쥴링을 시작합니다")
        boanNews_crawling()
        time.sleep(1)
        dailysecu_crawling()
        time.sleep(1)
        securityNotice_crawling()
        time.sleep(1)
        crawl_ncsc_page()
        time.sleep(1)
        delete_old_entries()
        time.sleep(1)
        send_slack_message(f"[DEBUG] 보안이슈 스케쥴링이 끝났습니다.")
    except Exception as e:
        error_message = f"스크립트 실행 중 오류 발생: {e}"
        print(error_message)
        send_slack_message(error_message)

# 스케줄 설정
start()  # 스크립트 실행 시 한 번 실행
schedule.every(1).hours.do(start)

# 루프 실행
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except Exception as e:
    error_message = f"메인 루프 실행 중 오류 발생: {e}"
    print(error_message)
    send_slack_message(error_message)
