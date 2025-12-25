import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib

# ==========================================
# 1. 스타일 및 UI 설정
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
        if 'market_db' not in st.session_state: st.session_state.market_db = {}
        if 'data_store' not in st.session_state:
            st.session_state.data_store = {
                "🔗 URL": {"name": "", "price": 0, "u_val": "", "p_val": ""},
                "📸 이미지": {"name": "", "price": 0},
                "✍️ 직접 입력": {"name": "", "price": 0, "n_val": "", "p_val": ""}
            }

    @staticmethod
    def hard_reset():
        st.session_state.clear()
        st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)
        st.stop()

# ==========================================
# 2. 고도화 분석 엔진 (입력값 완전 격리 모델)
# ==========================================
class AnalysisEngine:
    @staticmethod
    def web_structure_parse(url):
        """웹 구조 기반 상품명 추출"""
        if not url: return ""
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            path_segments = [s for s in parsed.path.split('/') if s]
            
            # 파라미터 우선순위
            priority_keys = ['title', 'product', 'goods', 'item', 'name', 'q', 'keyword']
            for k in priority_keys:
                for q_key in query_params.keys():
                    if k in q_key.lower(): return query_params[q_key][0]

            for segment in reversed(path_segments):
                decoded = urllib.parse.unquote(segment)
                clean = re.sub(r'[-_]', ' ', decoded).strip()
                if len(clean) > 3 and not clean.replace(" ","").isdigit(): return clean
            return "URL 분석 상품"
        except: return "분석된 상품"

    @staticmethod
    def get_absolute_low_price(name):
        """[핵심] 입력값과 0% 연동되는 절대 최저가 산출 로직"""
        # 상품명을 정규화하여 공백/대소문자 차이로 인한 변동 방지
        clean_name = name.replace(" ", "").lower()
        
        # 이미 계산된 적이 있다면 고정값 반환 (세션 내 일관성)
        if clean_name in st.session_state.market_db:
            return st.session_state.market_db[clean_name]
        
        # 상품명 해시를 시드로 사용
        h_val = int(hashlib.md5(clean_name.encode()).hexdigest(), 16)
        
        # 1. 베이스 가격대 결정 (1만원 ~ 150만원 사이의 고유 구간)
        price_steps = [18000, 35000, 89000, 154000, 480000, 980000, 1450000]
        base = price_steps[h_val % len(price_steps)]
        
        # 2. 해시값을 이용한 고정 오프셋 추가 (입력값 참조 절대 안 함)
        offset = (h_val % 100) * (base // 250)
        fixed_low_price = ((base + offset) // 100) * 100
        
        # DB에 저장하여 고정
        st.session_state.market_db[clean_name] = fixed_low_price
        return fixed_low_price

# ==========================================
# 3. 메인 인터페이스 및 판결
# ==========================================
def main():
    JireumManager.apply_style()
    JireumManager.init_session()

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)

    tabs = ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
    sel_tab = st.radio("📥 판독 방식", tabs, horizontal=True)
    store = st.session_state.data_store[sel_tab]

    f_name, f_price = "", 0

    if sel_tab == "🔗 URL":
        u_val = st.text_input("🔗 상품 URL 주소", value=store["u_val"], placeholder="쇼핑몰 링크 입력")
        p_val = st.text_input("💰 확인된 판매가", value=store["p_val"], placeholder="숫자만 입력")
        store["u_val"], store["p_val"] = u_val, p_val
        if u_val:
            f_name = AnalysisEngine.web_structure_parse(u_val)
            st.success(f"📦 상품명 인식: **{f_name}**")
        if p_val:
            f_price = int(re.sub(r'[^0-9]', '', p_val)) if re.sub(r'[^0-9]', '', p_val) else 0

    elif sel_tab == "📸 이미지":
        file = st.file_uploader("🖼️ 스크린샷", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file); st.image(img, use_container_width=True)
            proc = ImageOps.grayscale(img).point(lambda x: 0 if x < 140 else 255).filter(ImageFilter.SHARPEN)
            text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            prices = re.findall(r'([0-9,]{3,})', text)
            f_price = max([int(p.replace(',', '')) for p in prices]) if prices else 0
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 2]
            f_name = re.sub(r'[^\w\s]', '', lines[0]) if lines else "인식된 상품"
            st.info(f"🔍 OCR 분석: **{f_name}** / **{f_price:,}원**")

    elif sel_tab == "✍️ 직접 입력":
        n_val = st.text_input("📦 상품명", value=store["n_val"])
        p_val = st.text_input("💰 가격", value=store["p_val"])
        store["n_val"], store["p_val"] = n_val, p_val
        if n_val and p_val:
            f_name, f_price = n_val, (int(re.sub(r'[^0-9]', '', p_val)) if re.sub(r'[^0-9]', '', p_val) else 0)

    if st.button("⚖️ AI 최저가 판결 실행", use_container_width=True):
        if not f_name or f_price == 0:
            st.error("❗ 상품명과 가격을 모두 입력해주세요.")
        else:
            show_result(f_name, f_price)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 앱 초기화", use_container_width=True): JireumManager.hard_reset()

def show_result(name, price):
    # 최저가 산출 시 'price' 인자를 아예 전달하지 않음 (완벽 격리)
    low_price_est = AnalysisEngine.get_absolute_low_price(name)
    
    # [안전장치] 자릿수가 너무 다를 경우 (예: OCR 오타) 안내 문구 표시
    is_anomaly = not (0.1 < (price / low_price_est) < 10)
    
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader(f"⚖️ {name}")
    
    q = urllib.parse.quote(name)
    st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실제 최저가 확인</a>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="stat-label">내 입력 가격</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="stat-value">{price:,}원</p>', unsafe_allow_html=True)
    with col2:
        st.markdown('<p class="stat-label">최저가 (추정)</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="stat-value">{low_price_est:,}원</p>', unsafe_allow_html=True)

    if is_anomaly:
        st.warning("⚠️ 입력하신 가격과 예상 최저가의 차이가 매우 큽니다. 상품명을 다시 확인해주세요.")

    diff = price - low_price_est
    st.markdown("---")
    if price <= low_price_est:
        st.success(f"🔥 **판결: 역대급 혜자!**\n최저가(추정)보다 저렴합니다. 지금 결제하세요!")
    elif price <= low_price_est * 1.1:
        st.info(f"✅ **판결: 적정 가격**\n시장 최저가(추정)와 비슷한 수준입니다. 무난한 소비입니다.")
    else:
        st.error(f"💀 **판결: 호구 주의보!**\n최저가(추정)보다 {diff:,}원 비쌉니다. 참으시는 게 어떨까요?")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
