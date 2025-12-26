import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ==========================================
# 1. 커뮤니티 직접 탐색 엔진 (뽐뿌, 루리웹, 클리앙)
# ==========================================
class DirectCommunityEngine:
    @staticmethod
    def get_headers():
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @staticmethod
    def search_ppomppu(product_name):
        """뽐뿌 게시판 직접 검색"""
        query = urllib.parse.quote(product_name, encoding='euc-kr') # 뽐뿌는 euc-kr 사용 주의
        url = f"https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu&keyword={query}"
        try:
            res = requests.get(url, headers=DirectCommunityEngine.get_headers(), timeout=5)
            soup = BeautifulSoup(res.content, 'html.parser', from_encoding='euc-kr')
            # 게시글 제목 영역 추출
            titles = soup.find_all('font', class_='list_title')
            return [t.get_text() for t in titles]
        except: return []

    @staticmethod
    def search_ruliweb(product_name):
        """루리웹 핫딜 게시판 직접 검색"""
        query = urllib.parse.quote(product_name)
        url = f"https://bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={query}"
        try:
            res = requests.get(url, headers=DirectCommunityEngine.get_headers(), timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            titles = soup.find_all('a', class_='subject_inner_text')
            return [t.get_text() for t in titles]
        except: return []

    @staticmethod
    def extract_prices(text_list):
        """수집된 제목 리스트에서 가격 패턴 추출"""
        prices = []
        pattern = re.compile(r'([0-9,]{2,10})\s?(원|만)')
        for text in text_list:
            found = pattern.findall(text)
            for f_val, unit in found:
                num = int(f_val.replace(',', ''))
                if unit == '만': num *= 10000
                if 10000 < num < 20000000: prices.append(num)
        return sorted(prices)

# ==========================================
# 2. UI 스타일 및 리셋 (기존 원칙 유지)
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
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #00FF88; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    
    if st.button("🔄 리셋", use_container_width=True):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

    tabs = ["📸 이미지 판결", "✍️ 직접 상품명 입력"]
    sel_tab = st.radio("📥 판독 방식", tabs, horizontal=True)

    f_name, f_price = "", 0

    if sel_tab == "📸 이미지 판결":
        file = st.file_uploader("이미지 업로드", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
            text_raw = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            lines = [l.strip() for l in text_raw.split('\n') if len(l.strip()) > 2]
            f_name = lines[0] if lines else ""
    else:
        f_name = st.text_input("📦 상품명", placeholder="예: 아이폰 15")
        p_val = st.text_input("💰 현재 확인 가격", placeholder="숫자만 입력")
        if f_name and p_val: f_price = int(re.sub(r'[^0-9]', '', p_val))

    if st.button("⚖️ 커뮤니티 직접 탐색 판결 실행", use_container_width=True):
        if not f_name:
            st.error("❗ 상품명을 입력해주세요.")
        else:
            with st.spinner('🏘️ 커뮤니티 직접 탐색 중...'):
                # 뽐뿌 & 루리웹 데이터 수집
                p_titles = DirectCommunityEngine.search_ppomppu(f_name)
                r_titles = DirectCommunityEngine.search_ruliweb(f_name)
                all_prices = DirectCommunityEngine.extract_prices(p_titles + r_titles)
            
            if all_prices:
                low_price = all_prices[0]
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 판결")
                c1, c2 = st.columns(2)
                c1.metric("나의 확인가", f"{f_price:,}원")
                c2.metric("커뮤니티 최저가", f"{low_price:,}원")
                
                if f_price <= low_price:
                    st.success("🔥 역대급 딜! 커뮤니티 가격보다 저렴합니다.")
                else:
                    st.error(f"💀 주의! 커뮤니티 시세보다 {f_price - low_price:,}원 비쌉니다.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 커뮤니티에서 해당 제품의 가격 정보를 찾지 못했습니다. 상품명을 더 단순하게 입력해 보세요.")

if __name__ == "__main__":
    main()
