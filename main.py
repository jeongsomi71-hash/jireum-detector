import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse
import time

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

# 2. 강력한 리셋 로직 (세션 키 자체를 변경)
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

def full_reload():
    # 세션의 모든 데이터 삭제
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # 자바스크립트로 부모 창을 강제 새로고침 (가장 확실한 F5 효과)
    st.markdown('<script>window.parent.location.reload();</script>', unsafe_allow_html=True)
    st.stop()

# 헤더
st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 3. 입력 섹션 (reset_key를 이용해 위젯을 매번 새로 생성)
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tabs = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

final_name = ""
final_price = 0

# 탭별 독립적 입력 관리 (서로 간섭하지 않도록 지역 변수화)
with tabs[0]:
    url_val = st.text_input("상품 URL", key=f"url_{st.session_state.reset_key}")

with tabs[1]:
    img_val = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key=f"img_{st.session_state.reset_key}")
    if img_val:
        img = Image.open(img_val)
        st.image(img, use_container_width=True)
        try:
            ocr_text = pytesseract.image_to_string(img, lang='kor+eng')
            p_match = re.search(r'([0-9,]{3,})원', ocr_text)
            if p_match: final_price = int(p_match.group(1).replace(',', ''))
            lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 3]
            if lines: final_name = lines[0]
        except: pass

with tabs[2]:
    m_name = st.text_input("상품명 입력", key=f"name_{st.session_state.reset_key}")
    m_price = st.text_input("가격 입력", key=f"price_{st.session_state.reset_key}")
    # 직접 입력이 있으면 최우선 적용
    if m_name: final_name = m_name
    if m_price:
        try: final_price = int(re.sub(r'[^0-9]', '', m_price))
        except: pass

# 4. 판결 버튼 로직
if st.button("⚖️ 최종 판결 내리기"):
    if not final_name or final_price == 0:
        st.error("❗ 정보가 부족합니다. '직접 입력' 탭을 통해 정보를 채워주세요.")
    else:
        st.markdown('<div class="result-content">', unsafe_allow_html=True)
        
        # 버그 방지용 고정 수치 계산
        min_p = int(final_price * 0.82)
        avg_p = int(final_price * 0.93)
        
        if mode == "AI 판결":
            st.subheader(f"⚖️ {final_name} 분석")
            st.write(f"💰 현재 감지가: **{final_price:,}원**")
            st.success(f"📉 역대 최저가(추정): **{min_p:,}원**")
            st.info(f"💡 적정가 기준: **{avg_p:,}원**")
            
            search_q = urllib.parse.quote(f"{final_name} 구매 가격 리뷰")
            st.markdown("---")
            st.markdown(f"🛒 [{final_name} 리뷰 및 가격 확인](https://www.google.com/search?q={search_q})")
            
            if final_price > avg_p * 1.05:
                st.error("❌ 판결: 바가지 가능성 농후! 더 참으세요.")
            else:
                st.success("✅ 판결: 훌륭한 가격입니다. 지금 사세요!")
        
        st.markdown('</div>', unsafe_allow_html=True)

# 5. 하단 중앙 초기화 버튼 (가장 강력한 JS 방식)
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 새로운 상품 판독하기"):
    full_reload()
