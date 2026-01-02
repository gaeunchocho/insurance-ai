import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import os
import requests
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv

# --- [벡터 DB 라이브러리] ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- [1. 환경 설정 및 세션 초기화] ---
load_dotenv()
st.set_page_config(page_title="hi_light: 현대해상 보험 추천", page_icon="💡", layout="wide")

@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")

embeddings = load_embeddings()
CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

if os.path.exists(CHROMA_PATH):
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
else:
    st.error("❌ DB 폴더가 없습니다.")
    st.stop()

# 세션 상태 초기화
if "visitor_id" not in st.session_state:
    st.session_state.visitor_id = str(uuid.uuid4())[:8]
if "consult_count" not in st.session_state:
    st.session_state.consult_count = 1
    st.session_state.start_time = time.time()
    st.session_state.open_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "clicked_product" not in st.session_state:
    st.session_state.clicked_product = None

# 상품 데이터 및 링크
PRODUCT_LINKS = {
    "개인용 자동차보험": "https://www.hi.co.kr/serviceAction.do?menuId=100212",
    "간편한 3.10.10 건강보험(세만기형)": "https://www.hi.co.kr/serviceAction.do?menuId=202652",
    "골든타임 수술종합보험": "https://www.hi.co.kr/serviceAction.do?menuId=204360",
    "굿앤굿스타 종합보험(세만기형)": "https://www.hi.co.kr/serviceAction.do?menuId=100223",
    "굿앤굿 어린이종합보험Q": "https://www.hi.co.kr/serviceAction.do?menuId=100222",
    "내삶엔(3N) 맞춤간편 건강보험": "https://www.hi.co.kr/serviceAction.do?menuId=203552",
    "뉴하이카 운전자상해보험": "https://www.hi.co.kr/serviceAction.do?menuId=100215",
    "굿앤굿 우리펫보험": "https://www.hi.co.kr/serviceAction.do?menuId=202403",
    "퍼펙트플러스 종합보험(세만기형)": "https://www.hi.co.kr/serviceAction.do?menuId=100221",
    "행복가득 생활보장보험": "https://www.hi.co.kr/serviceAction.do?menuId=100242",
    "두배받는 암보험": "https://www.hi.co.kr/serviceAction.do?menuId=100224"
}

# 태그 카테고리 설정
tag_categories = {
    "👤 누구의 보험인가요?": ["#나", "#우리_아이", "#부모님", "#반려견", "#사회초년생", "#자영업자"],
    "🚑 어떤 위험이 걱정되나요?": ["#암_중증질환", "#수술_입원비", "#일상_생활책임", "#교통사고", "#치과", "#누수_화재"],
    "💰 우선 순위는 무엇인가요?": ["#가성비_보험료", "#든든한_진단비", "#무심사_가입", "#비갱신형", "#나중에환급"],
    "📅 최근에 어떤 변화가 있었나요?": ["#건강검진예정", "#내집마련", "#신차출고", "#자녀입학", "#유병자경력"]
}

if 'selected_tags' not in st.session_state:
    st.session_state.selected_tags = {cat: None for cat in tag_categories.keys()}

# --- [2. 구글 시트 로그 기록 함수] ---
# 기존 os.getenv 대신 st.secrets를 사용하도록 변경
def log_to_google_sheet(action_type, user_input="", recommended_product=""):
    try:
        # 1. Secrets 존재 확인
        if "gcp_service_account" in st.secrets:
            creds_info = st.secrets["gcp_service_account"]
            sheet_name = st.secrets["SPREADSHEET_NAME"]
            creds = Credentials.from_service_account_info(creds_info, scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ])
        else:
            # 로컬 테스트용 (기존 credentials.json 파일이 있을 경우)
            creds_path = "credentials.json"
            sheet_name = os.getenv("SPREADSHEET_NAME") or "hi_light_logs"
            creds = Credentials.from_service_account_file(creds_path, scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ])

        client = gspread.authorize(creds)
        worksheet = client.open(sheet_name).get_worksheet(0)

        duration = f"{int(time.time() - st.session_state.start_time)}초"
        row = [
            st.session_state.visitor_id,
            st.session_state.consult_count,
            st.session_state.open_time_str,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            action_type,
            user_input,
            recommended_product,
            duration
        ]
        worksheet.append_row(row)
    except Exception as e:
        # 터미널이 아닌 화면에 에러를 잠시 띄워 확인합니다.
        st.sidebar.error(f"로그 기록 실패: {e}")

# --- [3. 상품 버튼 렌더링 (2단계 링크 방식)] ---
def render_product_buttons(content, msg_idx):
    clean_content = content.replace(" ", "").replace("**", "")
    for p_name, p_url in PRODUCT_LINKS.items():
        if p_name.replace(" ", "") in clean_content:
            btn_key = f"btn_{msg_idx}_{p_name}"
            if st.button(f"🔎 {p_name} 더 알아보기", key=btn_key):
                log_to_google_sheet("상세보기클릭", user_input="버튼클릭", recommended_product=p_name)
                st.session_state.clicked_product = p_name
                st.rerun()

            if st.session_state.clicked_product == p_name:
                st.link_button(f"🚀 {p_name} 페이지 열기", p_url, type="primary")

