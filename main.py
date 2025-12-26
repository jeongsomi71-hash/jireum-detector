import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. 시세 분석 및 역전 방지 이상치 제거 엔진
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
            if prices[0] < prices[1] * 0.5: prices.pop(0)
        elif len(prices) >= 4:
            arr = np.array(prices)
            mean, std = np.mean(arr), np.std(arr)
            prices = [p for p in prices if (mean - 3*std) <= p <= (mean + 3*std)]
        return sorted(prices)

    @staticmethod
    def categorize_deals(titles, search_query, user_excludes):
        base_excludes = ["중고", "사용감", "리퍼", "S급", "민팃", "삽니다", "매입"]
        total_excludes = base_excludes + [x.strip() for x in user_excludes.split(',') if x.strip()]
        exclude_pattern = re.compile('|'.join(map(re.escape, total_excludes)))
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        categorized = {}
        for text in titles:
            if exclude_pattern.search(text): continue
            found = price_pattern.findall(text)
            if not found: continue
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            if num < 10000: continue 
            
            t_low = text.lower()
            tag = "일반/기본"
            if any(k in t_low for k in ["10인용", "10인"]): tag = "10인용"
            elif any(k in t_low for k in ["6인용", "6인"]): tag = "6인용"
            elif any(k in t_low for k in ["3인용", "3인"]): tag = "3인용"
            
            if tag not in categorized: categorized[tag] = []
            categorized[tag].append(num)
        
        cleaned_cat = {k: AdvancedSearchEngine.clean_prices_robust(v) for k, v in categorized.items()}
        
        # [역전 방지] 10인용이 6인용보다 비정상적으로 쌀 경우 처리
        if "10인용" in cleaned_cat and "6인용" in cleaned_cat:
            if cleaned_cat["10인용"][0] < cleaned_cat["6인용"][0] * 0.8:
                if len(cleaned_cat["10인용"]) > 1: cleaned_cat["10인용"].pop(0)
                    
        return {k: v for k, v in cleaned_cat.items() if v}

# ==========================================
# 2. UI 및 메인 제어 로직
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v2.7", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .main .block-container { max-width: 550px !important; padding-top: 5rem !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; }
        .price-highlight { color: #00FF88 !important; font-size: 2rem !important; font-weight: 900 !important; float: right; }
        .judgment-box { padding: 10px; border-radius: 8px; font-weight: 900; text-align: center; margin-top: 10px; }
        .link-btn-box { background-color: #333333 !important; color: #FFFFFF !important; padding: 10px; border-radius: 8px; text-align: center; font-size: 0.85rem; border: 1px solid #FFFFFF !important; font-weight: bold; margin-bottom: 5px; text-decoration: none; display: block; }
        .review-btn-box { background-color: #004d40 !important; color: #00FF88 !important; padding: 10px; border-radius: 8px; text-align: center; font-size: 0.85rem; border: 1px solid #00FF88 !important; font-weight: bold; text-decoration: none; display: block; }
        .stButton>button { width: 100%; border: 2px solid #00FF88 !important; background-color: #000000 !important; color: #00FF88 !important; font-weight: bold !important; }
        label p { color: #FFFFFF !important; font-weight: bold !important; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    
    # Session State 초기화
    if 'p_name' not in st.session_state: st.session_state.p_name = ""
    if 'p_price' not in st.session_state: st.session_state.p_price = ""
    if 'p_exclude' not in st.session_state: st.session_state.p_exclude = "직구, 해외, 렌탈, 당근, 중고"
    if 'results' not in st.session_state: st.session_state.results = None

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span style="font-size:0.8rem; color:#444;">v2.7</span></div>', unsafe_allow_html=True)

    name_input = st.text_input("📦 제품명 입력", value=st.session_state.p_name)
    price_input = st.text_input("💰 나의 확인가 (숫자만)", value=st.session_state.p_price)
    exclude_input = st.text_input("🚫 제외 단어", value=st.session_state.p_exclude)

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("🔍 시세 판독 실행"):
            if name_input:
                st.session_state.p_name, st.session_state.p_price, st.session_state.p_exclude = name_input, price_input, exclude_input
                with st.spinner('🏘️ 최적 경로 분석 중...'):
                    raw = AdvancedSearchEngine.search_all(name_input)
                    st.session_state.results = AdvancedSearchEngine.categorize_deals(raw, name_input, exclude_input)
                    st.rerun()
    with c2:
        if st.button("🔄 리셋"):
            for key in ['p_name', 'p_price', 'p_exclude', 'results']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    if st.session_state.results:
        st.markdown("### 📊 분석 리포트")
        for key, prices in sorted(st.session_state.results.items(), reverse=True):
            min_p, count = prices[0], len(prices)
            rel_txt, rel_col = ("🟢 신뢰도 높음", "#00FF88") if count >= 4 else ("🔴 신뢰도 낮음", "#FF5555")
            
            st.markdown(f'''
            <div class="detail-card">
                <span style="color:{rel_col}; font-weight:bold; font-size:0.8rem;">{rel_txt} (표본 {count}건)</span><br>
                <span style="color:white; font-weight:bold; font-size:1.1rem;">{key}</span>
                <span class="price-highlight">{min_p:,}원</span>
            </div>
            ''', unsafe_allow_html=True)
            
            if st.session_state.p_price.isdigit():
                user_p = int(st.session_state.p_price)
                diff = user_p - min_p
                if diff <= 0: st.markdown('<div class="judgment-box" style="background:#004d40; color:#00FF88;">✅ 판결: 역대급 최저가! 즉시 지르세요!</div>', unsafe_allow_html=True)
                elif diff < min_p * 0.1: st.markdown(f'<div class="judgment-box" style="background:#424200; color:#FFD700;">⚠️ 판결: 준수한 가격 (차액: {diff:,}원)</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="judgment-box" style="background:#4d0000; color:#FF5555;">❌ 판결: 아직 비쌈! (차액: {diff:,}원)</div>', unsafe_allow_html=True)

        st.markdown("### 🔗 실시간 근거 데이터 및 리뷰")
        e_q = urllib.parse.quote(st.session_state.p_name)
        l_col, r_col = st.columns(2)
        with l_col:
            st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={e_q}&category=1" class="link-btn-box">뽐뿌 시세</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.clien.net/service/search?q={e_q}" class="link-btn-box">클리앙 시세</a>', unsafe_allow_html=True)
        with r_col:
            # [수정] 뽐뿌 사용기 링크: 구매게시판(9) + 사용기(10) 통합 검색 결과로 연결
            st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={e_q}&category=2" class="review-btn-box">뽐뿌 사용기/후기</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.clien.net/service/search/board/use?sk=title&sv={e_q}" class="review-btn-box">클리앙 리뷰</a>', unsafe_allow_html=True)

if __name__ == "__main__": main()

# Version: v2.7 - Fixed Ppomppu Review Link, Maintained Robust Cross-Category Validation