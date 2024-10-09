import os
import re
import logging
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from datetime import datetime 
from dotenv import load_dotenv
import sheet_processor

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename='url_check_result.log',
    filemode='a'
)

def check_website_with_selenium_headless(url, title):
    options = Options()
    options.add_argument("--headless")    
    options.add_argument("--ignore-certificate-errors")  # SSL 인증서 오류 무시
    options.add_argument("--allow-insecure-localhost")  # 로컬 SSL 오류 무시
    options.add_argument("--disable-web-security")  # 웹 보안 비활성화
    
    redirect_flag = False
    current_url = url
    result = ''

    # 검사할 타이틀 키워드
    # 괄호를 기준으로 분리하여 괄호 밖과 괄호 안의 내용 모두 추출 ex: 오피스타(레플리카2)
    title_list = ['유흥', '성매매', '오피', '출장', '안마', '마사지', '키스', '잠시만']
    titles = re.findall(r'\w+', title)
    title_list.extend(titles)

    # 통신사에서 차단된 페이지
    block_list = ['warning.or.kr', 'uplus.co.kr', 'skbroadband.com']

    # URL에 "http"가 포함되지 않으면 바로 리턴 (예: 접속불가)
    if "http" not in url:
        return redirect_flag, 'X', url

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(10)
        driver.get(url)

        site_title = driver.title
        current_url = driver.current_url
        driver.quit()

        # 리다이렉트된 URL이 공식 차단 페이지가 아니라면 
        if not any(block in current_url for block in block_list):
            redirect_flag = url != current_url

        # 타이틀 키워드 가운데 하나라도 사이트에 포함되어 있다면
        if any(word in site_title for word in title_list):  
            log_url_check(url, site_title, current_url)
            result = 'O'
        else:
            result = 'X'

        
    except (WebDriverException, TimeoutException) as e:
        result = 'X'
        current_url = url 

    finally:
        try:
            driver.quit()
        except:
            pass
    
    return redirect_flag, result, current_url

#check url 로깅
def log_url_check(url, title, current_url):
    redirect_flag = False
    if(url != current_url):
        redirect_flag = True
    log_message = f"Redirect: {redirect_flag} | Original URL: {url} | Site Title: {title} | Current Url: {current_url} | Checked at: {datetime.now()}"
    logging.info(log_message)
    print(log_message)


def main(sheet_number):
    global worksheet
    load_dotenv()

    #Google API 연결 정보
    json_keyfile_path = os.getenv("KEYFILE_PATH")
    spreadsheet_id = os.getenv("SHEET_ID")

    sheet = sheet_processor.connect_to_gsheet(json_keyfile_path, spreadsheet_id)
    worksheet = sheet.get_worksheet(sheet_number)

    sheet_processor.insert_column_after_last_but_one(sheet, worksheet.id)

    rows = worksheet.get_values('A:F')
    results = []

    for i in range(1, len(rows)):
        row = rows[i]
        url = row[4]
        title = row[3]
        redirect_flag, result, redirect_url = check_website_with_selenium_headless(url, title)       
        updated_row = [
            row[0],           # 1번째 열 (연번)
            result,           # 2번째 열 (활성화 여부-국내)
            row[2],           # 3번째 열 (활성화 여부-국외)
            title,           # 4번째 열 (이름)
        ]

        if(redirect_flag):
            updated_row.extend([redirect_url, url])  # 5번째: 새 URL, 6번째: 이전 URL
        else:         
            updated_row.extend([url, row[5]]) # 5번째: 원래 URL, 6번째: 이전 URL

        results.append(updated_row)
    worksheet.update(results, f'A2:F{len(rows)}')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: 웹사이트를 검사할 Google Sheet가 몇 번째 시트인지 알려주세요.")
        print("사용 예(첫 번째 Sheet인 경우): python website_checker.py 1")
        sys.exit(1)  
    try:
        sheet_number = int(sys.argv[1])
        main(sheet_number - 1)
    except ValueError:
        print("Error: Sheet 순서는 숫자로만 넣어주셔야 합니다")
        sys.exit(1)
