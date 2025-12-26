import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ==========================================
# 1. 3대 커뮤니티 통합 직접 탐색 엔진
# ==========================================
class TripleCommunityEngine:
    @staticmethod
    def get_mobile_headers():
        return {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Referer": "https://m.ppomppu.co.kr/"
        }

    @staticmethod
    def search_ppomppu(product_name):
        query = urllib.parse.quote(product_name)
        url = f"https://m.ppomppu.co.kr/new/bbs_list.php?id=ppomppu&search_type=sub_memo&keyword={query}"
        try:
            res = requests.get(url, headers=TripleCommunityEngine.get_mobile_headers(), timeout=7)
            soup = BeautifulSoup(res.text, 'html.parser')
            titles = soup.select('.title')
            return [t.get_text(strip=True) for t in titles]
        except: return []

    @staticmethod
    def search_ruliweb(product_name):
        query = urllib.parse.quote(product_name)
        url = f"https://m.bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={query}"
        try:
            res = requests.get(url, headers=TripleCommunityEngine.get_mobile_headers(), timeout=7)
            soup = BeautifulSoup(res.text, 'html.parser')
            titles = soup.select('.subject_inner_text, .subject')
            return [t.get_text(strip=True) for t in titles]
        except: return []

    @staticmethod
    def search_clien(product_name):
        query = urllib.parse.quote(product_name)
        url = f"https://www.clien.net/service/search/board/jirum?sk=title&sv={query}"
        try:
            res = requests.get(url, headers=TripleCommunityEngine.get_mobile_headers(), timeout=7)
            soup = BeautifulSoup(res.text, 'html.parser')
            titles = soup.select('.list_subject .subject_fixed')
            return [t.get_text(strip=True) for t in titles]
        except: return []

    @staticmethod
    def extract_prices(texts):
        prices = []
        pattern = re.compile(r'([0-9,]{2,10})\s?(원|만)')
        for text in texts:
            found = pattern.findall(text)
            for f_val, unit in found:
                num = int(f_val.replace(',', ''))
                if unit == '만': num *= 10000
                if 10000 < num < 15000000: prices.append(num)
        return sorted(prices)

# ==========================================
# 2. UI 스타일 및 리셋 유틸리티
# ==========================================
def apply_custom_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
        .block-container { max-width: 500px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .result-box { border: 2px solid #00FF88; padding: 25px; border-radius: 15px; margin-top: 20px; background-color: #0A0A0A; }
        .stButton>button[kind="secondary"] { width: 100%; background-color: #333; color: white; border: none; }
        </style>
        """, unsafe_allow_html=True)

def reset_state():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# ==========================================
# 3. 메인 어플리케이션
# ==========================================
def main():
    apply_custom_style()
    
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)

    # [중대원칙] 우측 상단 리셋 버튼
    col_title, col_reset = st.columns([4, 1])
    with col_reset:
        if st.button("🔄 리셋", kind="secondary"):
            reset_state()

    # [중대원칙] 이미지 검색 및 직접 입력 탭
    tabs = ["📸 이미지 판결", "✍️ 직접 상품명 입력"]
    sel_tab = st.radio("📥 판독 방식 선택", tabs, horizontal=True)

    f_name, f_price = "", 0

    if sel_tab == "📸 이미지 판결":
        file = st.file_uploader("제품 이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            # OCR 전처리
            proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
            text_raw = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            lines = [l.strip() for l in text_raw.split('\n') if len(l.strip()) > 2]
            f_name = lines[0] if lines else ""
            if f_name: 
                st.info(f"🔍 이미지 인식 결과: **{f_name}**")
                # 이미지 인식 가격 입력창
                p_val_img = st.text_input("💰 확인하신 가격 입력", key="img_price")
                if p_val_img: f_price = int(re.sub(r'[^0-9]', '', p_val_img))

    elif sel_tab == "✍️ 직접 상품명 입력":
        f_name = st.text_input("📦 상품명 (예: 아이폰 15)", placeholder="쉼표(,)로 구분하면 더 정확합니다")
        p_val = st.text_input("💰 확인하신 가격", placeholder="숫자만 입력")
        if f_name and p_val:
            f_price = int(re.sub(r'[^0-9]', '', p_val))

    if st.button("⚖️ 통합 시세 판결 실행", use_container_width=True):
        if not f_name or f_price == 0:
            st.error("❗ 상품명과 가격을 모두 정확히 입력해주세요.")
        else:
            with st.spinner('🏘️ 3대 커뮤니티(뽐뿌, 루리웹, 클리앙) 기록을 분석 중입니다...'):
                # 병렬 탐색 시뮬레이션
                p_data = TripleCommunityEngine.search_ppomppu(f_name)
                r_data = TripleCommunityEngine.search_ruliweb(f_name)
                c_data = TripleCommunityEngine.search_clien(f_name)
                
                all_prices = TripleCommunityEngine.extract_prices(p_data + r_data + c_data)

            if all_prices:
                low_price = all_prices[0]
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 시세 분석 결과")
                c1, c2 = st.columns(2)
                c1.metric("나의 확인가", f"{f_price:,}원")
                c2.metric("역대 기록 최저가", f"{low_price:,}원")
                
                diff = f_price - low_price
                if diff <= 0:
                    st.success("🔥 **역대급 딜!** 기록된 시세보다 저렴합니다. 지금 사세요!")
                else:
                    st.error(f"💀 **주의!** 역대 기록보다 {diff:,}원 더 비쌉니다.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 커뮤니티 기록을 찾지 못했습니다. 키워드에 쉼표를 사용해 다시 시도해보세요 (예: 아이폰, 15).")

if __name__ == "__main__":
    main()
