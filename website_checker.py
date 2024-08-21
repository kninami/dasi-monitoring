import sheet_processor
import requests
import re 
import os
import logging
from urllib.parse import urlparse, urlunparse
from datetime import datetime 
from dotenv import load_dotenv

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename='url_changes.log',
    filemode='a'
)

# 웹사이트 살아있는지 여부 체크
def check_website_status(url):
    try:
        response = requests.get(url, timeout=5)  # 5초 타임아웃 설정
        if response.status_code == 200:
            return 'O'
        else:
            return 'X'
    except requests.RequestException:
        return 'X'

# URL 내의 숫자를 증가시키는 함수
def create_url_by_increasing_number(url):
    if not isinstance(url, str):
        return None  # url이 None이거나 문자열이 아닌 경우 None 반환
    
    match = re.search(r'(\d+)', url)
    if match:
        number = int(match.group(0))
        new_number = number + 1
        trial_url = url.replace(match.group(0), str(new_number).zfill(len(match.group(0))))
    else:
        # URL에 숫자가 포함되지 않은 경우, 도메인 이름 부분에 숫자를 추가 (예: lonelynight -> lonelynight1)
        parsed_url = urlparse(url)
        domain_parts = parsed_url.netloc.split('.')
        domain_parts[0] = domain_parts[0] + '1'
        new_domain = '.'.join(domain_parts)
        
        trial_url = urlunparse((
            parsed_url.scheme,
            new_domain,
            parsed_url.path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment
        ))
    return trial_url

# 변경후 url 별도 로깅
def log_url_change(original_url, new_url):
    if original_url != new_url:
        log_message = f"Original URL: {original_url} | New URL: {new_url} | Checked at: {datetime.now()}"
        logging.info(log_message)
        print(log_message)  # 콘솔에도 출력


# 실패한 요청 재시도
def retry_failed_requests(worksheet, data):
    for i in range(1, len(data)):
        original_url = data[i][3]
        trial_url = data[i][3]
        result = data[i][4]

        if result != "O":
            success = False
            for attempt in range(5):  # 최대 5회 시도
                trial_url = create_url_by_increasing_number(trial_url)
                print(f"Trying URL: {trial_url}")

                if not trial_url:
                    continue

                if check_website_status(trial_url) == 'O':
                    worksheet.update_cell(i + 1, 3, trial_url)  # 새로운 URL 저장 (Google worksheets의 열 번호는 1부터 시작)
                    worksheet.update_cell(i + 1, 5, 'O')
                    log_url_change(original_url, trial_url) #변경전후 url을 로그에 기록
                    success = True
                    break

            if not success:
                worksheet.update_cell(i + 1, 5, 'X')  # 5회 시도 후에도 실패하면 'X'로 표시

def main():
    load_dotenv()
    #Google API 연결 정보
    json_keyfile_path = os.getenv("KEYFILE_PATH")
    spreadsheet_id = os.getenv("SHEET_ID")

    sheet = sheet_processor.connect_to_gsheet(json_keyfile_path, spreadsheet_id)
    worksheet = sheet.sheet1
    urls = worksheet.col_values(4)  # 4번째 컬럼의 모든 값 가져오기
    
    for i in range(1, len(urls)):
        url = urls[i]
        status = check_website_status(url)
        worksheet.update_cell(i + 1, 5, status)  # 5번째 컬럼에 결과 기록 (i + 1은 헤더가 있으므로)

    # 다시 저장된 모든 데이터를 시트에서 가져와서 실패한 것들 URL 바꿔가며 retry 
    data = sheet_processor.get_data_from_sheet(sheet)
    retry_failed_requests(worksheet, data)

main()