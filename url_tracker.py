import re 
import os
import sys
import logging
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
import sheet_processor
import website_checker

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filename='url_tracking_result.log',
    filemode='a'
)

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

        target_domain = domain_parts[0]
        if domain_parts[0] == 'www':
            target_domain = domain_parts[1]
        target_domain = target_domain + '1'

        if domain_parts[0] == 'www':
            domain_parts[1] = target_domain  # www가 있는 경우
        else:
            domain_parts[0] = target_domain  # www가 없는 경우

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

def get_failed_result_row(worksheet):
    rows = worksheet.get_values('A:F')
    # 2번째 열 값이 'X'인 행과 그 행 번호를 함께 저장
    filtered_rows_with_index = [(i + 1, row) for i, row in enumerate(rows) if row[1] == 'X'] 
    return filtered_rows_with_index

# 변경후 url 별도 로깅
def log_url_change(original_url, new_url):
    if original_url != new_url:
        log_message = f"Original URL: {original_url} | New URL: {new_url} | Checked at: {datetime.now()}"
        logging.info(log_message)
        print(log_message)  # 콘솔에도 출력

# 실패한 웹사이트들 숫자 올려보며 재실행
def retry_failed_website(sheet_number):
    global worksheet
    load_dotenv()

    #Google API 연결 정보
    json_keyfile_path = os.getenv("KEYFILE_PATH")
    spreadsheet_id = os.getenv("SHEET_ID")

    sheet = sheet_processor.connect_to_gsheet(json_keyfile_path, spreadsheet_id)
    worksheet = sheet.get_worksheet(sheet_number)
    filtered_rows = get_failed_result_row(worksheet)
    results = []

    for row_num, row in filtered_rows:
        updated_row = []
        original_url = row[4]
        trial_url = original_url
        
        if "http" not in original_url:
            continue
        for attempt in range(5):  # 최대 5회 시도
            result = 'X'
            trial_url = create_url_by_increasing_number(trial_url)
            print(f"Trying URL: {trial_url}")
            redirect_flag, result, redirect_url = website_checker.check_website_with_selenium_headless(trial_url, row[3])
            if result == 'O':
                final_url = redirect_url if redirect_flag else trial_url
                updated_row = [
                    row[0],        # 1번째 열 (연번)
                    result,        # 2번째 열 (활성화 여부-국내)
                    row[2],        # 3번째 열 (활성화 여부-국외)
                    row[3],        # 4번째 열 (이름)
                    final_url,     # 5번째 열 (redirect_url 또는 trial_url)
                    original_url   # 6번째 열 (이전의 URL)
                ]
                results.append((row_num, updated_row))
                break

    for row_num, updated_row in results:
        cell_range = f'A{row_num}:F{row_num}'  # 해당 row_num에 있는 A~F 열 범위 지정
        worksheet.update([updated_row], cell_range)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: 웹사이트를 검사할 Google Sheet가 몇 번째 시트인지 알려주세요.")
        print("사용 예(첫 번째 Sheet인 경우): python url_tracker.py 1")
        sys.exit(1) 
    try:
        sheet_number = int(sys.argv[1])-1
        retry_failed_website(sheet_number)
    except ValueError:
        print("Error: Sheet 순서는 숫자로만 넣어주셔야 합니다")
        sys.exit(1)
