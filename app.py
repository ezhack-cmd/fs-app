from flask import Flask, render_template, request, jsonify
import json
import os
import requests
import zipfile
import io
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

app = Flask(__name__)

# OpenDart API 키
API_KEY = os.getenv('OPENDART_API_KEY')
if not API_KEY:
    raise ValueError("OPENDART_API_KEY not found in environment variables")

# 회사 코드 데이터 로드 또는 생성
def load_or_create_company_codes():
    if os.path.exists('corpCodes.json'):
        with open('corpCodes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print("corpCodes.json 파일이 없습니다. 생성합니다...")
        companies = download_corp_codes()
        with open('corpCodes.json', 'w', encoding='utf-8') as f:
            json.dump(companies, f, ensure_ascii=False, indent=2)
        return companies

def download_corp_codes():
    """회사코드(고유번호) 다운로드"""
    url = f"https://opendart.fss.or.kr/api/corpCode.xml"
    params = {
        'crtfc_key': API_KEY
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        # ZIP 파일로 응답이 오므로 압축 해제
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                # ZIP 파일 내의 XML 파일 읽기
                xml_filename = None
                for filename in zip_file.namelist():
                    if filename.endswith('.xml'):
                        xml_filename = filename
                        break
                
                if xml_filename:
                    with zip_file.open(xml_filename) as xml_file:
                        xml_content = xml_file.read().decode('utf-8')
                    
                    # XML 파싱
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(xml_content)
                    
                    companies = []
                    for corp in root.findall('.//list'):
                        corp_code_elem = corp.find('corp_code')
                        corp_name_elem = corp.find('corp_name')
                        stock_code_elem = corp.find('stock_code')
                        modify_date_elem = corp.find('modify_date')
                        
                        company_info = {
                            'corp_code': corp_code_elem.text if corp_code_elem is not None else '',
                            'corp_name': corp_name_elem.text if corp_name_elem is not None else '',
                            'stock_code': stock_code_elem.text if stock_code_elem is not None else '',
                            'modify_date': modify_date_elem.text if modify_date_elem is not None else ''
                        }
                        companies.append(company_info)
                    
                    return companies
                else:
                    raise Exception("ZIP 파일에서 XML 파일을 찾을 수 없습니다.")
        except zipfile.BadZipFile:
            raise Exception("응답이 유효한 ZIP 파일이 아닙니다.")
    else:
        raise Exception(f"Failed to download corp codes: {response.status_code}")

# 회사 코드 데이터 로드
companies = load_or_create_company_codes()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/search_company')
def search_company():
    """회사명으로 검색"""
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    
    # 회사명에 검색어가 포함된 회사들 찾기
    results = [c for c in companies if query in c['corp_name']]
    
    # 최대 10개만 반환
    return jsonify(results[:10])

@app.route('/get_financial_data')
def get_financial_data():
    """재무제표 데이터 가져오기"""
    corp_code = request.args.get('corp_code', '')
    bsns_year = request.args.get('bsns_year', '2023')
    reprt_code = request.args.get('reprt_code', '11011')  # 기본값: 사업보고서
    
    if not corp_code:
        return jsonify({'error': '회사 코드가 필요합니다.'})
    
    # OpenDart API 호출
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
    params = {
        'crtfc_key': API_KEY,
        'corp_code': corp_code,
        'bsns_year': bsns_year,
        'reprt_code': reprt_code
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return jsonify(data)

if __name__ == '__main__':
    # 개발 환경에서는 디버그 모드로 실행
    # 프로덕션 환경에서는 호스트와 포트를 환경 변수에서 가져옴
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 