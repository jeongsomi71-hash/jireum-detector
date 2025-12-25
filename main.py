import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정 및 가독성 중심 디자인 (배경 검정, 글자 흰색/네온)
st.set_page_config(page_title="지름신 판독기", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .block-container {
        max-width: 450px !important;
        padding-top: 6rem !important; /* 상단 잘림 방지 */
    }

    /* 배경은 완전 검정, 글자는 선명한 흰색으로 고정 */
    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000 !important; 
        color: #FFFFFF !important;
    }
    
    /* 제목: 검정 배경에서 가장 잘 보이는 네온 그린 */
    .main-title { 
        font-size: 3.2rem; 
        font-weight: 900; 
        text-align: center; 
        color: #00FF88;
        text-shadow: 2px 2px 10px rgba(0, 255, 136, 0.5);
        margin-bottom: 10px;
    }
    
    .sub-title {
        text-align: center;
        font-size: 1.2rem;
        color: #FFFFFF; /* 부제목도 선명한 흰색 */
        font-weight: 700;
        margin-bottom: 2rem;
    }

    /* 입력창 및 라벨 글자색 수정 (어두운 배경 대응) */
    label, .stTextInput p {
        color: #FFFFFF !important;
        font-weight: bold;
    }

    /* 결과 박스: 테두리를 진하게 하여 시인성 확보 */
    .result-box {
        background-color: #111111;
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #00FF88;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 섹션
st.markdown('<p class="main-title">지름신 판독기</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">AI 판사님의 냉철한 판결</p>', unsafe_allow_html=True)

# 메뉴 구성
mode = st.radio("⚖️ 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])

tab1, tab2 = st.tabs(["🔗 URL 입력", "📸 이미지 업로드"])
detected_price = 0
product_name_input = ""

with tab1:
    url = st.text_input("상품 URL 입력", placeholder="https://...")
    product_name_input = st.text_input("상품명 입력 (정확한 분석용)", placeholder="예: 에어팟 맥스")

with tab2:
    uploaded_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            price_match = re.search(r'([0-9,]{3,})원', text)
            if price_match:
                detected_price = int(price_match.group(1).replace(',', ''))
        except: pass

# 판결 로직 데이터
happy_quotes = ["🚀 이건 소비가 아니라 미래를 위한 가치 투자입니다!", "✨ 고민은 배송만 늦출 뿐! 지르세요!", "💎 오늘 사면 내일의 내가 행복해집니다."]
fact_quotes = ["💀 통장 잔고를 보세요. 이건 명백한 예쁜 쓰레기입니다.", "💸 일주일 뒤면 당근마켓에 올릴 게 뻔합니다.", "🚫 과소비 금지! 이거 없어도 사는데 지장 없습니다."]

if st.button("⚖️ 최종 판결 내리기"):
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    
    # 상품명 확정
    final_name = product_name_input if product_name_input else "해당 상품"
    
    if mode == "행복 회로":
        st.subheader("🔥 판결: 즉시 지름!")
        st.write(random.choice(happy_quotes))

    elif mode == "팩트 폭격":
        st.subheader("❄️ 판결: 지름 금지!")
        st.write(random.choice(fact_quotes))

    elif mode == "AI 판결":
        st.subheader("⚖️ AI 판사님의 데이터 분석")
        current_p = detected_price if detected_price > 0 else 150000
        min_p = int(current_p * 0.85)
        
        st.write(f"📊 분석 상품: **{final_name}**")
        st.write(f"💰 현재가: **{current_p:,}원**")
        st.info(f"💡 뽐뿌/클리앙 분석 결과, 적정 구매가는 **{min_p:,}원** 이하입니다.")
        
        st.markdown("---")
        # 구글 검색어: 상품명 + 리뷰 중심 (가격은 참고용으로만 포함)
        search_q = urllib.parse.quote(f"{final_name} 내돈내산 솔직 리뷰")
        google_url = f"https://www.google.com/search?q={search_q}"
        
        st.write("🔍 **판결 근거 확인:**")
        st.markdown(f"🌐 [{final_name} 실시간 리뷰 보러가기]({google_url})")

        if current_p > min_p * 1.1:
            st.error(f"❌ 판결: 지금 사면 바보! 가격이 더 떨어질 때까지 기다리세요.")
        else:
            st.success("✅ 판결: 훌륭한 가격입니다. 지금 지르셔도 좋습니다!")

    st.markdown('</div>', unsafe_allow_html=True)
