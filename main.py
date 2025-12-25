import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS: 디자인 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    .block-container { max-width: 500px !important; padding-top: 5rem !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
    .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 5px; }
    .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
    .result-content { margin-top: 30px; padding: 15px; border-top: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. 강력한 초기화 함수 (F5와 동일 효과)
def hard_reset():
    st.cache_data.clear()
    st.cache_resource.clear()
    for key in st.session_state.keys():
        del st.session_state[key]
    # URL에 타임스탬프를 섞어 브라우저가 완전히 새 페이지로 인식하게 만듦
    import time
    st.query_params.from_dict({"refresh": str(time.time())})
    st.rerun()

# 헤더
st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 입력 섹션 (키값을 고정하여 관리)
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tab1, tab2, tab3 = st.tabs(["🔗 URL 입력", "📸 이미지 업로드", "✍️ 직접 입력하기"])

raw_name = ""
raw_price = 0

with tab1:
    st.text_input("상품 URL 입력", key="url_input")

with tab2:
    uploaded_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="file_input")
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            price_match = re.search(r'([0-9,]{3,})원', text)
            if price_match:
                raw_price = int(price_match.group(1).replace(',', ''))
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
            if lines: raw_name = lines[0]
        except: pass

with tab3:
    m_name = st.text_input("상품명 직접 입력", key="m_name")
    m_price = st.text_input("가격 직접 입력 (숫자만)", key="m_price")
    if m_name: raw_name = m_name
    if m_price: 
        try: raw_price = int(re.sub(r'[^0-9]', '', m_price))
        except: pass

# 판결 버튼
if st.button("⚖️ 최종 판결 내리기"):
    if not raw_name or raw_price == 0:
        st.error("❗ 정보가 부족합니다. 직접 입력 탭에서 정보를 완성해 주세요.")
    else:
        st.markdown('<div class="result-content">', unsafe_allow_html=True)
        
        # 가격 계산 버그 방지: 1회성 고정 계산
        calc_min = int(raw_price * 0.82)
        calc_avg = int(raw_price * 0.93)
        
        if mode == "행복 회로":
            st.subheader(f"🔥 {raw_name}: 즉시 지름!")
            st.write("🚀 고민은 배송만 늦출 뿐! 미래의 나를 위한 선물입니다.")
        elif mode == "팩트 폭격":
            st.subheader(f"❄️ {raw_name}: 지름 금지!")
            st.write("💀 이 돈이면 국밥이 몇 그릇입니까? 당장 창을 닫으세요.")
        elif mode == "AI 판결":
            st.subheader("⚖️ AI 정밀 분석 결과")
            st.write(f"📊 분석 상품: **{raw_name}**")
            st.write(f"💰 현재 감지가: **{raw_price:,}원**")
            st.success(f"📉 역대 최저가(추정): **{calc_min:,}원**")
            st.info(f"💡 적정 구매가: **{calc_avg:,}원** 수준")
            
            search_q = urllib.parse.quote(f"{raw_name} 구매 가격 후기 리뷰")
            st.markdown("---")
            st.markdown(f"🛒 [{raw_name} 가격 정보 확인](https://www.google.com/search?q={search_q})")

            if raw_price > calc_avg * 1.05:
                st.error("❌ 판결: 거품 낀 가격입니다. 절대 사지 마세요!")
            else:
                st.success("✅ 판결: 적정 가격입니다. 지름신을 영접하세요!")
        st.markdown('</div>', unsafe_allow_html=True)

# 하단 초기화 버튼 (강력한 리프레시 로직 연결)
st.markdown("<br><br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 새로운 상품 판독하기"):
        hard_reset()
