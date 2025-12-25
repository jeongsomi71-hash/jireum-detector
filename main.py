import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS: 디자인 통일 (흰색 배경 + 검정 글씨 헤더)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .block-container {
        max-width: 500px !important;
        padding-top: 5rem !important;
    }

    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000 !important; 
        color: #FFFFFF !important;
    }
    
    .unified-header {
        background-color: #FFFFFF;
        color: #000000 !important;
        text-align: center;
        font-size: 1.8rem;
        font-weight: 800;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 5px;
    }
    
    .sub-header {
        background-color: #FFFFFF;
        color: #000000 !important;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 2.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더
st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 2. 강력한 초기화 함수: 자바스크립트를 이용한 메인 페이지 강제 이동
def hard_refresh_with_js():
    # 쿼리 파라미터를 비우고 페이지를 루트 주소로 강제 이동시킵니다.
    # 이 방식은 브라우저가 보관하던 모든 폼 데이터(이미지, 텍스트)를 날려버립니다.
    st.write('<section nonce="dummy"><script>window.parent.location.assign(window.parent.location.pathname);</script></section>', unsafe_allow_html=True)
    st.stop()

# 입력 섹션 (각 위젯에 고유 key 부여)
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tab1, tab2, tab3 = st.tabs(["🔗 URL 입력", "📸 이미지 업로드", "✍️ 직접 입력하기"])

final_name = ""
final_price = 0

with tab1:
    url = st.text_input("상품 URL 입력", key="url_input")

with tab2:
    uploaded_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="file_input")
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            price_match = re.search(r'([0-9,]{3,})원', text)
            if price_match:
                final_price = int(price_match.group(1).replace(',', ''))
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
            if lines: final_name = lines[0]
        except: pass

with tab3:
    manual_name = st.text_input("상품명 직접 입력", key="m_name")
    manual_price = st.text_input("가격 직접 입력", key="m_price")
    if manual_name: final_name = manual_name
    if manual_price: 
        try: final_price = int(re.sub(r'[^0-9]', '', manual_price))
        except: pass

# 판결 실행
if st.button("⚖️ 최종 판결 내리기"):
    if not final_name or final_price == 0:
        st.error("❗ 정보가 부족합니다. '직접 입력하기' 탭에서 정보를 완성해 주세요.")
    else:
        # (결과 출력 로직 생략 없이 그대로 유지)
        st.markdown('---')
        if mode == "행복 회로":
            st.subheader(f"🔥 {final_name}: 즉시 지름!")
            st.write("🚀 고민은 배송만 늦출 뿐!")
        elif mode == "팩트 폭격":
            st.subheader(f"❄️ {final_name}: 지름 금지!")
            st.write("💀 정신 차리세요. 통장이 비어갑니다.")
        elif mode == "AI 판결":
            st.subheader("⚖️ AI 정밀 분석")
            min_estimate = int(final_price * 0.82)
            st.write(f"📊 상품: **{final_name}** / 현재가: **{final_price:,}원**")
            search_q = urllib.parse.quote(f"{final_name} 구매 가격 후기")
            st.markdown(f"🛒 [{final_name} 가격 정보 확인](https://www.google.com/search?q={search_q})")

# 3. 하단 초기화 버튼 (가장 강력한 리다이렉트 방식)
st.markdown("<br><br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 새로운 상품 판독하기"):
        hard_refresh_with_js()
