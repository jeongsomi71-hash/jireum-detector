import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="지름신 판독기", layout="centered")

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

# 헤더
st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 핵심 1: 입력 위젯 간의 간섭을 방지하기 위한 로직 분리
# ----------------------------------------------------------------
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tab_select = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

# 각 탭의 결과값을 담을 독립 변수 초기화
name_from_url, price_from_url = "", 0
name_from_img, price_from_img = "", 0
name_manual, price_manual = "", 0

with tab_select[0]:
    url_input = st.text_input("상품 URL을 입력하세요", key="url_input")
    # URL 인식 로직 (필요 시 확장 가능)

with tab_select[1]:
    img_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="img_input")
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            p_match = re.search(r'([0-9,]{3,})원', text)
            if p_match: price_from_img = int(p_match.group(1).replace(',', ''))
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
            if lines: name_from_img = lines[0]
        except: pass

with tab_select[2]:
    name_manual = st.text_input("상품명 입력", key="m_name")
    p_input = st.text_input("가격 입력 (숫자만)", key="m_price")
    if p_input: 
        try: price_manual = int(re.sub(r'[^0-9]', '', p_input))
        except: pass

# ----------------------------------------------------------------
# 핵심 2: 우선순위 결정 (직접 입력 > 이미지 > URL)
# ----------------------------------------------------------------
final_name = name_manual if name_manual else (name_from_img if name_from_img else "")
final_price = price_manual if price_manual > 0 else (price_from_img if price_from_img > 0 else 0)

if st.button("⚖️ 최종 판결 내리기"):
    if not final_name or final_price == 0:
        st.error("❗ 판결할 상품 정보가 부족합니다. 직접 입력 탭을 확인해 주세요.")
    else:
        st.markdown('<div class="result-content">', unsafe_allow_html=True)
        # 가격 계산 고정 (버그 방지)
        min_p = int(final_price * 0.82)
        avg_p = int(final_price * 0.93)
        
        if mode == "AI 판결":
            st.subheader(f"⚖️ {final_name} 분석")
            st.write(f"💰 현재가: **{final_price:,}원**")
            st.success(f"📉 추정 최저가: **{min_p:,}원**")
            st.info(f"💡 적정가 기준: **{avg_p:,}원**")
            
            search_q = urllib.parse.quote(f"{final_name} 구매 가격 리뷰")
            st.markdown(f"🛒 [{final_name} 리뷰 확인](https://www.google.com/search?q={search_q})")
            
            if final_price > avg_p * 1.05:
                st.error("❌ 판결: 거품 낀 가격입니다. 사지 마세요!")
            else:
                st.success("✅ 판결: 가격이 합리적입니다. 지르세요!")
        # (행복 회로/팩트 폭격 로직 동일)
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 핵심 3: 물리적 F5 강제 구현 (JavaScript 사용)
# ----------------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 새로운 상품 판독하기"):
    # 이 스크립트는 브라우저의 모든 캐시와 위젯 상태를 무시하고 페이지를 아예 새로 고침합니다.
    st.components.v1.html(
        """
        <script>
        window.parent.location.reload();
        </script>
        """,
        height=0
    )
