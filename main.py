import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. 시세 분석 및 강건한 이상치 제거 엔진
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
    def clean_prices_robust(price_list):
        if not price_list: return []
        prices = sorted(list(set(price_list))) 
        if 1 < len(prices) <= 3:
            if prices[0] < prices[1] * 0.5:
                prices.pop(0)
        elif len(prices) >= 4:
            arr = np.array(prices)
            mean = np.mean(arr)
            std = np.std(arr)
            lower_bound = mean - (3 * std)
            upper_bound = mean + (3 * std)
            prices = [p for p in prices if p >= lower_bound and p <= upper_bound]
        return sorted(prices)

    @staticmethod
    def categorize_deals(titles, search_query, user_excludes):
        base_excludes = ["중고", "사용감", "리퍼", "S급", "민팃", "삽니다", "매입"]
        custom_excludes = [x.strip() for x in user_excludes.split(',') if x.strip()]
        total_excludes = base_excludes + custom_excludes
        exclude_pattern = re.compile('|'.join(map(re.escape, total_excludes)))
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        categorized = {}
        search_query_low = search_query.lower()

        for text in titles:
            if exclude_pattern.search(text): continue
            found = price_pattern.findall(text)
            if not found: continue
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            if num < 5000: continue 
            
            t_low = text.lower()
            model_tag = "일반/기본"
            if any(k in search_query_low for k in ["s24", "아이폰", "갤럭시", "버지", "p10"]):
                if any(k in t_low for k in ["울트라", "ultra", "p10", "버지"]): model_tag = "상급/Ultra"
                elif any(k in t_low for k in ["플러스", "plus", "d8", "링크"]): model_tag = "중급/Plus"
            
            specs = ""
            if "256" in t_low: specs = " 256G"
            elif "512" in t_low: specs = " 512G"
            elif "10인용" in t_low: specs = " 10인용"
            elif "6인용" in t_low: specs = " 6인용"

            key = f"{model_tag}{specs}".strip()
            if key not in categorized: categorized[key] = []
            categorized[key].append(num)
        return {k: AdvancedSearchEngine.clean_prices_robust(v) for k, v in categorized.items() if v}

# ==========================================
# 2. UI 및 로직 통합
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v2.5", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .main .block-container { max-width: 550px !important; padding-top: 5rem !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; }
        .price-highlight { color: #00FF88 !important; font-size: 2rem !important; font-weight: 900 !important; float: right; }
        .judgment-box { padding: 10px; border-radius: 8px; font-weight: 900; text-align: center; margin-top: 10px; }
        .link-btn-box { background-color: #333333 !important; color: #FFFFFF !important; padding: 12px; border-radius: 8px; text-align: center; font-size: 0.9rem; border: 1px solid #FFFFFF !important; font-weight: bold; margin-bottom: 10px; }
        .review-btn-box { background-color: #004d40 !important; color: #00FF88 !important; padding: 12px; border-radius: 8px; text-align: center; font-size: 0.9rem; border: 1px solid #00FF88 !important; font-weight: bold; }
        .stButton>button { width: 100%; border: 2px solid #00FF88 !important; background-color: #000000 !important; color: #00FF88 !important; font-weight: bold !important; }
        label p { color: #FFFFFF !important; font-weight: bold !important; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    
    # Session State 초기화 (중복 오류 방지)
    if 'p_name' not in st.session_state: st.session_state.p_name = ""
    if 'p_price' not in st.session_state: st.session_state.p_price = ""
    if 'p_exclude' not in st.session_state: st.session_state.p_exclude = "직구, 해외, 렌탈, 당근, 중고"
    if 'history' not in st.session_state: st.session_state.history = []
    if 'results' not in st.session_state: st.session_state.results = None

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span style="font-size:0.8rem; color:#444;">v2.5</span></div>', unsafe_allow_html=True)

    # 1. 입력 영역 (Reset 오류 방지를 위해 value 제거하고 key만 사용)
    f_name = st.text_input("📦 제품명 입력", key="p_name")
    f_price = st.text_input("💰 나의 확인가 (숫자만)", key="p_price")
    f_exclude = st.text_input("🚫 제외 단어", key="p_exclude")

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 시세 판독 실행"):
            if f_name:
                with st.spinner('🏘️ 분석 중...'):
                    raw = AdvancedSearchEngine.search_all(f_name)
                    st.session_state.results = AdvancedSearchEngine.categorize_deals(raw, f_name, f_exclude)
    with col2:
        if st.button("🔄 리셋"):
            st.session_state.p_name = ""
            st.session_state.p_price = ""
            st.session_state.p_exclude = "직구, 해외, 렌탈, 당근, 중고"
            st.session_state.results = None
            st.rerun()

    # 2. 결과 리포트 출력
    if st.session_state.results:
        cat_data = st.session_state.results
        st.markdown("### 📊 옵션별 최저가 리포트")
        for key, prices in sorted(cat_data.items(), key=lambda x: x[1][0]):
            count = len(prices)
            min_p = prices[0]
            rel_col = "#00FF88" if count >= 4 else "#FF5555"
            rel_txt = "🟢 신뢰도 높음" if count >= 4 else "🔴 신뢰도 낮음"

            st.markdown(f'''
            <div class="detail-card">
                <span style="color:{rel_col}; font-weight:bold; font-size:0.85rem;">{rel_txt} (표본 {count}건)</span><br>
                <span style="color:white; font-weight:bold; font-size:1.2rem;">{key}</span>
                <span class="price-highlight">{min_p:,}원</span>
            </div>
            ''', unsafe_allow_html=True)
            
            if f_price.isdigit():
                user_p = int(f_price)
                diff = user_p - min_p
                if diff <= 0: st.markdown('<div class="judgment-box" style="background:#004d40; color:#00FF88;">✅ 판결: 역대급 최저가! 즉시 지르세요!</div>', unsafe_allow_html=True)
                elif diff < min_p * 0.1: st.markdown(f'<div class="judgment-box" style="background:#424200; color:#FFD700;">⚠️ 판결: 준수한 가격 (차액: {diff:,}원)</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="judgment-box" style="background:#4d0000; color:#FF5555;">❌ 판결: 아직 비쌈! (차액: {diff:,}원)</div>', unsafe_allow_html=True)

        # 3. [복구] 시세 근거 및 리뷰 링크 버튼
        st.write("\n")
        st.markdown("### 🔗 실시간 근거 데이터 및 리뷰")
        e_q = urllib.parse.quote(f_name)
        c_link1, c_link2 = st.columns(2)
        with c_link1:
            st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={e_q}&category=1" target="_blank" style="text-decoration:none;"><div class="link-btn-box">뽐뿌 실시간 시세</div></a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.clien.net/service/search?q={e_q}" target="_blank" style="text-decoration:none;"><div class="link-btn-box">클리앙 실시간 시세</div></a>', unsafe_allow_html=True)
        with c_link2:
            st.markdown(f'<a href="https://www.ppomppu.co.kr/zboard/zboard.php?id=free_picture&category=2&keyword={e_q}" target="_blank" style="text-decoration:none;"><div class="review-btn-box" style="margin-bottom:10px;">뽐뿌 추천 사용기</div></a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.clien.net/service/search/board/use?sk=title&sv={e_q}" target="_blank" style="text-decoration:none;"><div class="review-btn-box">클리앙 베스트 리뷰</div></a>', unsafe_allow_html=True)

if __name__ == "__main__": main()

# Version: v2.5 - Fixed SessionState Error, Restored Links, Price Input & Reset