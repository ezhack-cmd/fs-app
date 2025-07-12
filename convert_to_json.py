import csv
import json

def convert_csv_to_json():
    """CSV 파일을 JSON으로 변환하여 빠른 검색이 가능하도록 함"""
    
    companies = []
    
    # CSV 파일 읽기
    with open('corp_codes.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            companies.append({
                'corp_code': row['corp_code'],
                'corp_name': row['corp_name'],
                'stock_code': row['stock_code'],
                'modify_date': row['modify_date']
            })
    
    # JSON 파일로 저장
    with open('corpCodes.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(companies, jsonfile, ensure_ascii=False, indent=2)
    
    print(f"총 {len(companies)}개 회사 정보가 corpCodes.json에 저장되었습니다.")
    
    # 검색 테스트
    test_companies = ['삼성전자', 'SK하이닉스', 'LG에너지솔루션']
    for company in test_companies:
        found = [c for c in companies if company in c['corp_name']]
        if found:
            print(f"'{company}' 검색 결과: {len(found)}개 발견")
            for f in found[:3]:  # 처음 3개만 출력
                print(f"  - {f['corp_name']} (코드: {f['corp_code']}, 종목코드: {f['stock_code']})")

if __name__ == "__main__":
    convert_csv_to_json() 