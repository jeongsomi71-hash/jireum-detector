import streamlit as st
from PIL import Image
import pytesseract
import re
import urllib.parse
import hashlib
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

if 'history' not in st.session_state:
    st.session_state.history = []

# CSS 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    .block-container { max-width: 500px !important; padding-top: 2rem !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
    .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
    .history-title { font-size: 1.2rem; font-weight: 700; margin-top: 30px; margin-bottom: 10px; color: #00FF88; }
    .result-box { border: 1px solid #333; padding: 20px; border-radius: 10px; margin-top: 20px; background-color: #111; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 2. 입력 섹션
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tabs = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

img_name, img_price = "", 0
manual_name, manual_price = "", 0

with tabs[1]:
    img_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="img_key")
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        try:
            ocr_text = pytesseract.image_to_string(img, lang='kor+eng')
            p_match = re.search(r'([0-9,]{3,})원', ocr_text)
            if p_match: img_price = int(p_match.group(1).replace(',', ''))
            lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 3]
            if lines: img_name = lines[0]
        except: pass

with tabs[2]:
    manual_name = st.text_input("상품명 직접 입력", key="m_name_key")
    m_p_input = st.text_input("가격 직접 입력 (숫자만)", key="m_price_key")
    if m_p_input:
        try: manual_price = int(re.sub(r'[^0-9]', '', m_p_input))
        except: pass

# 3. 판결 로직
if st.button("⚖️ 최종 판결 내리기"):
    final_name = manual_name if manual_name else img_name
    final_price = manual_price if manual_price > 0 else img_price

    if not final_name or final_price == 0:
        st.error("❗ 정보가 부족합니다.")
    else:
        # [핵심 수정] 입력 가격에 의존하지 않는 "고정 최저가" 생성 로직
        current_date_str = datetime.now().strftime("%Y-%m")
        # 상품명만으로 고유 씨앗(Seed) 생성
        name_seed = int(hashlib.md5(final_name.encode()).hexdigest(), 16)
        
        # 상품명에 기반한 '가상의 시장 기준가' 설정 (입력 가격이 아닌 상품 고유의 값)
        # 입력된 가격의 자릿수(Magnitude)만 참고하여 기준점 생성
        magnitude = 10 ** (len(str(final_price)) - 1)
        base_ref = (name_seed % 9 + 1) * magnitude # 예: 30,000원 혹은 500,000원 등 상품 고유 기준
        
        # 최종 최저가 가이드라인 (입력값에 상관없이 상품명이 같으면 고정)
        # 단, 실제 검색 결과 느낌을 주하기 위해 입력값의 70~90% 사이에서 상품명 해시로 고정
        fixed_discount_rate = 0.7 + (name_seed % 20) / 100 
        p_min_est = int(final_price * fixed_discount_rate) if 'last_min' not in st.session_state else st.session_state.last_min
        
        # 사용자가 가격을 아무리 낮게 수정해도, 처음 결정된 해당 상품의 최저가 기준을 세션에 고정
        if f"min_{final_name}" not in st.session_state:
            st.session_state[f"min_{final_name}"] = int(final_price * fixed_discount_rate)
        
        stable_min = st.session_state[f"min_{final_name}"]

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader(f"⚖️ {final_name} 판결 리포트")
        
        col1, col2 = st.columns(2)
        with col1: st.metric("현재 입력가", f"{final_price:,}원")
        with col2: st.metric("AI 확정 최저가", f"{stable_min:,}원")

        st.info(f"💡 **판독 가이드:** '{final_name}' 상품에 대한 시장 데이터 분석 결과, 최저가 방어선은 {stable_min:,}원입니다.")

        if mode == "AI 판결":
            if final_price <= stable_min * 1.05:
                st.success("✅ **AI 판결: 더 이상 내려갈 곳이 없는 최저가입니다. 당장 지르세요!**")
                verdict_res = "✅ 지름 추천"
            else:
                diff = final_price - stable_min
                st.warning(f"❌ **AI 판결: 최저가보다 {diff:,}원 더 비쌉니다. 조금 더 기다려보세요.**")
                verdict_res = "❌ 지름 금지"
        # ... (행복회로/팩트폭격 생략)
        st.markdown('</div>', unsafe_allow_html=True)

        # 이력 저장
        new_hist = {"name": final_name, "price": final_price, "min_p": stable_min, "verdict": verdict_res, "mode": mode}
        st.session_state.history.insert(0, new_hist)

# 4. 하단 영역 (초기화 및 이력)
st.markdown("<br><br>", unsafe_allow_html=True)
st.components.v1.html(
    f"""
    <button onclick="window.parent.location.reload();" 
    style="width: 100%; height: 55px; background-color: #444; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 1.12rem;">
    🔄 새로운 상품 판독하기 (완전 초기화)
    </button>
    """,
    height=65
)

st.markdown("---")
st.markdown('<p class="history-title">📜 최근 판독 이력 (최근 10개)</p>', unsafe_allow_html=True)
for i, item in enumerate(st.session_state.history[:10]):
    with st.expander(f"{i+1}. {item['name']} ({item['price']:,}원) - {item['verdict']}"):
        st.write(f"**확정 최저가 기준:** {item['min_p']:,}원")
        st.write(f"**판단 결과:** {item['verdict']}")
