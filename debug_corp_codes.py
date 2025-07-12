import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def debug_corp_codes():
    api_key = os.getenv('OPENDART_API_KEY')
    if not api_key:
        print("API 키를 찾을 수 없습니다.")
        return
    
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {
        'crtfc_key': api_key
    }
    
    print("API 요청 중...")
    response = requests.get(url, params=params)
    
    print(f"상태 코드: {response.status_code}")
    print(f"응답 헤더: {response.headers}")
    print(f"응답 내용 (처음 500자): {response.text[:500]}")
    
    if response.status_code == 200:
        # 파일로 저장해서 확인
        with open('corp_codes_response.xml', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("응답이 corp_codes_response.xml 파일에 저장되었습니다.")

if __name__ == "__main__":
    debug_corp_codes() 