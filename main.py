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

# ==========================================
# 2. UI 및 스타일링 (v1.1 반영)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v1.1", layout="centered")
    st.markdown("""
        <style>
        .block-container { max-width: 550px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 10px; border: 4px solid #00FF88; }
        .version-tag { font-size: 0.8rem; vertical-align: middle; color: #666; margin-left: 10px; }
        .detail-card { border: 2px solid #00FF88; padding: 15px; border-radius: 12px; margin-top: 20px; background-color: #0A0A0A; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; height: 3rem; }
        /* 폼 내부 버튼 정렬 */
        div[data-testid="column"] { display: flex; align-items: flex-end; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    
    # 상단 버전 표시 반영
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span class="version-tag">v1.1</span></div>', unsafe_allow_html=True)

    # [수정] 리셋 기능을 위해 세션 상태 관리
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False

    # [해결] 폼 구조 - Clear_on_submit으로 리셋 구현
    with st.form(key='search_form', clear_on_submit=True):
        f_name = st.text_input("📦 제품명 (예: 갤럭시 S24, 턴 버지 P10)", key="p_name")
        p_val = st.text_input("💰 나의 확인가 (숫자만)", key="p_price")
        
        cols = st.columns(2)
        submit_button = cols[0].form_submit_button(label='🔍 시세 판독 실행')
        reset_button = cols[1].form_submit_button(label='🔄 리셋')

    # 리셋 버튼 클릭 시 페이지 초기화
    if reset_button:
        st.rerun()

    # 판독 실행
    if submit_button:
        if not f_name:
            st.error("❗ 제품명을 입력해주세요.")
        else:
            with st.spinner('🏘️ 3대 커뮤니티 데이터를 분석 중...'):
                raw_titles = AdvancedSearchEngine.search_all(f_name)
                
                # 가격 추출 로직
                prices = []
                exclude_pattern = re.compile(r'중고|사용감|리퍼|S급|민팃')
                for t in raw_titles:
                    if exclude_pattern.search(t): continue
                    found = re.findall(r'([0-9,]{1,10})\s?(원|만)', t)
                    if found:
                        num = int(found[0][0].replace(',', ''))
                        if found[0][1] == '만': num *= 10000
                        if num > 10000: prices.append(num)
                
                prices = sorted(list(set(prices)))

            if prices:
                # [신규] 신뢰도 계산 및 표시
                count = len(prices)
                if count >= 8: rel_text, rel_color = "🟢 신뢰도 높음", "#00FF88"
                elif count >= 3: rel_text, rel_color = "🟡 신뢰도 중간", "#FFD700"
                else: rel_text, rel_color = "🔴 신뢰도 낮음 (데이터 부족)", "#FF4B4B"

                st.markdown(f"### <span style='color:{rel_color}'>{rel_text}</span>", unsafe_allow_html=True)

                # 결과 카드
                st.markdown(f'''
                <div class="detail-card">
                    <div style="color:#00FF88; font-weight:bold; margin-bottom:10px;">📊 분석 결과</div>
                    <div style="font-size:1.6rem; font-weight:bold;">최저가: {prices[0]:,}원</div>
                    <div style="color:#888; font-size:0.9rem; margin-top:5px;">탐지된 고유 시세: {count}개</div>
                </div>
                ''', unsafe_allow_html=True)

                # [신규] 커뮤니티 연결 링크 버튼
                st.write("")
                st.write("🔗 **판독 근거 확인 (커뮤니티 이동)**")
                links = AdvancedSearchEngine.get_search_links(f_name)
                l_cols = st.columns(3)
                for i, (site, url) in enumerate(links.items()):
                    l_cols[i].markdown(f'''
                        <a href="{url}" target="_blank" style="text-decoration:none;">
                            <div style="background:#111; color:#00FF88; padding:10px; border-radius:8px; text-align:center; font-size:0.8rem; border:1px solid #00FF88;">
                                {site}
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
                
                st.markdown('<div style="color:#FF4B4B; font-size:0.8rem; margin-top:30px; text-align:center;">⚠️ 최근 1년 내 최저가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 검색 결과가 없습니다. 키워드를 더 단순하게 시도해보세요.")

if __name__ == "__main__":
    main()

# Version: v1.1 - Reset, Reliability, and Links Integrated
