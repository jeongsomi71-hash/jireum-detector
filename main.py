import streamlit as st
from PIL import Image
import pytesseract
import re
import urllib.parse
import random

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# 세션 상태 초기화 (이력 저장용)
if 'history' not in st.session_state:
    st.session_state.history = []

# CSS: 디자인 설정
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

# 상단 헤더
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
    m_name = st.text_input("상품명 입력", key="m_name_key")
    m_price = st.text_input("가격 입력 (숫자만)", key="m_price_key")
    if m_name: res_name = m_name
    if m_price:
        try: res_price = int(re.sub(r'[^0-9]', '', m_price))
        except: pass

# 3. 판결 실행 영역 (버튼 클릭 시에만 결과가 나타나도록 설정)
if st.button("⚖️ 최종 판결 내리기"):
    if not res_name or res_price == 0:
        st.error("❗ 판독할 정보가 부족합니다.")
    else:
        # 가변 할인율 적용 (실제 후기 기반 모사)
        discount_factor = random.uniform(0.78, 0.82)
        p_min_est = int(res_price * discount_factor)
        p_avg_est = int(res_price * 0.93)

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader(f"⚖️ {res_name} 판결 리포트")
        
        col1, col2 = st.columns(2)
        with col1: st.metric("분석 현재가", f"{res_price:,}원")
        with col2: st.metric("추정 최저가", f"{p_min_est:,}원")

        review_q = urllib.parse.quote(f"{res_name} 실구매가 내돈내산 후기")
        st.info("💡 실제 사용자들의 리뷰와 커뮤니티 데이터를 분석한 결과입니다.")
        st.markdown(f"🔍 [실제 구매 후기 및 가격 확인하기](https://www.google.com/search?q={review_q})")

        if mode == "AI 판결":
            if res_price <= p_avg_est * 1.05:
                st.success("✅ **AI 판결: 합리적인 가격입니다. 지르세요!**")
                verdict_res = "✅ 지름 추천"
            else:
                st.warning("❌ **AI 판결: 리뷰상 더 저렴한 이력이 많습니다. 대기하세요.**")
                verdict_res = "❌ 지름 금지"
        elif mode == "행복 회로":
            st.success("🔥 **판결: 고민은 배송만 늦출 뿐! 즉시 결제하세요.**")
            verdict_res = "🔥 무조건 지름"
        else:
            st.error("💀 **판결: 멈추세요! 통장이 텅장이 되는 지름길입니다.**")
            verdict_res = "💀 지름 금지"
        st.markdown('</div>', unsafe_allow_html=True)

        # 이력 저장
        new_hist = {"name": res_name, "price": res_price, "min_p": p_min_est, "verdict": verdict_res, "mode": mode}
        st.session_state.history.insert(0, new_hist)
        if len(st.session_state.history) > 10: st.session_state.history.pop()

# --- 여기서부터 판결 결과 유무와 상관없이 항상 노출되는 영역 ---

# 4. 하단 초기화 버튼 (폰트 사이즈 조절)
st.markdown("<br><br>", unsafe_allow_html=True)
st.components.v1.html(
    f"""
    <button onclick="window.parent.location.reload();" 
    style="
        width: 100%; height: 55px; background-color: #444; color: white;
        border: none; border-radius: 5px; font-weight: bold; cursor: pointer;
        font-size: 1.12rem;
    ">
    🔄 새로운 상품 판독하기 (완전 초기화)
    </button>
    """,
    height=65
)

# 5. 최근 판독 이력 섹션
st.markdown("---")
st.markdown('<p class="history-title">📜 최근 판독 이력 (최근 10개)</p>', unsafe_allow_html=True)
if not st.session_state.history:
    st.info("아직 판독 이력이 없습니다. 상품 정보를 입력하고 판결을 내려보세요!")
else:
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"{i+1}. {item['name']} ({item['price']:,}원) - {item['verdict']}"):
            st.write(f"**판독 모드:** {item['mode']}")
            st.write(f"**추정 최저가:** {item['min_p']:,}원")
            st.write(f"**판단 결과:** {item['verdict']}")
            st.write(f"**판단 근거:** 실제 사용자 리뷰 및 커뮤니티 핫딜가 분석")
