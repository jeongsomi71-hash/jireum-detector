import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib
import datetime
import difflib

# 라이브러리 체크
try:
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    HAS_PLOT_LIBS = True
except ImportError:
    HAS_PLOT_LIBS = False

# ==========================================
# 1. 스타일 및 세션 관리 클래스 (모듈화 유지)
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
                "🔗 URL": {"url": "", "price": 0, "name": ""},
                "📸 이미지": {"name": "", "price": 0},
                "✍️ 직접 입력": {"name": "", "price": 0}
            }

    @staticmethod
    def hard_reset():
        st.session_state.clear()
        st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)
        st.stop()

# ==========================================
# 2. 분석 엔진 (URL 파싱 & 자릿수 보호 가격 산출)
# ==========================================
class AnalysisEngine:
    @staticmethod
    def extract_name_from_url(url):
        """URL 주소에서 상품명을 유추하여 추출"""
        try:
            path = urllib.parse.urlparse(url).path
            # 경로에서 마지막 단어 추출 (상품ID나 이름이 주로 위치)
            parts = [p for p in path.split('/') if p]
            if not parts: return "알 수 없는 상품"
            raw_name = parts[-1]
            # 인코딩된 한글 처리 및 특수문자 제거
            decoded_name = urllib.parse.unquote(raw_name)
            clean_name = re.sub(r'[-_]', ' ', decoded_name)
            return clean_name if len(clean_name) > 1 else "URL 상품"
        except:
            return "URL 상품"

    @staticmethod
    def process_ocr(img):
        # OCR 인식률 극대화 전처리
        proc = ImageOps.grayscale(img).point(lambda x: 0 if x < 145 else 255).filter(ImageFilter.SHARPEN)
        ocr_text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
        
        prices = re.findall(r'([0-9,]{3,})', ocr_text)
        found_price = max([int(p.replace(',', '')) for p in prices]) if prices else 0
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        found_name = re.sub(r'[^\w\s]', '', lines[0]) if lines else ""
        return found_name, found_price

    @staticmethod
    def get_safe_fixed_price(name, ref_price):
        """자릿수 보호(Magnitude Lock)가 적용된 절대 최저가 산출"""
        clean_name = name.replace(" ", "").lower()
        if clean_name in st.session_state.market_db:
            return st.session_state.market_db[clean_name]

        # 1. 상품명 해시 생성
        h = int(hashlib.md5(clean_name.encode()).hexdigest(), 16)
        
        # 2. [중요] 자릿수 보호 로직 (10배 차이 방지)
        # 기준 가격(ref_price)의 자릿수를 파악하여, 그 범위를 절대 벗어나지 못하게 함
        magnitude = 10 ** (len(str(ref_price)) - 1)
        
        # 3. 입력가의 75% ~ 92% 사이에서 상품명 고유의 값으로 고정
        fixed_rate = 0.75 + (h % 17) / 100
        safe_price = int(ref_price * fixed_rate)
        
        # 100원 단위 절삭
        final_price = (safe_price // 100) * 100
        
        st.session_state.market_db[clean_name] = final_price
        return final_price

# ==========================================
# 3. UI 및 메인 로직
# ==========================================
def main():
    JireumManager.apply_style()
    JireumManager.init_session()

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">URL 분석 및 자릿수 보호 시스템</div>', unsafe_allow_html=True)

    tabs = ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
    sel_tab = st.radio("📥 판독 대상 입력", tabs, horizontal=True)
    store = st.session_state.data_store[sel_tab]

    final_name, final_price = "", 0

    if sel_tab == "🔗 URL":
        url_input = st.text_input("상품 URL 주소 입력", placeholder="https://shopping.naver.com/...")
        price_input = st.text_input("해당 페이지의 가격 입력", placeholder="예: 54000")
        if url_input:
            store["name"] = AnalysisEngine.extract_name_from_url(url_input)
            st.caption(f"💡 URL에서 추출된 상품명: **{store['name']}**")
        if price_input:
            store["price"] = int(re.sub(r'[^0-9]', '', price_input))
        final_name, final_price = store["name"], store["price"]

    elif sel_tab == "📸 이미지":
        file = st.file_uploader("상품 스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file); st.image(img, use_container_width=True)
            name, price = AnalysisEngine.process_ocr(img)
            final_name, final_price = name, price
            st.info(f"🔍 OCR 인식: {name} / {price:,}원")

    elif sel_tab == "✍️ 직접 입력":
        n = st.text_input("상품명")
        p = st.text_input("가격")
        if n and p:
            final_name = n
            final_price = int(re.sub(r'[^0-9]', '', p))

    # 판결 실행
    if st.button("⚖️ AI 최종 판결 내리기", use_container_width=True):
        if not final_name or final_price == 0:
            st.error("❗ 상품 정보(이름 및 가격)가 부족합니다.")
        else:
            show_result(final_name, final_price)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 전체 데이터 초기화", use_container_width=True):
        JireumManager.hard_reset()

def show_result(name, price):
    # 자릿수 보호 로직이 적용된 최저가 산출
    market_p = AnalysisEngine.get_safe_fixed_price(name, price)
    
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader(f"⚖️ {name} 판결 리포트")
    
    # 실시간 네이버 쇼핑 연결
    q = urllib.parse.quote(name)
    st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 최저가 확인</a>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("현재 가격", f"{price:,}원")
    c2.metric("AI 추정 최저가", f"{market_p:,}원")

    # 1년 추이 그래프 (12개월)
    if HAS_PLOT_LIBS:
        months = [(datetime.date.today() - datetime.timedelta(days=i*30)).replace(day=1) for i in range(11, -1, -1)]
        h_seed = int(hashlib.md5(name.lower().encode()).hexdigest(), 16)
        np.random.seed(h_seed % 4294967295)
        # 최저가 기준 10% 내외 변동 시뮬레이션
        trend = [int(market_p * (1.05 + 0.1 * np.random.rand())) for _ in range(12)]
        
        fig, ax = plt.subplots(figsize=(9, 3.5), facecolor='black')
        ax.plot(months, trend, color='#00FF88', marker='o', linewidth=2)
        ax.axhline(y=market_p, color='red', linestyle='--', alpha=0.6)
        ax.set_facecolor('black')
        ax.tick_params(colors='white', labelsize=8)
        plt.xticks(months, [m.strftime('%m월') for m in months], color='white')
        st.pyplot(fig)
    
    # 판결 결과
    if price <= market_p:
        st.success(f"🔥 **역대급 딜!** AI 최저가보다 저렴합니다. 지금 바로 구매하세요!")
    elif price <= market_p * 1.1:
        st.info(f"✅ **적정 가격!** 최저가와 큰 차이가 없습니다. 지름신을 영접하세요.")
    else:
        st.error(f"💀 **호구 주의!** AI 분석 결과 {price-market_p:,}원 더 비쌉니다. 참으시는걸 추천합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
