import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS: 상단 타이틀과 부제목의 디자인 및 폰트 사이즈 통일
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
    
    /* 3. 타이틀과 부제목 폰트/색상 통일 (흰색 배경에 검정 글씨) */
    .unified-header {
        background-color: #FFFFFF;
        color: #000000 !important;
        text-align: center;
        font-size: 1.8rem; /* 폰트 사이즈 동일하게 조정 */
        font-weight: 800;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        line-height: 1.2;
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

    .result-content {
        margin-top: 30px;
        padding: 15px;
        border-top: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 상단 헤더 (디자인 통일)
st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 2. 새로운 상품 판독하기: F5와 동일한 효과를 주는 함수
def reset_app():
    # 세션 상태 전체 비우기
    for key in st.session_state.keys():
        del st.session_state[key]
    # JS를 활용한 브라우저 강제 새로고침 (F5 효과)
    st.markdown('<script>window.location.reload();</script>', unsafe_allow_html=True)
    st.rerun()

# 입력 섹션
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
        st.markdown('<div class="result-content">', unsafe_allow_html=True)
        
        if mode == "행복 회로":
            st.subheader(f"🔥 {final_name}: 즉시 지름!")
            st.write("🚀 이것은 소비가 아니라 인생을 위한 투자입니다.")
        elif mode == "팩트 폭격":
            st.subheader(f"❄️ {final_name}: 지름 금지!")
            st.write("💀 정신 차리세요. 이 돈이면 국밥이 몇 그릇입니까?")
        elif mode == "AI 판결":
            st.subheader("⚖️ AI 정밀 분석")
            min_estimate = int(final_price * 0.82)
            st.write(f"📊 상품: **{final_name}**")
            st.write(f"💰 분석가: **{final_price:,}원**")
            st.success(f"📉 추정 최저가: **{min_estimate:,}원**")
            
            # 1. 가격/구매 정보가 포함된 리뷰 검색 링크 최적화
            # 상품명 + "구매 가격 리뷰" 키워드 조합
            search_q = urllib.parse.quote(f"{final_name} 구매 가격 후기 리뷰")
            google_url = f"https://www.google.com/search?q={search_q}"
            
            st.markdown("---")
            st.markdown(f"🛒 [{final_name} 가격 정보 및 리뷰 확인]({google_url})")

            if final_price > min_estimate * 1.15:
                st.error("❌ 판결: 현재 가격은 바가지입니다. 기다리세요!")
            else:
                st.success("✅ 판결: 적정가입니다. 지름신을 영접하세요!")
        st.markdown('</div>', unsafe_allow_html=True)

# 2. 하단 중앙 정렬 초기화 버튼
st.markdown("<br><br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # 클릭 시 브라우저를 완전히 새로고침하는 기능 연결
    if st.button("🔄 새로운 상품 판독하기"):
        reset_app()
