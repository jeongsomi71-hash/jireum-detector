import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime

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
# 2. UI 및 스타일링 (v1.2 가독성 강화)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v1.2", layout="centered")
    st.markdown("""
        <style>
        .block-container { max-width: 550px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 10px; border: 4px solid #00FF88; }
        .version-tag { font-size: 0.8rem; vertical-align: middle; color: #666; margin-left: 10px; }
        .detail-card { border: 2px solid #00FF88; padding: 20px; border-radius: 12px; margin-top: 20px; background-color: #0A0A0A; text-align: center; }
        
        /* [개선] 최저가 글자 색상 및 크기 강조 */
        .price-highlight { color: #00FF88 !important; font-size: 2.2rem !important; font-weight: 900 !important; text-shadow: 2px 2px 4px rgba(0,255,136,0.3); margin: 10px 0; display: block; }
        
        .history-item { border-left: 3px solid #00FF88; padding: 8px 12px; margin-bottom: 5px; background: #111; font-size: 0.85rem; border-radius: 0 5px 5px 0; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; height: 3.5rem; font-size: 1.1rem; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    
    # 세션 상태 초기화 (이력 저장용)
    if 'history' not in st.session_state:
        st.session_state.history = []

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span class="version-tag">v1.2</span></div>', unsafe_allow_html=True)

    with st.form(key='search_form', clear_on_submit=False):
        f_name = st.text_input("📦 제품명 (예: 갤럭시 S24, 턴 버지 P10)")
        p_val = st.text_input("💰 나의 확인가 (숫자만)")
        
        cols = st.columns(2)
        submit_button = cols[0].form_submit_button(label='🔍 시세 판독 실행')
        reset_button = cols[1].form_submit_button(label='🔄 리셋')

    if reset_button:
        # 이력은 유지하되 입력창과 현재 결과만 초기화
        st.rerun()

    if submit_button:
        if not f_name:
            st.error("❗ 제품명을 입력해주세요.")
        else:
            with st.spinner('🏘️ 데이터를 분석 중...'):
                raw_titles = AdvancedSearchEngine.search_all(f_name)
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
                low_price = prices[0]
                count = len(prices)
                
                # 신뢰도 측정
                if count >= 8: rel_text, rel_color = "🟢 신뢰도 높음", "#00FF88"
                elif count >= 3: rel_text, rel_color = "🟡 신뢰도 중간", "#FFD700"
                else: rel_text, rel_color = "🔴 신뢰도 낮음", "#FF4B4B"

                # [개선] 결과 카드 내 최저가 가독성 강화
                st.markdown(f"### <span style='color:{rel_color}'>{rel_text}</span>", unsafe_allow_html=True)
                st.markdown(f'''
                <div class="detail-card">
                    <div style="color:#FFFFFF; font-size:1.1rem; opacity:0.8;">분석된 최저가</div>
                    <span class="price-highlight">{low_price:,}원</span>
                    <div style="color:#888; font-size:0.9rem;">탐지된 고유 시세: {count}개</div>
                </div>
                ''', unsafe_allow_html=True)

                # 조회 이력 추가 (최근 10개 유지)
                now = datetime.now().strftime("%H:%M:%S")
                history_entry = f"[{now}] {f_name} → {low_price:,}원 ({rel_text})"
                st.session_state.history.insert(0, history_entry)
                st.session_state.history = st.session_state.history[:10]

                # 커뮤니티 링크
                st.write("")
                st.write("🔗 **실시간 검색 결과 확인**")
                links = AdvancedSearchEngine.get_search_links(f_name)
                l_cols = st.columns(3)
                for i, (site, url) in enumerate(links.items()):
                    l_cols[i].markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background:#111; color:#00FF88; padding:10px; border-radius:8px; text-align:center; font-size:0.8rem; border:1px solid #00FF88;">{site}</div></a>', unsafe_allow_html=True)
                
                st.markdown('<div style="color:#FF4B4B; font-size:0.8rem; margin-top:30px; text-align:center;">⚠️ 최근 1년 내 최저가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 검색 결과가 없습니다.")

    # [신규] 과거 조회 이력 표시 (하단 섹션)
    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 조회 이력 (Top 10)")
        for item in st.session_state.history:
            st.markdown(f'<div class="history-item">{item}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# Version: v1.2 - History Log (10) & Enhanced Price Visibility
