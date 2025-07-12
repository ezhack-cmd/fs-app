import os
import requests
import zipfile
import io
import sqlite3
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# OpenDart API 키
API_KEY = os.getenv('OPENDART_API_KEY')
if not API_KEY:
    raise ValueError("OPENDART_API_KEY not found in environment variables")

def download_corp_codes():
    """회사코드(고유번호) 다운로드"""
    print("OpenDART에서 회사 코드 다운로드 중...")
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

def create_database():
    """회사 코드 데이터베이스 생성"""
    print("SQLite 데이터베이스 생성 중...")
    
    # 데이터베이스 연결
    conn = sqlite3.connect('corp_codes.db')
    cursor = conn.cursor()
    
    # 테이블 생성 (이미 존재하면 삭제)
    cursor.execute('DROP TABLE IF EXISTS companies')
    cursor.execute('''
    CREATE TABLE companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        corp_code TEXT NOT NULL,
        corp_name TEXT NOT NULL,
        stock_code TEXT,
        modify_date TEXT
    )
    ''')
    
    # 인덱스 생성
    cursor.execute('CREATE INDEX idx_corp_name ON companies (corp_name)')
    cursor.execute('CREATE INDEX idx_corp_code ON companies (corp_code)')
    cursor.execute('CREATE INDEX idx_stock_code ON companies (stock_code)')
    
    # 회사 코드 다운로드
    companies = download_corp_codes()
    
    # 데이터 삽입
    print(f"데이터베이스에 {len(companies)}개 회사 정보 삽입 중...")
    for company in companies:
        cursor.execute(
            'INSERT INTO companies (corp_code, corp_name, stock_code, modify_date) VALUES (?, ?, ?, ?)',
            (
                company['corp_code'],
                company['corp_name'],
                company['stock_code'],
                company['modify_date']
            )
        )
    
    # 변경사항 저장
    conn.commit()
    
    # 연결 종료
    conn.close()
    
    print("데이터베이스 생성 완료!")

if __name__ == "__main__":
    create_database() 