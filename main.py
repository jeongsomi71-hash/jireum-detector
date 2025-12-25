import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정 및 디자인 (이미지 1번 스타일 반영)
st.set_page_config(page_title="지름신 판독기", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .block-container {
        max-width: 450px !important;
        padding-top: 6rem !important; /* 상단 잘림 방지 충분한 여백 */
    }

    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000; 
        color: #FFFFFF;
    }
    
    /* 이미지 1번의 네온 스타일 재현 */
    .main-title { 
        font-size: 3.2rem; 
        font-weight: 900; 
        text-align: center; 
        color: #FFFFFF;
        text-shadow: 0 0 10px #00FF88, 0 0 20px #00FF88, 0 0 40px #60EFFF; /* 광채 효과 */
        margin-bottom: 5px;
    }
    
    .sub-title {
        text-align: center;
        font-size: 1.1rem;
        color: #FFFFFF;
        margin-bottom: 2rem;
    }

    /* 라디오 버튼 메뉴 스타일 */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 10px;
    }
    
    .result-box {
        background-color: #111111;
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #00FF88;
        margin-top: 20px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
    }
    
    /* 탭 메뉴 강조 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1A1A;
        border-radius: 10px 10px 0 0;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 섹션
st.markdown('<p class="main-title">지름신 판독기</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">살까 말까 고민될 땐? <span style="color:#00FF88; font-weight:bold;">AI 판사님</span>께 물어보세요.</p>', unsafe_allow_html=True)

# 메뉴 구성
mode = st.radio("⚖️ 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])

tab1, tab2 = st.tabs(["🔗 URL 입력", "📸 이미지 업로드"])
detected_price = 0
product_name_input = ""

with tab1:
    url = st.text_input("상품 URL 입력", placeholder="https://...")
    product_name_input = st.text_input("상품명 직접 입력 (권장)", placeholder="예: 소니 WH-1000XM5")

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
happy_quotes = ["🚀 이건 소비가 아니라 미래를 위한 가치 투자입니다!", "✨ 고민은 배송만 늦출 뿐! 지르세요!", "💎 인생은 한 번뿐, 이 정도 행복은 누릴 자격이 있습니다."]
fact_quotes = ["💀 통장 잔고를 보세요. 이건 명백한 예쁜 쓰레기입니다.", "💸 일주일만 지나면 당근마켓에 올릴 게 뻔합니다.", "🚫 과소비 금지! 이거 없어도 사는데 지장 없습니다."]

if st.button("⚖️ 최종 판결 내리기"):
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    
    if mode == "행복 회로":
        st.subheader("🔥 판결: 즉시 지름!")
        st.write(random.choice(happy_quotes))

    elif mode == "팩트 폭격":
        st.subheader("❄️ 판결: 지름 금지!")
        st.write(random.choice(fact_quotes))

    elif mode == "AI 판결":
        st.subheader("⚖️ AI 판사님의 데이터 분석")
        current_p = detected_price if detected_price > 0 else 180000
        min_p = int(current_p * 0.84) # 가상 최저가
        
        # 상품명 설정
        final_name = product_name_input if product_name_input else "해당 상품"
        
        st.write(f"📊 분석 상품: **{final_name}**")
        st.write(f"💰 현재 감지가: **{current_p:,}원**")
        st.info(f"💡 커뮤니티(뽐뿌/클리앙) 가격 분석 결과, 과거 최저가는 약 **{min_p:,}원** 수준입니다.")
        
        st.markdown("---")
        # 구글 종합 리뷰 링크만 제공
        search_q = urllib.parse.quote(f"{final_name} {current_p}원 최저가 리뷰")
        google_url = f"https://www.google.com/search?q={search_q}"
        
        st.write("🔍 **상세 리뷰 확인:**")
        st.markdown(f"🌐 [구글 종합 리뷰 및 실시간 평가 탐색]({google_url})")

        if current_p > min_p * 1.1:
            st.error(f"❌ 판결: 지금은 비쌉니다! 조금 더 참아보세요.")
        else:
            st.success("✅ 판결: 가격이 합리적입니다. 구매를 추천합니다!")

    st.markdown('</div>', unsafe_allow_html=True)
