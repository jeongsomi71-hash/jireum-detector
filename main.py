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
        """뽐뿌 모바일 핫딜 검색"""
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
        """루리웹 모바일 핫딜 검색"""
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
        """클리앙 알뜰구매 게시판 검색 (추가됨)"""
        query = urllib.parse.quote(product_name)
        # 클리앙 모바일 알뜰구매 게시판 URL
        url = f"https://www.clien.net/service/search/board/jirum?sk=title&sv={query}"
        try:
            res = requests.get(url, headers=TripleCommunityEngine.get_mobile_headers(), timeout=7)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 클리앙 게시글 제목 클래스
            titles = soup.select('.list_subject .subject_fixed')
            return [t.get_text(strip=True) for t in titles]
        except: return []

    @staticmethod
    def extract_prices(texts):
        """수집된 모든 제목에서 가격 정보 추출"""
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
# 2. 메인 UI 및 판독 로직
# ==========================================
def apply_custom_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        .block-container { max-width: 500px !important; }
        html, body, [class*="css"] { background-color: #000; color: #fff; font-family: 'Noto Sans KR'; }
        .unified-header { background: #fff; color: #000; text-align: center; padding: 20px; border-radius: 12px; font-weight: 900; border: 4px solid #00FF88; margin-bottom: 20px; }
        .result-box { border: 2px solid #00FF88; padding: 20px; border-radius: 15px; background: #0A0A0A; margin-top: 15px; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)

    f_name = st.text_input("📦 상품명 입력", placeholder="예: 아이폰 15 프로")
    f_price_raw = st.text_input("💰 확인하신 가격", placeholder="숫자만 입력")

    if st.button("🔍 3대 커뮤니티 역대 시세 분석 시작", use_container_width=True):
        if not f_name or not f_price_raw:
            st.error("❗ 상품명과 가격을 입력해주세요.")
        else:
            f_price = int(re.sub(r'[^0-9]', '', f_price_raw))
            
            with st.spinner('🏘️ 뽐뿌, 루리웹, 클리앙 시세를 뒤지는 중...'):
                p_titles = TripleCommunityEngine.search_ppomppu(f_name)
                r_titles = TripleCommunityEngine.search_ruliweb(f_name)
                c_titles = TripleCommunityEngine.search_clien(f_name)
                
                all_titles = p_titles + r_titles + c_titles
                all_prices = TripleCommunityEngine.extract_prices(all_titles)

            if all_prices:
                low_price = all_prices[0] # 가장 낮은 가격을 역대 최저가로 간주
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 판결 리포트")
                st.write(f"나의 확인가: **{f_price:,}원**")
                st.write(f"역대 기록 시세: **{low_price:,}원**")
                
                if f_price <= low_price:
                    st.success("🔥 역대급 딜입니다! 즉시 구매를 추천합니다.")
                else:
                    diff = f_price - low_price
                    st.error(f"❌ 참으세요! 최저가보다 {diff:,}원 더 비쌉니다.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 커뮤니티에서 가격 정보를 찾지 못했습니다. 키워드를 더 단순하게 바꿔보세요.")

if __name__ == "__main__":
    main()
