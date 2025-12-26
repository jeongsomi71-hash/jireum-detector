import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# ==========================================
# 1. 시세 분석 및 신뢰도 측정 엔진
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        }

    @staticmethod
    def get_search_links(query):
        """커뮤니티별 검색 결과 링크 생성"""
        encoded_query = urllib.parse.quote(query)
        return {
            "뽐뿌": f"https://m.ppomppu.co.kr/new/bbs_list.php?id=ppomppu&search_type=sub_memo&keyword={encoded_query}",
            "루리웹": f"https://m.bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={encoded_query}",
            "클리앙": f"https://www.clien.net/service/search/board/jirum?sk=title&sv={encoded_query}"
        }

    @staticmethod
    def search_all(product_name):
        links = AdvancedSearchEngine.get_search_links(product_name)
        all_titles = []
        for name, url in links.items():
            try:
                res = requests.get(url, headers=AdvancedSearchEngine.get_mobile_headers(), timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                if "ppomppu" in url: titles = [t.get_text(strip=True) for t in soup.select('.title')]
                elif "ruliweb" in url: titles = [t.get_text(strip=True) for t in soup.select('.subject_inner_text, .subject')]
                else: titles = [t.get_text(strip=True) for t in soup.select('.list_subject .subject_fixed')]
                all_titles.extend(titles)
            except: continue
        return all_titles

    @staticmethod
    def calculate_reliability(prices):
        """데이터 개수에 따른 신뢰도 판별"""
        count = len(prices)
        if count >= 10: return "🟢 신뢰도 높음", "#00FF88"
        elif count >= 3: return "🟡 신뢰도 중간", "#FFD700"
        else: return "🔴 신뢰도 낮음 (데이터 부족)", "#FF4B4B"

# ==========================================
# 2. UI 및 스타일링
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        .block-container { max-width: 550px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .detail-card { border: 2px solid #00FF88; padding: 15px; border-radius: 12px; margin-bottom: 12px; background-color: #0A0A0A; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; }
        .link-button { display: inline-block; padding: 5px 10px; border: 1px solid #444; border-radius: 5px; color: #AAA; text-decoration: none; font-size: 0.8rem; margin-right: 5px; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)

    # [수정] 폼을 사용하여 리셋 시 입력창을 확실히 비움
    with st.form("search_form", clear_on_submit=True):
        f_name = st.text_input("📦 분석할 제품명 (자전거, 전자제품 등)", placeholder="예: 턴 버지 P10")
        p_val = st.text_input("💰 나의 확인가 (숫자만)")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("⚖️ 시세 판독 실행")
        with col2:
            reset = st.form_submit_button("🔄 리셋 (내용 비우기)")

    if submit and f_name:
        with st.spinner('🏘️ 커뮤니티 데이터를 정밀 분석 중...'):
            raw_titles = AdvancedSearchEngine.search_all(f_name)
            
            # 필터링 및 가격 추출 (고도화1 로직 유지)
            prices = []
            exclude_pattern = re.compile(r'중고|사용감|리퍼|S급')
            for t in raw_titles:
                if exclude_pattern.search(t): continue
                found = re.findall(r'([0-9,]{1,10})\s?(원|만)', t)
                if found:
                    num = int(found[0][0].replace(',', ''))
                    if found[0][1] == '만': num *= 10000
                    if num > 10000: prices.append(num)
            
            prices = sorted(list(set(prices)))

        if prices:
            reliability, rel_color = AdvancedSearchEngine.calculate_reliability(prices)
            
            st.markdown(f"### <span style='color:{rel_color}'>{reliability}</span>", unsafe_allow_html=True)
            
            st.markdown(f'''
            <div class="detail-card">
                <div style="color:#00FF88; font-weight:bold; margin-bottom:10px;">📊 분석 결과</div>
                <div style="font-size:1.5rem; font-weight:bold;">최저가: {prices[0]:,}원</div>
                <div style="color:#888; font-size:0.9rem; margin-top:5px;">수집된 가격대: {len(prices)}개 탐지됨</div>
            </div>
            ''', unsafe_allow_html=True)

            # [수정] 근거 데이터 링크 제공
            st.write("🔗 **판독 근거 (커뮤니티 검색 결과)**")
            links = AdvancedSearchEngine.get_search_links(f_name)
            link_cols = st.columns(3)
            for i, (site, url) in enumerate(links.items()):
                link_cols[i].markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background:#222; color:#00FF88; padding:10px; border-radius:5px; text-align:center; font-size:0.8rem; border:1px solid #444;">{site} 바로가기</div></a>', unsafe_allow_html=True)

            st.markdown('<div style="color:#FF4B4B; font-size:0.8rem; margin-top:20px;">⚠️ 최근 1년 내 최저가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ 데이터를 찾지 못했습니다. 상품명을 더 단순하게 입력해보세요.")

if __name__ == "__main__":
    main()
