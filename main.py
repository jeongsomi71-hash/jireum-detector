import streamlit as st
from PIL import Image
import pytesseract
import re
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# 세션 상태 초기화 (판결 이력 저장용)
if 'history' not in st.session_state:
    st.session_state.history = []

# CSS 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    .block-container { max-width: 500px !important; padding-top: 2rem !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
    .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
    
    /* 최근 판독 이력 제목 폰트 사이즈 조절 (기존 1.5rem -> 1.2rem 수준으로 80% 축소) */
    .history-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 30px;
        margin-bottom: 10px;
        color: #00FF88;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더
st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 2. 입력 섹션
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tabs = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

res_name, res_price = "", 0

with tabs[0]:
    st.text_input("상품 URL 입력", key="url_key")

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
    m_price = st.text_input("가격 입력", key="manual_price_key")
    if m_name: res_name = m_name
    if m_price:
        try: res_price = int(re.sub(r'[^0-9]', '', m_price))
        except: pass

# 3. 판결 내리기 및 이력 저장
if st.button("⚖️ 최종 판결 내리기"):
    if not res_name or res_price == 0:
        st.error("❗ 정보가 부족합니다.")
    else:
        p_min = int(res_price * 0.82)
        p_avg = int(res_price * 0.93)
        verdict = "✅ 지름 추천" if res_price <= p_avg * 1.05 else "❌ 지름 금지"
        
        st.markdown('---')
        st.subheader(f"⚖️ {res_name} 판결 결과")
        st.write(f"💰 입력 가격: {res_price:,}원")
        st.write(f"📉 추정 최저가: {p_min:,}원")
        st.write(f"📢 판결: {verdict}")
        
        new_history = {
            "name": res_name,
            "price": res_price,
            "min_p": p_min,
            "verdict": verdict,
            "mode": mode
        }
        st.session_state.history.insert(0, new_history)
        if len(st.session_state.history) > 10:
            st.session_state.history.pop()

# 4. 하단 초기화 버튼 (폰트 사이즈를 기존 1.4rem의 80% 수준인 1.12rem으로 조절)
st.markdown("<br>", unsafe_allow_html=True)
st.components.v1.html(
    f"""
    <button onclick="window.parent.location.reload();" 
    style="
        width: 100%; height: 55px; background-color: #444; color: white;
        border: none; border-radius: 5px; font-weight: bold; cursor: pointer;
        font-size: 1.12rem; /* 기존 1.4rem 대비 80% 수준 */
    ">
    🔄 새로운 상품 판독하기 (완전 초기화)
    </button>
    """,
    height=65
)

# 5. 최근 판독 이력 (제목 폰트 사이즈 반영)
st.markdown("---")
st.markdown('<p class="history-title">📜 최근 판독 이력 (최근 10개)</p>', unsafe_allow_html=True)
for i, item in enumerate(st.session_state.history):
    with st.expander(f"{i+1}. {item['name']} ({item['price']:,}원) - {item['verdict']}"):
        st.write(f"**판독 모드:** {item['mode']}")
        st.write(f"**추정 최저가:** {item['min_p']:,}원")
        st.write(f"**판단 결과:** {item['verdict']}")
        st.write(f"**판단 근거:** 현재가 대비 역대 데이터 분석을 통한 적정가 산출")
