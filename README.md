# 재무제표 시각화 웹 애플리케이션

OpenDart API를 활용하여 상장회사의 재무제표를 시각화하는 웹 애플리케이션입니다.

## 기능

1. 회사명 검색으로 회사 코드(corp_code) 조회
2. OpenDart API를 통해 재무제표 데이터 가져오기
3. Chart.js를 이용한 재무제표 시각화
   - 재무상태표: 자산, 부채, 자본 구성
   - 손익계산서: 매출액, 영업이익, 당기순이익 추이

## 설치 방법

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 OpenDart API 키를 설정합니다:

```
OPENDART_API_KEY=your_api_key_here
```

### 3. 회사 코드 데이터베이스 생성

```bash
python convert_to_json.py
```

## 실행 방법

```bash
python app.py
```

웹 브라우저에서 http://localhost:5000 으로 접속하여 사용합니다.

## 사용 방법

1. 회사명 입력 필드에 검색할 회사명을 입력합니다.
2. 검색 결과에서 원하는 회사를 클릭합니다.
3. 사업연도와 보고서 종류를 선택합니다.
4. "재무정보 불러오기" 버튼을 클릭합니다.
5. 재무상태표와 손익계산서가 차트로 시각화됩니다.

## 기술 스택

- Backend: Python, Flask
- Frontend: HTML, JavaScript, Bootstrap 5
- 데이터 시각화: Chart.js
- API: OpenDart API #   f s - a p p  
 #   f s - a p p  
 