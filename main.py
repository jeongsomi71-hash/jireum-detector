import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS: 헤더 디자인 통일
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    .block-container { max-width: 500px !important; padding-top: 5rem !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
    .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
    </style>
    """, unsafe_allow_html=True)

# 상단 헤더
st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 2. 입력 섹션 (간섭 차단을 위해 탭별로 독립적인 변수 사용)
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tabs = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

res_name, res_price = "", 0

with tabs[0]:
    url_input = st.text_input("상품 URL 입력", key="url_key")

with tabs[1]:
    img_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="img_key")
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        try:
            ocr_text = pytesseract.image_to_string(img, lang='kor+eng')
            p_match = re.search(r'([0-9,]{3,})원', ocr_text)
            if p_match: res_price = int(p_match.group(1).replace(',', ''))
            lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 3]
            if lines: res_name = lines[0]
        except: pass

with tabs[2]:
    m_name = st.text_input("상품명 입력", key="manual_name_key")
    m_price = st.text_input("가격 입력 (숫자만)", key="manual_price_key")
    # 직접 입력이 있으면 기존 OCR 결과보다 우선순위를 높임
    if m_name: res_name = m_name
    if m_price:
        try: res_price = int(re.sub(r'[^0-9]', '', m_price))
        except: pass

# 3. 판결 로직 (계산 버그 방지: 버튼 클릭 시점에서만 1회 계산)
if st.button("⚖️ 최종 판결 내리기"):
    if not res_name or res_price == 0:
        st.error("❗ 정보가 부족합니다. '직접 입력' 탭에서 정보를 완성해 주세요.")
    else:
        st.markdown('<hr>', unsafe_allow_html=True)
        # 비율 누적 버그 해결을 위한 변수 고정
        p_min = int(res_price * 0.82)
        p_avg = int(res_price * 0.93)
        
        if mode == "AI 판결":
            st.subheader(f"⚖️ {res_name} 분석")
            st.write(f"💰 현재가: **{res_price:,}원**")
            st.success(f"📉 추정 최저가: **{p_min:,}원**")
            st.info(f"💡 적정가 기준: **{p_avg:,}원**")
            
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(res_name + ' 구매 가격 리뷰')}"
            st.markdown(f"🛒 [{res_name} 리뷰 및 실구매가 확인]({search_url})")
            
            if res_price > p_avg * 1.05:
                st.error("❌ 판결: 거품이 껴 있습니다. 지금 사면 손해!")
            else:
                st.success("✅ 판결: 합리적인 가격입니다. 지르셔도 좋습니다!")

# ----------------------------------------------------------------
# 4. 핵심: 자바스크립트를 직접 심은 물리적 "F5" 버튼
# ----------------------------------------------------------------
st.markdown("<br><br><center>", unsafe_allow_html=True)
# 일반 st.button 대신 HTML 버튼을 직접 생성하여 클릭 시 부모 창을 강제 새로고침합니다.
st.components.v1.html(
    f"""
    <button onclick="window.parent.location.reload();" 
    style="
        width: 100%;
        height: 50px;
        background-color: #444;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        cursor: pointer;
    ">
    🔄 새로운 상품 판독하기 (완전 초기화)
    </button>
    """,
    height=60
)
st.markdown("</center>", unsafe_allow_html=True)
