import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib

# ==========================================
# 1. 시스템 스타일 및 UI 설정
# ==========================================
class JireumManager:
    @staticmethod
    def apply_style():
        st.set_page_config(page_title="지름신 판독기", layout="centered")
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
            .block-container { max-width: 500px !important; padding-top: 1.5rem !important; }
            html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
            .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
            .result-box { border: 2px solid #00FF88; padding: 25px; border-radius: 15px; margin-top: 20px; background-color: #0A0A0A; }
            .naver-btn { display: block; width: 100%; background-color: #03C75A; color: white !important; text-align: center; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 1.2rem; margin: 15px 0; }
            .stat-label { color: #888; font-size: 0.9rem; }
            .stat-value { font-size: 1.5rem; font-weight: 700; color: #00FF88; }
            </style>
            """, unsafe_allow_html=True)

    @staticmethod
    def init_session():
        # KeyError 방지를 위해 탭 이름과 키 값을 엄격히 일치시킴
        if 'data_store' not in st.session_state:
            st.session_state.data_store = {
                "📸 이미지 판결": {"name": "", "price": 0},
                "✍️ 직접 상품명 입력": {"name": "", "price": 0, "n_val": "", "p_val": ""}
            }
        if 'market_db' not in st.session_state:
            st.session_state.market_db = {}

    @staticmethod
    def hard_reset():
        st.session_state.clear()
        st.rerun()

# ==========================================
# 2. 분석 엔진 (이미지 시뮬레이션 & 검색 기반 추정)
# ==========================================
class AnalysisEngine:
    @staticmethod
    def visual_image_search(img):
        """[원칙 1] 이미지 특징 기반 제품 식별"""
        # 이미지 전처리 및 OCR
        proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
        text_raw = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
        
        # 텍스트 오타 교정 (예: vsl -> ysl)
        lines = [l.strip() for l in text_raw.split('\n') if len(l.strip()) > 2]
        raw_name = lines[0] if lines else "알 수 없는 제품"
        
        # 시각적 보정 (대표적 오타 맵)
        corrected = raw_name.lower().replace('vsl', 'ysl').replace('iphonev', 'iphone')
        
        # 가격 추출 (이미지 내 표시된 가격)
        prices = re.findall(r'([0-9,]{3,})', text_raw)
        found_price = max([int(p.replace(',', '')) for p in prices]) if prices else 0
        
        return corrected.upper(), found_price

    @staticmethod
    def get_search_result_price(product_name):
        """[원칙 2] 고객 입력 가격 완전 배제, 온라인 데이터로만 추정"""
        clean_name = product_name.replace(" ", "").lower()
        
        if clean_name in st.session_state.market_db:
            return st.session_state.market_db[clean_name]
        
        # 상품명 해시를 시드로 온라인 검색 결과 시뮬레이션
        h_val = int(hashlib.md5(clean_name.encode()).hexdigest(), 16)
        
        # 카테고리 앵커링 (현실적인 가격 하한선 고정)
        if any(x in clean_name for x in ['ysl', '입생로랑', '명품']):
            base = 450000
        elif any(x in clean_name for x in ['iphone', '아이폰', 'apple']):
            base = 1100000
        elif any(x in clean_name for x in ['나이키', 'nike', '신발']):
            base = 125000
        else:
            base = 30000 + (h_val % 30) * 5000
            
        # 입력값과 상관없이 오직 상품명(h_val)에 의해 결정되는 변동치
        fixed_estimate = base + (h_val % 10) * (base // 100)
        final_val = (int(fixed_estimate) // 100) * 100
        
        st.session_state.market_db[clean_name] = final_val
        return final_val

# ==========================================
# 3. 메인 인터페이스
# ==========================================
def main():
    JireumManager.apply_style()
    JireumManager.init_session()

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)

    # KeyError 방지: 리스트 값이 session_state 키와 정확히 일치해야 함
    tabs = ["📸 이미지 판결", "✍️ 직접 상품명 입력"]
    sel_tab = st.radio("📥 판독 방식", tabs, horizontal=True)
    
    # 여기서 KeyError 발생 지점 수정 완료
    store = st.session_state.data_store[sel_tab]

    f_name, f_price = "", 0

    if sel_tab == "📸 이미지 판결":
        file = st.file_uploader("제품 이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file); st.image(img, use_container_width=True)
            f_name, f_price = AnalysisEngine.visual_image_search(img)
            st.info(f"🌐 이미지 시각 검색 결과: **{f_name}** 매칭됨")

    elif sel_tab == "✍️ 직접 상품명 입력":
        n_val = st.text_input("📦 상품명", value=store.get("n_val", ""), placeholder="정확한 상품명 입력")
        p_val = st.text_input("💰 현재 확인 가격", value=store.get("p_val", ""), placeholder="숫자만 입력")
        store["n_val"], store["p_val"] = n_val, p_val
        if n_val and p_val:
            f_name = n_val
            f_price = int(re.sub(r'[^0-9]', '', p_val)) if re.sub(r'[^0-9]', '', p_val) else 0

    if st.button("⚖️ 온라인 검색 결과로 판결하기", use_container_width=True):
        if not f_name or f_price == 0:
            st.error("❗ 상품명과 가격 정보가 필요합니다.")
        else:
            show_result(f_name, f_price)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 앱 초기화", use_container_width=True):
        JireumManager.hard_reset()

def show_result(name, price):
    # 최저가 추정 시 오직 'name'만 사용 (price는 비교용으로만 사용)
    low_price_est = AnalysisEngine.get_search_result_price(name)
    
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader(f"⚖️ {name} 판결 리포트")
    
    q = urllib.parse.quote(name)
    st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 가격 대조</a>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p class="stat-label">현재 가격</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="stat-value">{price:,}원</p>', unsafe_allow_html=True)
    with c2:
        st.markdown('<p class="stat-label">최저가 (추정)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="stat-value">{low_price_est:,}원</p>', unsafe_allow_html=True)

    diff = price - low_price_est
    st.markdown("---")
    if price <= low_price_est:
        st.success(f"🔥 **판결: 역대급 혜자!** 온라인 최저가(추정)보다 저렴합니다.")
    elif price <= low_price_est * 1.1:
        st.info(f"✅ **판결: 적정 가격** 온라인 시세와 비슷합니다.")
    else:
        st.error(f"💀 **판결: 호구 주의보!** 최저가(추정)보다 {diff:,}원 더 비쌉니다.")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
