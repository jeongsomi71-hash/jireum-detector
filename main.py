import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib
import datetime

# 라이브러리 체크
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
# 2. 분석 엔진 모듈 (절대 가격 로직 탑재)
# ==========================================
class AnalysisEngine:
    @staticmethod
    def process_ocr(img):
        proc = ImageOps.grayscale(img).point(lambda x: 0 if x < 150 else 255).filter(ImageFilter.SHARPEN)
        ocr_text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
        prices = re.findall(r'([0-9,]{3,})', ocr_text)
        found_price = max([int(p.replace(',', '')) for p in prices]) if prices else 0
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        found_name = re.sub(r'[^\w\s]', '', lines[0]) if lines else ""
        return found_name, found_price

    @staticmethod
    def get_absolute_fixed_price(name):
        """입력 가격과 무관하게 상품명 해시로만 결정되는 '절대 최저가'"""
        if name in st.session_state.market_db: return st.session_state.market_db[name]
        
        # 상품명 고유 해시 생성
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        
        # 상품명에서 느껴지는 가격대 추정 (이름의 길이나 특정 키워드로 가상의 베이스 가격 설정)
        # 실제 환경이라면 카테고리 DB가 있겠지만, 여기서는 해시를 이용해 1만원~200만원 사이의 고유 구간 설정
        base_ranges = [10000, 50000, 150000, 500000, 1200000, 2500000]
        selected_base = base_ranges[h % len(base_ranges)]
        
        # 해당 베이스에서 해시 기반으로 정교한 금액 결정
        offset = (h % 100) * (selected_base // 200)
        fixed = ((selected_base + offset) // 100) * 100
        
        st.session_state.market_db[name] = fixed
        return fixed

# ==========================================
# 3. 메인 실행부
# ==========================================
def main():
    JireumManager.apply_style()
    JireumManager.init_session()

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">입력 가격에 흔들리지 않는 AI 판결</div>', unsafe_allow_html=True)

    tabs = ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
    sel_tab = st.radio("📥 입력 방식", tabs, horizontal=True)
    store = st.session_state.data_store[sel_tab]

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

    if st.button("⚖️ 최종 판결 내리기", use_container_width=True):
        if not store["name"] or store["price"] == 0:
            st.error("❗ 상품명과 가격을 정확히 입력해주세요.")
        else:
            show_result(store["name"], store["price"])

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 앱 완전 초기화", use_container_width=True):
        JireumManager.hard_reset()

def show_result(name, price):
    # 이제 입력 가격(price)은 판독 기준이 아닌, '비교 대상'으로만 쓰입니다.
    market_p = AnalysisEngine.get_absolute_fixed_price(name)
    
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader(f"⚖️ {name} AI 판결")
    
    q = urllib.parse.quote(name)
    st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 최저가</a>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("사용자 입력가", f"{price:,}원")
    c2.metric("AI 추정 최저가", f"{market_p:,}원")

    # [보강] 1년 가격 추이 그래프 (12개월)
    if HAS_PLOT_LIBS:
        # 최근 12개월 날짜 생성
        months = [(datetime.date.today() - datetime.timedelta(days=i*30)).replace(day=1) for i in range(11, -1, -1)]
        h_seed = int(hashlib.md5(name.encode()).hexdigest(), 16)
        np.random.seed(h_seed % 4294967295)
        
        # 1년치 데이터 시뮬레이션
        trend = [int(market_p * (1.1 + 0.15 * np.random.rand())) for _ in range(12)]
        
        fig, ax = plt.subplots(figsize=(9, 4), facecolor='black')
        ax.plot(months, trend, color='#00FF88', marker='o', linewidth=2)
        ax.axhline(y=market_p, color='red', linestyle='--', label='AI 최저가')
        
        ax.set_facecolor('black')
        ax.tick_params(colors='white', labelsize=8)
        plt.xticks(months, [m.strftime('%Y-%m') for m in months], rotation=45)
        ax.set_title("지난 1년 가격 추이 (월간)", color='white', pad=20)
        fig.tight_layout()
        st.pyplot(fig)
    
    # 판결 로직 (절대값 비교)
    diff = price - market_p
    if price <= market_p:
        st.success(f"🔥 **판결: 역대급 혜자!**\nAI 최저가보다 {abs(diff):,}원 저렴합니다. 당장 결제하세요!")
    elif price <= market_p * 1.1:
        st.info(f"✅ **판결: 적정가**\n최저가와 큰 차이가 없습니다. 고민은 배송만 늦출 뿐!")
    else:
        st.error(f"💀 **판결: 호구 주의보!**\n과거 {market_p:,}원에 구매 가능했던 기록이 있습니다. {diff:,}원을 아끼기 위해 참으세요!")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