# --- [4. AI 응답 생성 함수] ---
def generate_ai_response(messages):
    api_key = os.getenv('POTENS_API_KEY')
    endpoint = os.getenv('POTENS_ENDPOINT')
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    product_list = ", ".join(PRODUCT_LINKS.keys())
    last_query = messages[-1]["content"]
    docs = db.similarity_search(last_query, k=3)
    context = "\n\n".join([f"[{doc.metadata.get('source', '약관')}] {doc.page_content}" for doc in docs])
    history = "\n".join([f"{'고객' if m['role']=='user' else '상담원'}: {m['content']}" for m in messages])

    if len(messages) <= 2:
        full_prompt = f"""당신은 현대해상의 보험 전문가입니다. 다음 형식을 엄격히 지켜 답변하세요.
[추천 가능 상품] {product_list}
[약관 근거] {context}
[대화 내역] {history}

**출력 형식 가이드**:
1. 첫 줄: ## 💡 추천 상품
2. 둘째 줄: ### 🏥 [상품명] (가장 적합한 상품명 선택)
3. 셋째 줄: 약관에 따르면...
4. 보장 내용: 핵심 보장 3가지를 불렛 포인트(•)로 작성
   - 각 포인트는 반드시 '한 줄'로만 작성하고 끝에 이모티콘을 붙이세요. ✨
   - 불렛 포인트 사이에는 반드시 빈 줄을 하나씩 넣으세요.
   - 단어나 의미를 절대 중복하여 사용하지 마세요.
5. 마무리: 한 줄 띄우고 고객이 간단히 답할 수 있는 질문을 던진 뒤, 자연스럽게 상세보기 버튼 클릭을 유도하세요. 👇
상담원 답변:"""
    else:
        full_prompt = f"""당신은 현대해상의 친절한 보험 전문가입니다. [약관 근거]를 바탕으로 대화하세요.
[약관 근거] {context}
[대화 내역] {history}
**답변 가이드**: 친절하고 자유롭게 답변, 핵심 전달, 적절한 이모티콘 사용, 가벼운 질문 포함.
상담원 답변:"""

    payload = {"prompt": full_prompt, "model": "claude-3-5-sonnet-20241022", "max_tokens": 1000, "temperature": 0.5}
    try:
        res = requests.post(endpoint, json=payload, headers=headers).json()
        ans = res.get('message') or res.get('content') or res['choices'][0]['message']['content']
        return ans.strip()
    except: return "분석 중 오류가 발생했습니다."

# --- [5. 메인 UI] ---
st.title("💡 hi_light: 현대해상 약관 상담")

# 태그 선택 섹션
with st.expander("📍 맞춤 키워드 선택", expanded=not st.session_state.messages):
    for cat, tags in tag_categories.items():
        st.write(f"**{cat}**")
        cols = st.columns(len(tags))
        for i, tag in enumerate(tags):
            is_sel = (st.session_state.selected_tags[cat] == tag)
            if cols[i].button(f"✅ {tag}" if is_sel else tag, key=f"t_{cat}_{tag}"):
                st.session_state.selected_tags[cat] = None if is_sel else tag
                st.rerun()
    
    selected_str = " ".join([v for v in st.session_state.selected_tags.values() if v])
    user_desc = st.text_area("상황 설명", value=selected_str, placeholder="태그를 선택하거나 직접 상황을 입력하세요.")
    
    if st.button("🚀 현대해상 상품 추천", type="primary"):
        if user_desc.strip():
            st.session_state.messages.append({"role": "user", "content": user_desc})
            with st.spinner("분석 중..."):
                ans = generate_ai_response(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                
                extracted_p = "해당 없음"
                for p in PRODUCT_LINKS.keys():
                    if p.replace(" ","") in ans.replace(" ",""): extracted_p = p; break
                
                log_to_google_sheet("초기추천", user_input=user_desc, recommended_product=extracted_p)
            st.rerun()

st.divider()

# 채팅창
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_product_buttons(msg["content"], i)

if prompt := st.chat_input("추가 질문을 입력하세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        ans = generate_ai_response(st.session_state.messages)
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        log_to_google_sheet("추가질문", user_input=prompt)
        st.rerun()

# 사이드바
with st.sidebar:
    st.info("현대해상 약관 기반 상담 서비스입니다.")
    if st.button("🔄 상담 리셋하기"):
        log_to_google_sheet("상담초기화")
        st.session_state.messages = []
        st.session_state.consult_count += 1
        st.session_state.selected_tags = {k: None for k in tag_categories.keys()}
        st.session_state.clicked_product = None
        st.rerun()
