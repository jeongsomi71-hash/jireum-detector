import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import time

# ==========================================
# 1. 고성능 커뮤니티 직접 탐색 엔진 (모바일 우회)
# ==========================================
class MobileDirectEngine:
    @staticmethod
    def get_mobile_headers():
        # 모바일 브라우저(iPhone)로 완벽하게 위장하여 자바스크립트 검사를 우회합니다.
        return {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            "Referer": "https://m.ppomppu.co.kr/"
        }

    @staticmethod
    def search_ppomppu(product_name):
        """뽐뿌 모바일 페이지 직접 검색"""
        # 모바일 뽐뿌는 UTF-8을 지원하므로 인코딩 문제가 적습니다.
        query = urllib.parse.quote(product_name)
        url = f"https://m.ppomppu.co.kr/new/bbs_list.php?id=ppomppu&search_type=sub_memo&keyword={query}"
        
        try:
            res = requests.get(url, headers=MobileDirectEngine.get_mobile_headers(), timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 모바일 뽐뿌의 게시글 제목 클래스 추출
            titles = soup.select('.title')
            return [t.get_text(strip=True) for t in titles]
        except:
            return []

    @staticmethod
    def search_ruliweb(product_name):
        """루리웹 모바일 핫딜 게시판 직접 검색"""
        query = urllib.parse.quote(product_name)
        url = f"https://m.bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={query}"
        
        try:
            res = requests.get(url, headers=MobileDirectEngine.get_mobile_headers(), timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 루리웹 모바일 제목 추출
            titles = soup.select('.subject_inner_text, .subject')
            return [t.get_text(strip=True) for t in titles]
        except:
            return []

    @staticmethod
    def extract_lowest_price(texts):
        """수집된 텍스트 중 가장 낮은 가격(역대 최저가 후보) 추출"""
        prices = []
        # 숫자와 '원' 또는 '만'이 붙은 패턴 탐색
        pattern = re.compile(r'([0-9,]{2,10})\s?(원|만)')
        
        for text in texts:
            found = pattern.findall(text)
            for f_val, unit in found:
                num = int(f_val.replace(',', ''))
                if unit == '만': num *= 10000
                # 1만원 미만이나 1000만원 이상은 노이즈로 간주
                if 10000 < num < 10000000:
                    prices.append(num)
        
        return min(prices) if prices else None

# ==========================================
# 2. UI 및 로직 통합
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
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)
    
    if st.button("🔄 검색 초기화"):
        st.rerun()

    f_name = st.text_input("📦 판독할 상품명", placeholder="예: 아이폰 15 프로")
    f_price_raw = st.text_input("💰 현재 내가 본 가격", placeholder="숫자만 입력")

    if st.button("🔍 커뮤니티 역대 시세 분석", use_container_width=True):
        if not f_name or not f_price_raw:
            st.error("❗ 상품명과 가격을 모두 입력해주세요.")
        else:
            f_price = int(re.sub(r'[^0-9]', '', f_price_raw))
            
            with st.spinner('📱 모바일 우회 채널로 커뮤니티 데이터를 긁어오는 중...'):
                # 뽐뿌 모바일 & 루리웹 모바일 동시 타격
                p_data = MobileDirectEngine.search_ppomppu(f_name)
                r_data = MobileDirectEngine.search_ruliweb(f_name)
                
                low_price = MobileDirectEngine.extract_lowest_price(p_data + r_data)

            if low_price:
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 판결: {f_name}")
                col1, col2 = st.columns(2)
                col1.metric("현재 나의 가격", f"{f_price:,}원")
                col2.metric("역대 최저가 기록", f"{low_price:,}원")
                
                diff = f_price - low_price
                if diff <= 0:
                    st.success(f"✅ **와우! 역대급입니다.** 기록된 최저가보다 저렴하거나 같습니다. 무조건 사세요!")
                elif diff < (low_price * 0.05):
                    st.warning(f"🤔 **나쁘지 않네요.** 최저가와 약 {diff:,}원 차이입니다. 급하시면 사세요.")
                else:
                    st.error(f"❌ **참으세요!** 역대 시세보다 {diff:,}원 더 비쌉니다. 존버를 추천합니다.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 커뮤니티 기록을 찾지 못했습니다. 상품명을 더 정확하거나 짧게 입력해보세요 (예: 아이폰15).")

if __name__ == "__main__":
    main()
