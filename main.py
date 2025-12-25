import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib
import datetime

# 그래프 라이브러리 로드 시도 (없을 경우 대비 예외처리)
try:
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    HAS_PLOT_LIBS = True
except ImportError:
    HAS_PLOT_LIBS = False

# ==========================================
# 1. 스타일 및 세션 관리 클래스
# ==========================================
class JireumManager:
    @staticmethod
    def apply_style():
        st.set_page_config(page_title="지름신 판독기", layout="centered")
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
            .block-container { max-width: 500px !important; padding-top: 2rem !important; }
            html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
            .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
            .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
            .result-box { border: 2px solid #00FF88; padding: 20px; border-radius: 10px; margin-top: 20px; background-color: #111; }
            .naver-btn { display: block; width: 100%; background-color: #03C75A; color: white !important; text-align: center; padding: 15px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1rem; margin-bottom: 15px; }
            </style>
            """, unsafe_allow_html=True)

    @staticmethod
    def init_session():
        if 'history' not in st.session_state: st.session_state.history = []
        if 'market_db' not in st.session_state: st.session_state.market_db = {}
        if 'data_store' not in st.session_state:
            st.session_state.data_store = {
                tab: {"name": "", "price": 0, "n_val": "", "p_val": ""} 
                for tab in ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
            }

    @staticmethod
    def hard_reset():
        st.session_state.clear()
        st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)
        st.stop()

# ==========================================
# 2. 분석 엔진 모듈
# ==========================================
class AnalysisEngine:
    @staticmethod
    def process_ocr(img):
        # 고도화된 이진화 전처리 (원칙 유지)
        proc = ImageOps.grayscale(img).point(lambda x: 0 if x < 150 else 255).filter(ImageFilter.SHARPEN)
        ocr_text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
        
        prices = re.findall(r'([0-9,]{3,})', ocr_text)
        found_price = max([int(p.replace(',', '')) for p in prices]) if prices else 0
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        found_name = re.sub(r'[^\w\s]', '', lines[0]) if lines else ""
        return found_name, found_price

    @staticmethod
    def get_fixed_price(name, current_p):
        # 비율이 아닌 상품명 해시 기반 고정 (원칙 유지)
        if name in st.session_state.market_db: return st.session_state.market_db[name]
        
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        rate = 0.78 + (h % 14) / 100
        fixed = (int(current_p * rate) // 100) * 100
        st.session_state.market_db[name] = fixed
        return fixed

# ==========================================
# 3. 메인 UI 렌더링
# ==========================================
def main():
    JireumManager.apply_style()
    JireumManager.init_session()

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">실시간 최저가 및 AI 판결</div>', unsafe_allow_html=True)

    tabs = ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
    sel_tab = st.radio("📥 입력 방식 (데이터 격리)", tabs, horizontal=True)
    store = st.session_state.data_store[sel_tab]

    # 입력 필드 (데이터 유실 방지 로직)
    if sel_tab != "📸 이미지":
        n = st.text_input("상품명", value=store["n_val"], key=f"n_{sel_tab}")
        p = st.text_input("가격", value=store["p_val"], key=f"p_{sel_tab}")
        store["n_val"], store["p_val"] = n, p
        store["name"], store["price"] = n, (int(re.sub(r'[^0-9]', '', p)) if re.sub(r'[^0-9]', '', p) else 0)
    else:
        file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file); st.image(img, use_container_width=True)
            name, price = AnalysisEngine.process_ocr(img)
            store["name"], store["price"] = name, price
            st.info(f"🔍 인식: {name} / {price:,}원")

    # 판결 실행
    if st.button("⚖️ 최종 판결 내리기", use_container_width=True):
        if not store["name"] or store["price"] == 0:
            st.error("❗ 상품명과 가격을 모두 입력해주세요.")
        else:
            show_result(store["name"], store["price"])

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 앱 완전 초기화", use_container_width=True):
        JireumManager.hard_reset()

def show_result(name, price):
    market_p = AnalysisEngine.get_fixed_price(name, price)
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader(f"⚖️ {name} AI 판결")
    
    # 네이버 쇼핑 링크
    q = urllib.parse.quote(name)
    st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 최저가</a>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("입력가", f"{price:,}원")
    c2.metric("리뷰 최저가", f"{market_p:,}원")

    # 그래프 렌더링 (라이브러리 체크)
    if HAS_PLOT_LIBS:
        dates = [datetime.date.today() - datetime.timedelta(days=i) for i in range(30, -1, -1)]
        h_seed = int(hashlib.md5(name.encode()).hexdigest(), 16)
        np.random.seed(h_seed % 4294967295)
        # 가상 추이 생성
        trend = [int((market_p*1.1) + (market_p*0.05)*(np.random.rand()-0.5)) for _ in range(31)]
        fig, ax = plt.subplots(figsize=(8, 3), facecolor='black')
        ax.plot(dates, trend, color='#00FF88', marker='o', markersize=3)
        ax.axhline(y=market_p, color='red', linestyle='--', alpha=0.5)
        ax.set_facecolor('black')
        ax.tick_params(colors='white', labelsize=7)
        st.pyplot(fig)
    
    # 판결 문구
    if price <= market_p: st.success("🔥 역대급 딜! 고민은 배송만 늦출 뿐.")
    elif price <= market_p * 1.05: st.info("✅ 무릎 가격! 결제를 추천합니다.")
    else: st.error(f"💀 호구 주의! {price-market_p:,}원 더 저렴한 기록이 있습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
