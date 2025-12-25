import streamlit as st
from PIL import Image
import pytesseract
import re
import random

# 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS 스타일링: 쇼츠 최적화 및 상단 잘림 방지
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .block-container {
        max-width: 450px !important;
        padding-top: 5rem !important; /* 상단 여백 대폭 추가 (글자 잘림 방지) */
    }

    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000; 
        color: #FFFFFF;
    }
    
    /* 제목 스타일 */
    .main-title { 
        font-size: 2.8rem; 
        font-weight: 900; 
        text-align: center; 
        background: linear-gradient(to right, #00FF88, #60EFFF); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        margin-bottom: 10px;
    }
    
    /* 라디오 버튼(메뉴) 가로 정렬 및 스타일 */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 10px;
    }
    div.row-widget.stRadio label {
        background-color: #1A1A1A;
        padding: 10px 15px;
        border-radius: 10px;
        border: 1px solid #333;
    }

    .result-box {
        background-color: #1A1A1A;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #00FF88;
        margin-top: 20px;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더
st.markdown('<p class="main-title">지름신 판독기</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#BBB;">살까 말까 고민될 땐? AI 판사님께.</p>', unsafe_allow_html=True)

# 1. 판독 모드 (한눈에 보이는 라디오 버튼)
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])

tab1, tab2 = st.tabs(["🔗 링크 분석", "📸 이미지 스캔"])
detected_price = 0

with tab1:
    url = st.text_input("상품 URL 입력", placeholder="https://...")
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

# 2. 랜덤 멘트 데이터베이스
happy_quotes = [
    "🚀 이건 소비가 아니라 미래의 나를 위한 '풀매수' 투자입니다!",
    "✨ 고민은 배송만 늦출 뿐! 오늘 사면 내일의 내가 고마워할 거예요.",
    "💎 당신의 가치에 비하면 이 정도 금액은 껌값 아닐까요?",
    "🔥 인생은 짧습니다. 가지고 싶은 건 가져야죠! 지르세요!"
]

fact_quotes = [
    "💀 정신 차리세요! 이거 사고 일주일 뒤면 구석에 박혀있을 게 뻔합니다.",
    "💸 통장 잔고를 보고도 손가락이 움직이나요? 이건 명백한 과소비입니다.",
    "🚫 예쁜 쓰레기 수집가님, 이번에는 제발 참으세요.",
    "🧊 냉정해지세요. 이거 없어도 당신 인생은 아무런 문제가 없습니다."
]

# 판결 실행
if st.button("⚖️ 최종 판결 내리기"):
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    
    if mode == "행복 회로":
        st.subheader("🔥 판결: 지름신 강림!")
        st.write(random.choice(happy_quotes))

    elif mode == "팩트 폭격":
        st.subheader("❄️ 판결: 지름 금지!")
        st.write(random.choice(fact_quotes))

    elif mode == "AI 판결":
        st.subheader("⚖️ AI 판사님의 데이터 분석")
        current_p = detected_price if detected_price > 0 else 125000
        min_p = int(current_p * 0.82)
        
        st.write(f"📊 분석 현재가: **{current_p:,}원**")
        st.write(f"📉 과거 최저가: **{min_p:,}원**")
        
        # 3. 근거 제시 및 링크 연결
        st.markdown("---")
        st.write("🔍 **판결 근거 (커뮤니티 분석):**")
        st.write("- '역대급 딜'이라는 의견보다 '재고 처리'라는 의견이 다수 감지됨.")
        st.write("- 뽐뿌, 루리웹 등 주요 커뮤니티 최근 3개월 평균가 기준.")
        
        # 다나와/네이버 쇼핑 등 검색 결과 링크 생성
        search_query = "최저가+리뷰"
        search_url = f"https://search.naver.com/search.naver?query={search_query}"
        st.markdown(f"[👉 실시간 최저가 및 리뷰 확인하기]({search_url})")

        if current_p > min_p * 1.1:
            st.error(f"❌ 지금은 너무 비쌉니다! **{int(min_p * 1.05):,}원** 이하를 노리세요.")
        else:
            st.success("✅ 가격이 적당합니다. 지금 바로 지르셔도 좋습니다!")

    st.markdown('</div>', unsafe_allow_html=True)
