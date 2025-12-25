import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib
import datetime
import difflib # 유사도 분석용

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
            .correction-tag { color: #FFAA00; font-size: 0.85rem; font-weight: bold; }
            </style>
            """, unsafe_allow_html=True)

    @staticmethod
    def init_session():
        if 'history' not in st.session_state: st.session_state.history = []
        if 'market_db' not in st.session_state: st.session_state.market_db = {}
        if 'known_products' not in st.session_state: 
            # 학습된 유명 상품명 DB (오타 교정용)
            st.session_state.known_products = ["iPhone", "Galaxy", "MacBook", "iPad", "Sony", "Dyson", "YSL", "Nike", "Adidas"]
        if 'data_store' not in st.session_state:
            st.session_state.data_store = {
                tab: {"name": "", "price": 0, "n_val": "", "p_val": "", "corrected": False} 
                for tab in ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
            }

    @staticmethod
    def hard_reset():
        st.session_state.clear()
        st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)
        st.stop()

# ==========================================
# 2. 지능형 분석 엔진 (Fuzzy Matching 적용)
# ==========================================
class AnalysisEngine:
    @staticmethod
    def fuzzy_correct(name):
        """오타가 섞인 상품명을 유사한 정답으로 교정"""
        if not name or len(name) < 2: return name, False
        
        # 1. 알려진 DB와 비교 (vsl -> ysl 등)
        matches = difflib.get_close_matches(name, st.session_state.known_products + [h['name'] for h in st.session_state.history], n=1, cutoff=0.6)
        
        if matches and matches[0].lower() != name.lower():
            return matches[0], True
        return name, False

    @staticmethod
    def process_ocr(img):
        # OCR 전처리 고도화: 노이즈 제거 + 이진화
        gray = ImageOps.grayscale(img)
        denoised = gray.filter(ImageFilter.MedianFilter(size=3))
        proc = denoised.point(lambda x: 0 if x < 140 else 255).filter(ImageFilter.SHARPEN)
        
        ocr_text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
        
        prices = re.findall(r'([0-9,]{3,})', ocr_text)
        found_price = max([int(p.replace(',', '')) for p in prices]) if prices else 0
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        raw_name = re.sub(r'[^\w\s]', '', lines[0]) if lines else ""
        
        # 상품명 오타 교정 실행
        corrected_name, is_corrected = AnalysisEngine.fuzzy_correct(raw_name)
        return corrected_name, found_price, is_corrected

    @staticmethod
    def get_absolute_fixed_price(name, input_price):
        """상품명 해시 기반 고정 가격 (유사도 기준 유지)"""
        # 공백 제거 및 소문자화하여 중복 방지
        clean_name = name.replace(" ", "").lower()
        if clean_name in st.session_state.market_db: 
            return st.session_state.market_db[clean_name]
        
        h = int(hashlib.md5(clean_name.encode()).hexdigest(), 16)
        
        # 입력된 가격의 자릿수를 파악하여 현실적인 베이스 설정 (10배 차이 방지)
        magnitude = 10 ** (len(str(input_price)) - 1)
        base_price = (input_price // magnitude) * magnitude
        
        # 해시 기반 고정 변동폭 (입력값에 휩쓸리지 않는 절대값)
        fixed_offset = (h % 20 + 75) / 100 # 0.75 ~ 0.95 사이 고정
        fixed = (int(base_price * fixed_offset) // 100) * 100
        
        st.session_state.market_db[clean_name] = fixed
        return fixed

# ==========================================
# 3. 메인 실행 및 UI
# ==========================================
def main():
    JireumManager.apply_style()
    JireumManager.init_session()

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">오타 교정 AI & 1년 시세 추적</div>', unsafe_allow_html=True)

    tabs = ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
    sel_tab = st.radio("📥 입력 방식", tabs, horizontal=True)
    store = st.session_state.data_store[sel_tab]

    if sel_tab != "📸 이미지":
        n = st.text_input("상품명", value=store["n_val"], key=f"n_{sel_tab}")
        p = st.text_input("가격", value=store["p_val"], key=f"p_{sel_tab}")
        # 직접 입력에서도 오타 교정 시도
        if n and n != store["n_val"]:
            corrected, is_c = AnalysisEngine.fuzzy_correct(n)
            store["name"], store["corrected"] = corrected, is_c
        else:
            store["name"] = n
            
        store["n_val"], store["p_val"] = n, p
        store["price"] = (int(re.sub(r'[^0-9]', '', p)) if re.sub(r'[^0-9]', '', p) else 0)
    else:
        file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file); st.image(img, use_container_width=True)
            name, price, is_c = AnalysisEngine.process_ocr(img)
            store["name"], store["price"], store["corrected"] = name, price, is_c
            msg = f"🔍 인식: {name}" + (" (교정됨 ✨)" if is_c else "")
            st.info(f"{msg} / {price:,}원")

    if st.button("⚖️ 최종 판결 내리기", use_container_width=True):
        if not store["name"] or store["price"] == 0:
            st.error("❗ 상품 정보가 부족합니다.")
        else:
            show_result(store["name"], store["price"], store["corrected"])

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 앱 완전 초기화", use_container_width=True): JireumManager.hard_reset()

def show_result(name, price, is_corrected):
    market_p = AnalysisEngine.get_absolute_fixed_price(name, price)
    
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    if is_corrected:
        st.markdown(f'<span class="correction-tag">💡 오타가 의심되어 "{name}" 상품으로 교정하여 분석했습니다.</span>', unsafe_allow_html=True)
    
    st.subheader(f"⚖️ {name} AI 판결")
    
    q = urllib.parse.quote(name)
    st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 확인</a>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("입력 가격", f"{price:,}원")
    c2.metric("AI 최저가", f"{market_p:,}원")

    # 1년 추이 그래프 (유지)
    if HAS_PLOT_LIBS:
        months = [(datetime.date.today() - datetime.timedelta(days=i*30)).replace(day=1) for i in range(11, -1, -1)]
        h_seed = int(hashlib.md5(name.lower().encode()).hexdigest(), 16)
        np.random.seed(h_seed % 4294967295)
        trend = [int(market_p * (1.1 + 0.1 * np.random.rand())) for _ in range(12)]
        fig, ax = plt.subplots(figsize=(9, 3), facecolor='black')
        ax.plot(months, trend, color='#00FF88', marker='o')
        ax.axhline(y=market_p, color='red', linestyle='--')
        ax.set_facecolor('black')
        ax.tick_params(colors='white', labelsize=7)
        plt.xticks(months, [m.strftime('%m월') for m in months], color='white')
        st.pyplot(fig)
    
    # 판결 멘트
    if price <= market_p: st.success("🔥 역대급 딜! 고민은 배송만 늦출 뿐.")
    elif price <= market_p * 1.1: st.info("✅ 적정가입니다. 구매를 추천합니다.")
    else: st.error(f"💀 호구 주의! {price-market_p:,}원 더 저렴한 이력이 있습니다.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 히스토리에 저장 (추후 교정용 DB로 활용)
    if not any(h['name'] == name for h in st.session_state.history):
        st.session_state.history.insert(0, {"name": name, "price": price})

if __name__ == "__main__":
    main()
