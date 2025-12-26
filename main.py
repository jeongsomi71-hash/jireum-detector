import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# ==========================================
# 1. 3대 커뮤니티 통합 직접 탐색 엔진 (성지 타겟팅)
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
    def search_community(product_name, site):
        query = urllib.parse.quote(product_name)
        if site == "ppomppu":
            url = f"https://m.ppomppu.co.kr/new/bbs_list.php?id=ppomppu&search_type=sub_memo&keyword={query}"
        elif site == "ruliweb":
            url = f"https://m.bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={query}"
        elif site == "clien":
            url = f"https://www.clien.net/service/search/board/jirum?sk=title&sv={query}"
        
        try:
            res = requests.get(url, headers=TripleCommunityEngine.get_mobile_headers(), timeout=7)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            if site == "ppomppu": titles = [t.get_text(strip=True) for t in soup.select('.title')]
            elif site == "ruliweb": titles = [t.get_text(strip=True) for t in soup.select('.subject_inner_text, .subject')]
            elif site == "clien": titles = [t.get_text(strip=True) for t in soup.select('.list_subject .subject_fixed')]
            
            return titles
        except: return []

    @staticmethod
    def extract_lowest_deal_prices(texts):
        """중고는 배제하고 성지/신품 핫딜 가격만 추출"""
        prices = []
        # 중고 관련 키워드만 엄격히 제외
        exclude_pattern = re.compile(r'중고|민팃|리퍼|S급|A급|B급|사용감|풀박중고')
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        for text in texts:
            # 중고 키워드 발견 시 즉시 제외
            if exclude_pattern.search(text):
                continue
                
            found = price_pattern.findall(text)
            for f_val, unit in found:
                num = int(f_val.replace(',', ''))
                if unit == '만': num *= 10000
                
                # 성지 가격은 매우 낮을 수 있으므로 하한선을 거의 없앰 (단, 0원은 제외)
                if 0 < num < 15000000: 
                    prices.append(num)
        return sorted(prices)

# ==========================================
# 2. UI 및 스타일 적용
# ==========================================
def apply_custom_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
        .block-container { max-width: 500px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .result-box { border: 2px solid #00FF88; padding: 25px; border-radius: 15px; margin-top: 20px; background-color: #111111; }
        .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)

    # [원칙] 우측 상단 리셋 버튼
    col_title, col_reset = st.columns([4, 1])
    with col_reset:
        if st.button("🔄 리셋"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

    st.subheader("✍️ 실시간 핫딜 시세 검색")
    f_name = st.text_input("📦 상품명", placeholder="예: 아이폰 15 프로, 성지, 현완")
    p_val = st.text_input("💰 확인하신 가격 (숫자만)", placeholder="예: 950000")

    if st.button("⚖️ 성지·신품 통합 판결 실행"):
        if not f_name or not p_val:
            st.error("❗ 상품명과 가격을 모두 입력해주세요.")
        else:
            f_price = int(re.sub(r'[^0-9]', '', p_val))
            
            with st.spinner('🏘️ 3대 커뮤니티에서 성지 및 신품 기록을 수집 중...'):
                all_titles = []
                for site in ["ppomppu", "ruliweb", "clien"]:
                    all_titles.extend(TripleCommunityEngine.search_community(f_name, site))
                
                clean_prices = TripleCommunityEngine.extract_lowest_deal_prices(all_titles)

            if clean_prices:
                low_price = clean_prices[0] # 성지 포함 역대 최저가
                
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 통합 판결")
                c1, c2 = st.columns(2)
                c1.metric("나의 확인가", f"{f_price:,}원")
                c2.metric("역대 성지/신품 최저가", f"{low_price:,}원")
                
                diff = f_price - low_price
                if diff <= 0:
                    st.success("🔥 **역대급 딜!** 성지 가격보다도 저렴하거나 동급입니다.")
                elif diff < (low_price * 0.1):
                    st.warning(f"🤔 **적정가입니다.** 최저가와 약 {diff:,}원 차이로 구매할만 합니다.")
                else:
                    st.error(f"💀 **주의!** 역대 기록보다 {diff:,}원 더 비쌉니다.")
                
                st.info("💡 중고 키워드는 제외되었으며, 성지 현금완납 가격은 포함되었습니다.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 정보를 찾지 못했습니다. 키워드를 '아이폰, 성지' 처럼 쉼표로 나눠보세요.")

if __name__ == "__main__":
    main()
