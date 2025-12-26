import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import time

# ==========================================
# 1. 시세 분석 및 포럼 확장 엔진
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
            "뽐뿌(통합)": f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=1",
            "클리앙(알뜰)": f"https://www.clien.net/service/search/board/jirum?sk=title&sv={encoded_query}",
            "클리앙(전체)": f"https://www.clien.net/service/search?q={encoded_query}"
        }

    @staticmethod
    def search_all(product_name):
        links = AdvancedSearchEngine.get_search_links(product_name)
        all_titles = []
        
        for name, url in links.items():
            try:
                res = requests.get(url, headers=AdvancedSearchEngine.get_mobile_headers(), timeout=10)
                # 서버 부하 방지 및 차단 회피를 위한 미세 지연
                time.sleep(0.3)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                if "ppomppu" in url:
                    # 뽐뿌 통합검색 결과 추출
                    titles = [t.get_text(strip=True) for t in soup.select('.title, .content')]
                elif "clien" in url:
                    # 클리앙 게시판/통합검색 결과 추출
                    titles = [t.get_text(strip=True) for t in soup.select('.list_subject .subject_fixed, .subject_fixed')]
                
                all_titles.extend(titles)
            except: continue
            
        return all_titles

# ==========================================
# 2. UI 및 스타일링 (v1.4)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v1.4", layout="centered")
    st.markdown("""
        <style>
        .block-container { max-width: 550px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 10px; border: 4px solid #00FF88; }
        .version-tag { font-size: 0.8rem; vertical-align: middle; color: #666; margin-left: 10px; }
        .detail-card { border: 2px solid #00FF88; padding: 20px; border-radius: 12px; margin-top: 20px; background-color: #0A0A0A; text-align: center; }
        .price-highlight { color: #00FF88 !important; font-size: 2.2rem !important; font-weight: 900 !important; text-shadow: 2px 2px 4px rgba(0,255,136,0.3); margin: 10px 0; display: block; }
        .link-btn-box { background:#111; color:#FFFFFF !important; padding:10px; border-radius:8px; text-align:center; font-size:0.8rem; border:1px solid #00FF88; }
        .history-item { border-left: 3px solid #00FF88; padding: 8px 12px; margin-bottom: 5px; background: #111; font-size: 0.85rem; border-radius: 0 5px 5px 0; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; height: 3.5rem; font-size: 1.1rem; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 'history' not in st.session_state: st.session_state.history = []

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span class="version-tag">v1.4</span></div>', unsafe_allow_html=True)

    with st.form(key='search_form'):
        f_name = st.text_input("📦 제품명 (예: 갤럭시 S24, 턴 버지 P10)")
        p_val = st.text_input("💰 나의 확인가 (숫자만)")
        cols = st.columns(2)
        submit_button = cols[0].form_submit_button(label='🔍 시세 판독 실행')
        reset_button = cols[1].form_submit_button(label='🔄 리셋')

    if reset_button: st.rerun()

    if submit_button:
        if not f_name:
            st.error("❗ 제품명을 입력해주세요.")
        else:
            with st.spinner('🏘️ 포럼 및 게시판 데이터를 광범위하게 수집 중...'):
                raw_titles = AdvancedSearchEngine.search_all(f_name)
                prices = []
                exclude_pattern = re.compile(r'중고|사용감|리퍼|S급|민팃|삽니다|매입')
                
                for t in raw_titles:
                    if exclude_pattern.search(t): continue
                    # 가격 추출 패턴 (숫자 뒤 '만' 혹은 '원')
                    found = re.findall(r'([0-9,]{1,10})\s?(원|만)', t)
                    if found:
                        num = int(found[0][0].replace(',', ''))
                        if found[0][1] == '만': num *= 10000
                        # 자전거 소모품 등 저가 제외를 위해 10,000원 이상만 수집
                        if num >= 10000: prices.append(num)
                
                prices = sorted(list(set(prices)))

            if prices:
                low_price = prices[0]
                count = len(prices)
                
                # 신뢰도 측정 (데이터 수 기준)
                if count >= 10: rel_text, rel_color = "🟢 신뢰도 높음", "#00FF88"
                elif count >= 4: rel_text, rel_color = "🟡 신뢰도 중간", "#FFD700"
                else: rel_text, rel_color = "🔴 신뢰도 낮음", "#FF4B4B"

                st.markdown(f"### <span style='color:{rel_color}'>{rel_text}</span>", unsafe_allow_html=True)
                st.markdown(f'''
                <div class="detail-card">
                    <div style="color:#FFFFFF; font-size:1.1rem; opacity:0.8;">분석된 최저가</div>
                    <span class="price-highlight">{low_price:,}원</span>
                    <div style="color:#888; font-size:0.9rem;">탐지된 데이터 소스: {count}개</div>
                </div>
                ''', unsafe_allow_html=True)

                # 이력 저장
                now = datetime.now().strftime("%H:%M:%S")
                history_entry = f"[{now}] {f_name} → {low_price:,}원 ({rel_text})"
                st.session_state.history.insert(0, history_entry)
                st.session_state.history = st.session_state.history[:10]

                # 커뮤니티 링크 (루리웹 제거, 검색 범위 확장 링크)
                st.write("")
                st.write("🔗 **실시간 근거 데이터 확인**")
                links = AdvancedSearchEngine.get_search_links(f_name)
                l_cols = st.columns(len(links))
                for i, (site, url) in enumerate(links.items()):
                    l_cols[i].markdown(f'''
                        <a href="{url}" target="_blank" style="text-decoration:none;">
                            <div class="link-btn-box">{site}</div>
                        </a>
                    ''', unsafe_allow_html=True)
                
                st.markdown('<div style="color:#FF4B4B; font-size:0.8rem; margin-top:30px; text-align:center;">⚠️ 최근 1년 내 낮은 가격들의 평균가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 포럼을 포함해 검색했으나 결과가 없습니다. 검색어를 더 짧게 시도해보세요.")

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 조회 이력 (Top 10)")
        for item in st.session_state.history:
            st.markdown(f'<div class="history-item">{item}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# Version: v1.4 - Forum Data Expansion & Removed Ruliweb (404 Error)
