import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime

# ==========================================
# 1. 정밀 분류 및 시세 분석 엔진
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        links = {
            "뽐뿌(통합)": f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=1",
            "클리앙(알뜰)": f"https://www.clien.net/service/search/board/jirum?sk=title&sv={encoded_query}",
            "클리앙(전체)": f"https://www.clien.net/service/search?q={encoded_query}"
        }
        all_titles = []
        for url in links.values():
            try:
                res = requests.get(url, headers=AdvancedSearchEngine.get_mobile_headers(), timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                if "ppomppu" in url:
                    all_titles.extend([t.get_text(strip=True) for t in soup.select('.title, .content')])
                else:
                    all_titles.extend([t.get_text(strip=True) for t in soup.select('.list_subject .subject_fixed, .subject_fixed')])
            except: continue
        return all_titles

    @staticmethod
    def categorize_deals(titles):
        exclude_pattern = re.compile(r'중고|사용감|리퍼|S급|민팃|삽니다|매입')
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        categorized = {}

        for text in titles:
            if exclude_pattern.search(text): continue
            found = price_pattern.findall(text)
            if not found: continue
            
            # 가격 계산
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            if num < 10000: continue

            # 옵션 추출 로직 (v1.5 복구 및 강화)
            t_low = text.lower()
            model = "일반/기본"
            if any(k in t_low for k in ["울트라", "ultra", "p10", "버지"]): model = "상급/Ultra"
            elif any(k in t_low for k in ["플러스", "plus", "d8", "링크"]): model = "중급/Plus"

            storage = ""
            if "256" in t_low: storage = " 256G"
            elif "512" in t_low: storage = " 512G"
            elif "1tb" in t_low or "1티라" in t_low: storage = " 1TB"

            opt = ""
            if "자급제" in t_low: opt = " (자급제)"
            elif any(k in t_low for k in ["현완", "번이", "기변", "성지"]): opt = " (성지)"

            key = f"{model}{storage}{opt}".strip()
            if key not in categorized: categorized[key] = []
            categorized[key].append(num)
        
        return {k: sorted(list(set(v))) for k, v in categorized.items()}

# ==========================================
# 2. UI 및 스타일링
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v1.5", layout="centered")
    st.markdown("""
        <style>
        .block-container { max-width: 550px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 10px; border: 4px solid #00FF88; }
        .version-tag { font-size: 0.8rem; vertical-align: middle; color: #666; margin-left: 10px; }
        .detail-card { border: 2px solid #00FF88; padding: 15px; border-radius: 12px; margin-top: 10px; background-color: #0A0A0A; }
        .price-highlight { color: #00FF88 !important; font-size: 1.8rem !important; font-weight: 900 !important; float: right; }
        .link-btn-box { background:#111; color:#FFFFFF !important; padding:10px; border-radius:8px; text-align:center; font-size:0.8rem; border:1px solid #00FF88; }
        .history-item { border-left: 3px solid #00FF88; padding: 8px 12px; margin-bottom: 5px; background: #111; font-size: 0.85rem; border-radius: 0 5px 5px 0; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; height: 3.5rem; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 'history' not in st.session_state: st.session_state.history = []

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span class="version-tag">v1.5</span></div>', unsafe_allow_html=True)

    with st.form(key='search_form', clear_on_submit=False):
        f_name = st.text_input("📦 제품명 (예: 갤럭시 S24, 턴 버지 P10)")
        p_val = st.text_input("💰 나의 확인가 (숫자만)")
        cols = st.columns(2)
        submit_button = cols[0].form_submit_button(label='🔍 시세 판독 실행')
        reset_button = cols[1].form_submit_button(label='🔄 리셋')

    if reset_button: st.rerun()

    if submit_button and f_name:
        with st.spinner('🏘️ 포럼 포함 상세 옵션별 시세 분석 중...'):
            raw_titles = AdvancedSearchEngine.search_all(f_name)
            cat_data = AdvancedSearchEngine.categorize_deals(raw_titles)

            if cat_data:
                st.write("### 📊 옵션별 시세 리포트")
                # 최저가 순으로 정렬
                sorted_keys = sorted(cat_data.keys(), key=lambda x: cat_data[x][0])
                
                for key in sorted_keys:
                    prices = cat_data[key]
                    count = len(prices)
                    rel_color = "#00FF88" if count >= 5 else ("#FFD700" if count >= 2 else "#FF4B4B")
                    
                    st.markdown(f'''
                    <div class="detail-card">
                        <span style="color:{rel_color}; font-size:0.8rem;">● 데이터 {count}건</span><br>
                        <span style="font-weight:bold; font-size:1.1rem;">{key}</span>
                        <span class="price-highlight">{prices[0]:,}원</span>
                    </div>
                    ''', unsafe_allow_html=True)

                # 이력 저장 (전체 최저가 기준)
                best_price = min([p[0] for p in cat_data.values()])
                now = datetime.now().strftime("%H:%M:%S")
                st.session_state.history.insert(0, f"[{now}] {f_name} → {best_price:,}원")
                st.session_state.history = st.session_state.history[:10]

                # 링크 및 경고 문구
                st.write("\n🔗 **실시간 근거 데이터 확인**")
                links = {"뽐뿌(통합)": f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={urllib.parse.quote(f_name)}&category=1",
                         "클리앙(전체)": f"https://www.clien.net/service/search?q={urllib.parse.quote(f_name)}"}
                l_cols = st.columns(len(links))
                for i, (site, url) in enumerate(links.items()):
                    l_cols[i].markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div class="link-btn-box">{site}</div></a>', unsafe_allow_html=True)
                
                st.markdown('<div style="color:#FF4B4B; font-size:0.8rem; margin-top:30px; text-align:center;">⚠️ 최근 1년 내 낮은 가격들의 평균가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
            else: st.warning("⚠️ 데이터를 찾지 못했습니다.")

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 조회 이력 (Top 10)")
        for item in st.session_state.history:
            st.markdown(f'<div class="history-item">{item}</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()

# Version: v1.5 - Restored Option Categorization & History Tracking
