import os
import logging
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

def check_website_with_selenium_headless(url):
    options = Options()
    options.add_argument("--headless")
    redirect_flag = False
    current_url = url
    result = ''

    # URL에 "http"가 포함되지 않으면 바로 리턴 (예: 접속불가)
    if "http" not in url:
        return redirect_flag, 'X', url

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        title = driver.title
        current_url = driver.current_url
        driver.quit()

        redirect_flag = url != current_url

        if title:
            log_url_check(url, title, current_url)
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

def main():
    global worksheet
    load_dotenv()

    #Google API 연결 정보
    json_keyfile_path = os.getenv("KEYFILE_PATH")
    spreadsheet_id = os.getenv("SHEET_ID")

    sheet = sheet_processor.connect_to_gsheet(json_keyfile_path, spreadsheet_id)
    worksheet = sheet.get_worksheet(2)
    rows = worksheet.get_all_values()
    results = []

    for i in range(1, len(rows)):
        updated_row = []
        row = rows[i]
        url = row[4]
        redirect_flag, result, redirect_url = check_website_with_selenium_headless(url)
        
        if(redirect_flag):
            updated_row = [
                row[0],           # 1번째 열 (연번)
                result,           # 2번째 열 (활성화 여부-국내)
                row[2],           # 3번째 열 (활성화 여부-국외)
                row[3],           # 4번째 열 (이름)
                redirect_url,     # 5번째 열 (찾아낸 신규 URL)
                url,              # 6번째 열 (이전의 URL)
            ]
        else:         
            updated_row = [
                row[0],           # 1번째 열 (연번)
                result,           # 2번째 열 (활성화 여부-국내)
                row[2],           # 3번째 열 (활성화 여부-국외)
                row[3],           # 4번째 열 (이름)
                url,              # 5번째 열 (원래 URL 유지)
                row[5],           # 6번째 열 (이전의 URL)
            ]

        results.append(updated_row)
    worksheet.update(results, f'A2:F{len(rows)}')

if __name__ == "__main__":
    main()