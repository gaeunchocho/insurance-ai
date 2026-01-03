**hi_light: 현대해상 보험 추천 AI 서비스
현대해상 약관 데이터를 바탕으로 사용자에게 최적의 보험 상품을 추천하고 상담해주는 RAG(Retrieval-Augmented Generation) 기반 AI 챗봇입니다.**

**주요 기능**

맞춤 키워드 추천: 사용자의 상황(대상, 위험 요소, 우선순위 등)을 태그로 선택하여 빠르게 맞춤형 상품을 추천받을 수 있습니다.

약관 기반 상담: LangChain과 ChromaDB를 활용하여 실제 보험 약관 데이터를 근거로 정확한 정보를 제공합니다.

실시간 상품 연결: 추천된 상품에 대해 현대해상 공식 홈페이지 상세 페이지로 연결되는 다이렉트 버튼을 제공합니다.

상담 로그 기록: Google Sheets API를 연동하여 사용자의 상담 흐름과 클릭 데이터를 실시간으로 기록하고 분석합니다.


**기술스택**

Frontend : Streamlit

AI : Framework,"LangChain, LangChain-Chroma, LangChain-HuggingFace"

LLM : Claude 3.5 Sonnet (via Potens API)

Embeddings : ko-sroberta-multitask

Database : ChromaDB (Vector Store)

Data Sync : Google Sheets API (gspread)

**설치 및 실행 방법**

저장소 클론
Bash
git clone https://github.com/gaeunchocho/insurance-ai.git
cd insurance-ai

필수 라이브러리 설치
pip install -r requirements.txt

환경 변수 설정 .env 파일 또는 Streamlit Secrets에 아래 정보를 설정해야 합니다.

POTENS_API_KEY: AI 모델 호출을 위한 API 키

POTENS_ENDPOINT: API 엔드포인트 주소

SPREADSHEET_NAME: 로그를 기록할 구글 시트 이름

gcp_service_account: 구글 API 인증 정보 (JSON 형식)

앱 실행
streamlit run app.py

**파일 구조**
app.py: 스트림릿 메인 실행 파일 및 UI 로직
chroma_db/: 보험 약관 데이터가 임베딩되어 저장된 벡터 데이터베이스
requirements.txt: 프로젝트 의존성 라이브러리 목록
.streamlit/secrets.toml: (로컬용) 보안 설정 파일

본 서비스는 현대해상 공식 서비스가 아닌 약관 기반 상담 데모 프로젝트입니다.
정확한 보장 내용 및 가입 상담은 반드시 보험사 공식 홈페이지나 상담사를 통해 확인해야 합니다.
