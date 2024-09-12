import time
import random
import os
import requests
from dotenv import load_dotenv
import sheet_processor

load_dotenv()

json_keyfile_path = os.getenv("KEYFILE_PATH")
spreadsheet_id = os.getenv("TWITTER_SHEET_ID")
bearer_token = os.getenv("BEARER_TOKEN")

def check_user_status(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    
    response = requests.get(url, headers=headers)
    response_content = response.json()

    remaining_requests = response.headers.get('x-rate-limit-remaining')
    reset_time = response.headers.get('x-rate-limit-reset')

    print(f"Remaining requests: {remaining_requests}")
    print(f"Rate limit resets at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(reset_time)))}")
    print(response_content)

    # "Too Many Requests" 처리
    if response_content.get("title") == "Too Many Requests":
        return ""  
    
    # "errors" 처리
    errors = response_content.get("errors", [])
    for error in errors:
        detail = error.get("detail", "")
        if "suspended" in detail:
            return ['미유통', '정지']
        if "find" in detail:
            return ['미유통', '삭제']
    
    # errors가 없는 경우
    return ['유통', '해당없음']

if __name__ == "__main__":
    
    sheet = sheet_processor.connect_to_gsheet(json_keyfile_path, spreadsheet_id)
    worksheet = sheet.get_worksheet(0)
    user_list = worksheet.get_all_values()
    
    need_to_check_user_rows = []
    for index, user in enumerate(user_list):
        user_account = user[2]
        user_check_result = user[4]

        if not user_check_result: 
            check_result = check_user_status(user_account)
            need_to_check_user_rows.append(user_account)

            if isinstance(check_result, list) and len(check_result) >= 2:
                worksheet.update_cell(index + 1, 5, check_result[0])  # E열 (5번째 열)에 첫 번째 값 ("미유통")을 업데이트
                worksheet.update_cell(index + 1, 6, check_result[1])  # F열 (6번째 열)에 두 번째 값 ("정지")를 업데이트
            else:
                print("API limit reached")
                break

            time_delay = random.uniform(3, 10)
            print(f"Delaying for {time_delay:.2f} seconds...")
            time.sleep(time_delay)

        if len(need_to_check_user_rows) == 3:
            break
