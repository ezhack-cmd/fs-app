import os
import requests
import zipfile
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OpenDartClient:
    def __init__(self):
        self.api_key = os.getenv('OPENDART_API_KEY')
        if not self.api_key:
            raise ValueError("OPENDART_API_KEY not found in environment variables")
        
        self.base_url = "https://opendart.fss.or.kr/api"
    
    def get_company_info(self, corp_code):
        """기업 정보 조회"""
        url = f"{self.base_url}/company.json"
        params = {
            'crtfc_key': self.api_key,
            'corp_code': corp_code
        }
        
        response = requests.get(url, params=params)
        return response.json()
    
    def get_financial_info(self, corp_code, year, report_code):
        """재무정보 조회"""
        url = f"{self.base_url}/fnlttSinglAcnt.json"
        params = {
            'crtfc_key': self.api_key,
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': report_code
        }
        
        response = requests.get(url, params=params)
        return response.json()
    
    def download_corp_codes(self):
        """회사코드(고유번호) 다운로드"""
        url = f"{self.base_url}/corpCode.xml"
        params = {
            'crtfc_key': self.api_key
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
                            company_info = {
                                'corp_code': corp.find('corp_code').text if corp.find('corp_code') is not None else '',
                                'corp_name': corp.find('corp_name').text if corp.find('corp_name') is not None else '',
                                'stock_code': corp.find('stock_code').text if corp.find('stock_code') is not None else '',
                                'modify_date': corp.find('modify_date').text if corp.find('modify_date') is not None else ''
                            }
                            companies.append(company_info)
                        
                        return companies
                    else:
                        raise Exception("ZIP 파일에서 XML 파일을 찾을 수 없습니다.")
            except zipfile.BadZipFile:
                raise Exception("응답이 유효한 ZIP 파일이 아닙니다.")
        else:
            raise Exception(f"Failed to download corp codes: {response.status_code}")
    
    def save_corp_codes_to_csv(self, filename='corp_codes.csv'):
        """회사코드를 CSV 파일로 저장"""
        import csv
        
        companies = self.download_corp_codes()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['corp_code', 'corp_name', 'stock_code', 'modify_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for company in companies:
                writer.writerow(company)
        
        print(f"회사코드가 {filename}에 저장되었습니다. (총 {len(companies)}개 회사)")
        return filename

def main():
    try:
        # OpenDart 클라이언트 초기화
        client = OpenDartClient()
        print("OpenDart API 클라이언트가 성공적으로 초기화되었습니다.")
        
        # 회사코드 다운로드 및 CSV 저장
        print("회사코드를 다운로드 중...")
        csv_file = client.save_corp_codes_to_csv()
        
        # 사용 예시 (실제 corp_code는 OpenDart에서 제공하는 코드를 사용해야 함)
        # company_info = client.get_company_info("00126380")
        # print(company_info)
        
    except ValueError as e:
        print(f"오류: {e}")
        print("환경 변수 파일(.env)에 OPENDART_API_KEY를 설정해주세요.")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")

if __name__ == "__main__":
    main() 