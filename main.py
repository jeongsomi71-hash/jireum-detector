import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS: 폰트 사이즈 2배 확대 및 줄바꿈 방지 적용
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .block-container {
        max-width: 600px !important; /* 타이틀 줄바꿈 방지를 위해 너비 확장 */
        padding-top: 5rem !important;
    }

    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000 !important; 
        color: #FFFFFF !important;
    }
    
    /* 2. 지름신 판독기 폰트 사이즈 2배 및 줄바꿈 금지 */
    .main-title { 
        font-size: 8.5rem; /* 기존보다 약 2배 더 키움 */
        font-weight: 900; 
        text-align: center; 
        color: #00FF88;
        text-shadow: 4px 4px 20px rgba(0, 255, 136, 0.8);
        line-height: 1.0;
        margin-bottom: 20px;
        white-space: nowrap; /* 줄바꿈 방지 */
        letter-spacing: -5px; /* 글자 간격 조절로 가로 폭 최적화 */
    }
    
    .sub-title-box {
        background-color: #FFFFFF;
        color: #000000 !important;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 2.5rem;
    }

    .result-content {
        margin-top: 30px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 섹션
st.markdown('<p class="main-title">지름신 판독기</p>', unsafe_allow_html=True)
st.markdown('<div class="sub-title-box">⚖️ AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 1. 새로운 상품 판독하기: 모든 상태를 강제로 초기화하는 함수
def reset_app():
    # 모든 세션 상태 삭제
    for key in st.session_state.keys():
        del st.session_state[key]
    # 쿼리 파라미터를 사용하여 페이지를 완전히 새로 고침
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# 메뉴 및 입력 세션
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
    if manual_price: final_price = int(re.sub(r'[^0-9]', '', manual_price))

# 판결 실행
if st.button("⚖️ 최종 판결 내리기"):
    if not final_name or final_price == 0:
        st.error("❗ 정보가 부족합니다. '직접 입력하기' 탭에서 보완해 주세요.")
    else:
        st.markdown('<div class="result-content">', unsafe_allow_html=True)
        if mode == "행복 회로":
            st.subheader(f"🔥 {final_name}: 무조건 지름!")
            st.write("🚀 미래의 나를 위한 최고의 선물입니다.")
        elif mode == "팩트 폭격":
            st.subheader(f"❄️ {final_name}: 지름 금지!")
            st.write("💀 정신 차리세요. 곧 당근마켓에 올리게 될 겁니다.")
        elif mode == "AI 판결":
            st.subheader("⚖️ AI 정밀 분석")
            min_estimate = int(final_price * 0.82)
            st.write(f"📊 상품: **{final_name}** / 현재가: **{final_price:,}원**")
            st.success(f"📉 추정 최저가: **{min_estimate:,}원**")
            
            search_q = urllib.parse.quote(f"{final_name} 리뷰 후기")
            st.markdown(f"🌐 [{final_name} 리뷰 확인하기](https://www.google.com/search?q={search_q})")
        st.markdown('</div>', unsafe_allow_html=True)

# 1. 하단 중앙 정렬 초기화 버튼
st.markdown("<br><br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 새로운 상품 판독하기"):
        reset_app()
