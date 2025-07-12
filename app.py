from flask import Flask, render_template, request, jsonify
import json
import os
import requests
import zipfile
import io
import sqlite3
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

app = Flask(__name__)

# 디버그 모드 활성화
app.debug = True

# OpenDart API 키
API_KEY = os.getenv('OPENDART_API_KEY')
if not API_KEY:
    raise ValueError("OPENDART_API_KEY not found in environment variables")

# 데이터베이스 연결 함수
def get_db_connection():
    conn = sqlite3.connect('corp_codes.db')
    conn.row_factory = sqlite3.Row
    return conn

# 데이터베이스 초기화 확인
def init_db_if_needed():
    if not os.path.exists('corp_codes.db'):
        from create_corp_db import create_database
        create_database()

# 애플리케이션 시작 시 데이터베이스 초기화 확인
init_db_if_needed()

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
    
    # 데이터베이스에서 회사명 검색
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 회사명에 검색어가 포함된 회사들 찾기 (최대 10개)
    cursor.execute(
        "SELECT corp_code, corp_name, stock_code, modify_date FROM companies WHERE corp_name LIKE ? LIMIT 10",
        (f'%{query}%',)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'corp_code': row['corp_code'],
            'corp_name': row['corp_name'],
            'stock_code': row['stock_code'],
            'modify_date': row['modify_date']
        })
    
    conn.close()
    return jsonify(results)

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
    
    print(f"OpenDART API 호출: {url} - 파라미터: {params}")
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        print(f"OpenDART API 응답: 상태 코드={response.status_code}, 응답={data.get('status')}, 메시지={data.get('message')}")
        
        # 재무비율 계산 추가
        if data.get('status') == '000' and data.get('list'):
            print(f"재무제표 데이터 개수: {len(data['list'])}")
            data['financial_ratios'] = calculate_financial_ratios(data['list'])
        else:
            print(f"재무제표 데이터 없음: {data}")
            # 빈 데이터 구조 제공
            if 'list' not in data:
                data['list'] = []
            if 'financial_ratios' not in data:
                data['financial_ratios'] = {}
        
        return jsonify(data)
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'list': [],
            'financial_ratios': {}
        })

def calculate_financial_ratios(financial_data):
    """재무비율 계산"""
    ratios = {}
    
    # 필요한 계정 추출
    bs_data = {item['account_nm']: item for item in financial_data if item['sj_div'] == 'BS'}
    is_data = {item['account_nm']: item for item in financial_data if item['sj_div'] == 'IS'}
    
    print(f"재무상태표 계정 수: {len(bs_data)}, 손익계산서 계정 수: {len(is_data)}")
    
    # 당기 데이터로 계산
    try:
        # 1. 유동비율 (Current Ratio) = 유동자산 / 유동부채
        if '유동자산' in bs_data and '유동부채' in bs_data:
            current_assets = float(bs_data['유동자산']['thstrm_amount'].replace(',', ''))
            current_liabilities = float(bs_data['유동부채']['thstrm_amount'].replace(',', ''))
            if current_liabilities > 0:
                ratios['current_ratio'] = {
                    'name': '유동비율',
                    'value': round(current_assets / current_liabilities * 100, 2),
                    'unit': '%'
                }
        
        # 2. 부채비율 (Debt Ratio) = 부채총계 / 자본총계
        if '부채총계' in bs_data and '자본총계' in bs_data:
            total_liabilities = float(bs_data['부채총계']['thstrm_amount'].replace(',', ''))
            total_equity = float(bs_data['자본총계']['thstrm_amount'].replace(',', ''))
            if total_equity > 0:
                ratios['debt_ratio'] = {
                    'name': '부채비율',
                    'value': round(total_liabilities / total_equity * 100, 2),
                    'unit': '%'
                }
        
        # 3. 매출액이익률 (Profit Margin) = 당기순이익 / 매출액
        if '당기순이익' in is_data and '매출액' in is_data:
            net_income = float(is_data['당기순이익']['thstrm_amount'].replace(',', ''))
            revenue = float(is_data['매출액']['thstrm_amount'].replace(',', ''))
            if revenue > 0:
                ratios['profit_margin'] = {
                    'name': '매출액이익률',
                    'value': round(net_income / revenue * 100, 2),
                    'unit': '%'
                }
        
        # 4. 자기자본이익률 (ROE) = 당기순이익 / 자본총계
        if '당기순이익' in is_data and '자본총계' in bs_data:
            net_income = float(is_data['당기순이익']['thstrm_amount'].replace(',', ''))
            total_equity = float(bs_data['자본총계']['thstrm_amount'].replace(',', ''))
            if total_equity > 0:
                ratios['roe'] = {
                    'name': '자기자본이익률(ROE)',
                    'value': round(net_income / total_equity * 100, 2),
                    'unit': '%'
                }
        
        # 5. 총자산이익률 (ROA) = 당기순이익 / 자산총계
        if '당기순이익' in is_data and '자산총계' in bs_data:
            net_income = float(is_data['당기순이익']['thstrm_amount'].replace(',', ''))
            total_assets = float(bs_data['자산총계']['thstrm_amount'].replace(',', ''))
            if total_assets > 0:
                ratios['roa'] = {
                    'name': '총자산이익률(ROA)',
                    'value': round(net_income / total_assets * 100, 2),
                    'unit': '%'
                }
    
    except (ValueError, KeyError, ZeroDivisionError) as e:
        print(f"재무비율 계산 중 오류 발생: {e}")
    
    print(f"계산된 재무비율: {ratios}")
    return ratios

@app.route('/get_company_info')
def get_company_info():
    """회사 정보 가져오기"""
    corp_code = request.args.get('corp_code', '')
    
    if not corp_code:
        return jsonify({'error': '회사 코드가 필요합니다.'})
    
    # OpenDart API 호출
    url = "https://opendart.fss.or.kr/api/company.json"
    params = {
        'crtfc_key': API_KEY,
        'corp_code': corp_code
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return jsonify(data)

@app.route('/get_company_by_code')
def get_company_by_code():
    """회사 코드로 회사 정보 조회"""
    corp_code = request.args.get('corp_code', '')
    
    if not corp_code:
        return jsonify({'error': '회사 코드가 필요합니다.'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT corp_code, corp_name, stock_code, modify_date FROM companies WHERE corp_code = ?",
        (corp_code,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            'corp_code': row['corp_code'],
            'corp_name': row['corp_name'],
            'stock_code': row['stock_code'],
            'modify_date': row['modify_date']
        })
    else:
        return jsonify({'error': '해당 회사 코드를 찾을 수 없습니다.'})

if __name__ == '__main__':
    # 개발 환경에서는 디버그 모드로 실행
    # 프로덕션 환경에서는 호스트와 포트를 환경 변수에서 가져옴
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 