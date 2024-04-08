# -*- coding: utf-8 -*-

import requests
import json
import schedule
import time
import urllib.request
import xml.etree.ElementTree as ET
import re
import ssl
import datetime


# SSL 인증서 검증 비활성화
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Notion API 토큰
NOTION_API_TOKEN = "secret_wrCl4doJA9dLvLvhvr9F0fkAY5G481amKbb9jHwSTld"

# 데이터베이스 ID
DATABASE_ID = "18aa4d68041448779c2513b29c3a930a"

# Notion 페이지 생성 함수
def create_notion_page(title, content, url, date, category_):
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
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
                "rich_text": [
                    {
                        "text": {
                            "content": date
                            }
                    }
                ]
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

def date_re(date_string):
    try:
        # 1. +0900 형식의 문자열
        date_object = datetime.datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        # 2. GMT 형식의 문자열
        date_object = datetime.datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")
    print("날짜 출력",date_object,"///"+date_object.strftime('%Y-%m-%d'))
    return date_object.strftime('%Y-%m-%d')


def securityNotice_crawling():
    print("")
    print("")
    print("---------------------------------------------------")
    print("------------securityNotice_crawling 실행------------")
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
        category_ = "보안공지"
        if Duplicate_check(title) == 1:
            print("이미 있는 공지")
        else:
            try:
                create_notion_page(title, content, url, date, category_)
            except:
                pass

def boanNews_crawling():
    print("")
    print("")
    print("---------------------------------------------")
    print("------------boanNews_crawling 실행------------")
    url = 'http://www.boannews.com/media/news_rss.xml?skind=5'
    response = requests.get(url)
    response.encoding = response.apparent_encoding  # 데이터의 인코딩 방식을 자동으로 인식하여 설정

    s = response.text
    root = ET.fromstring(s)
    channel = root[0]
    items = filter(lambda x: x.tag == 'item', channel)

    for item in items:
        title = item[0].text.strip()
        url = item[1].text
        content = item[2].text
        date = date_re(item[4].text)
        category_ = "보안뉴스"
        if Duplicate_check(title) == 1:
            print("이미 있는 뉴스")
        else:
            try:
                create_notion_page(title, content, url, date, category_)
            except:
                pass

  
def Duplicate_check(title_to_check):
    # 데이터베이스 쿼리를 위한 엔드포인트 설정
    endpoint = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    # HTTP 요청 헤더 설정
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2021-05-13"
    }

    # 데이터베이스 쿼리를 실행하여 응답 받기
    response = requests.post(endpoint, headers=headers)

    # 응답 데이터 확인
    if response.status_code == 200:
        data = response.json()
        # 데이터베이스 내의 모든 항목을 확인하여 제목 비교
        for item in data["results"]:
            # 데이터베이스 내의 항목 제목과 비교하여 중복 여부 확인
            if item["properties"]["title"]["title"][0]["text"]["content"] == title_to_check:
                print(f"'{title_to_check}' 제목은 데이터베이스에 이미 존재합니다.")
                return 1  # 중복된 경우 1 반환
        print(f"'{title_to_check}' 제목은 데이터베이스에 존재하지 않습니다.")
        return 0  # 중복되지 않은 경우 0 반환

def start(): 
    now = datetime.datetime.now()
    print(f"{now}: 루프 시작")
    securityNotice_crawling()
    time.sleep(1)
    boanNews_crawling()
    time.sleep(1)
    now = datetime.datetime.now()
    print(f"{now}: 루프 끝")
    print("")

securityNotice_crawling()
time.sleep(1)
boanNews_crawling()
time.sleep(1)
# 스케줄러 설정: 매일 00:00에 start 함수 실행
schedule.every(30).minutes.do(start)


# 스케줄러 루프 실행
while True:
    schedule.run_pending()
    time.sleep(1)