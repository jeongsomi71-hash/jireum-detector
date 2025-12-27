
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. CORE ENGINE (기능 유지)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        url = f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=1"
        all_data = []
        try:
            res = requests.get(url, headers=AdvancedSearchEngine.get_mobile_headers(), timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('.title')
            for item in items:
                for extra in item.find_all(['span', 'em', 'font']):
                    extra.decompose()
                p_title = item.get_text(strip=True)
                p_title = re.sub(r'[\(\[]\d+[\)\]]$', '', p_title).strip()
                if p_title: all_data.append({"title": p_title})
        except: pass
        return all_data

    @staticmethod
    def categorize_deals(items, user_excludes, search_query):
        raw_first_word = search_query.strip().split()[0] if search_query else ""
        clean_first_word = re.sub(r'[^a-zA-Z0-9가-힣]', '', raw_first_word).lower()
        gift_keywords = ["상품권", "증정", "페이백", "포인트", "캐시백", "이벤트", "경품"]
        base_excludes = ["중고", "사용감", "리퍼", "S급", "민팃", "삽니다", "매입"]
        total_excludes = base_excludes + [x.strip() for x in user_excludes.split(',') if x.strip()]
        exclude_pattern = re.compile('|'.join(map(re.escape, total_excludes)))
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        raw_results = []
        for item in items:
            title = item['title']
            clean_title = re.sub(r'[^a-zA-Z0-9가-힣]', '', title).lower()
            if clean_first_word and clean_first_word not in clean_title: continue
            if exclude_pattern.search(title): continue
            found = price_pattern.findall(title)
            if not found: continue
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            if num < 5000: continue 
            if any(k in title for k in gift_keywords) and num < 100000: continue
            raw_results.append({"price": num, "title": title})

        if not raw_results: return {}
        prices = [x['price'] for x in raw_results]
        q1, q3 = np.percentile(prices, [25, 75])
        iqr = q3 - q1
        filtered_results = [x for x in raw_results if (q1 - 1.5*iqr) <= x['price'] <= (q3 + 1.5*iqr)]

        categorized = {}
        for item in filtered_results:
            t_low = item['title'].lower()
            spec = "일반"
            if "10인" in t_low: spec = "10인용"
            elif "6인" in t_low: spec = "6인용"
            if "256" in t_low: spec += " 256G"
            elif "512" in t_low: spec += " 512G"
            if spec not in categorized: categorized[spec] = []
            categorized[spec].append(item)
        return categorized

# ==========================================
# 2. UI DESIGN (입력창 시인성 강화)
# ==========================================
def apply_premium_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        
        /* 1. 레이블 (흰색 고정) */
        label p { color: #FFFFFF !important; font-weight: 800 !important; font-size: 1.1rem !important; margin-bottom: 5px; }
        
        /* 2. 입력창 (흰색 배경 + 검정 글자) */
        .stTextInput input {
            background-color: #FFFFFF !important;
            color: #000000 !important; /* 입력 후 글자색: 검정 */
            border: 2px solid #DDDDDD !important;
            border-radius: 10px !important;
            height: 3rem !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        
        /* 3. 입력 전 가이드 텍스트 (Placeholder) 색상 */
        .stTextInput input::placeholder {
            color: #666666 !important; /* 가이드 글자색: 진한 회색 */
            opacity: 1;
        }

        /* 4. 입력창 포커스 시 테두리 */
        .stTextInput input:focus {
            border-color: #00FF88 !important;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.2) !important;
        }

        /* 헤더/기타 스타일 */
        .main-title { font-size: 2.2rem; font-weight: 900; color: #00FF88 !important; text-align: center; margin-bottom: 5px; }
        .sub-title { color: #CCCCCC !important; text-align: center; font-size: 0.85rem; margin-bottom: 30px; }

        .stButton>button { width: 100%; border-radius: 10px; height: 3.5rem; font-weight: 800; font-size: 1.1rem; }
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button { background-color: #00FF88 !important; color: #000 !important; border: none !important; }
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button { background-color: transparent !important; color: #FF4B4B !important; border: 2px solid #FF4B4B !important; }

        .result-card { background-color: #111111; border: 2px solid #00FF88; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
        .price-text { color: #00FF88 !important; font-size: 2rem; font-weight: 900; float: right; }
        .title-text { color: #FFFFFF !important; font-size: 1.1rem; display: block; margin-bottom: 10px; line-height: 1.4; }
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_premium_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

    st.markdown('<div class="main-title">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">v7.2 VISIBILITY REFINED</div>', unsafe_allow_html=True)

    # 입력 영역
    rk = st.session_state.reset_key
    in_name = st.text_input("📦 검색 모델명", key=f"n_{rk}", placeholder="제품명을 입력하세요")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        in_price = st.text_input("💰 나의 확인가", key=f"p_{rk}", placeholder="가격을 입력하세요")
    with col_p2:
        in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고", key=f"e_{rk}")

    st.write("") 
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("🔍 판독 시작"):
            if in_name:
                with st.spinner('데이터 추출 중...'):
                    # 뽐뿌 검색 로직 호출
                    raw = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, in_exclude, in_name)
                    data = {"name": in_name, "user_price": in_price, "results": res, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    if data not in st.session_state.history: st.session_state.history.insert(0, data)
                    st.rerun()
    with c2:
        if st.button("🔄 리셋"):
            st.session_state.reset_key += 1
            st.session_state.current_data = None
            st.rerun()

    # 결과 표시
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("<hr style='border:1px solid #333'>", unsafe_allow_html=True)
        
        if not d['results']:
            clean_term = re.sub(r'[^a-zA-Z0-9가-힣]$', '', d['name'].split()[0])
            st.error(f'"{clean_term}" 검색 결과가 없습니다. 핵심 단어만 입력해 보세요.')
        else:
            for opt, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'''
                    <div class="result-card">
                        <span class="price-text">{best['price']:,}원</span>
                        <span class="title-text">[{opt}] {best['title']}</span>
                        <div style="clear:both;"></div>
                    </div>
                ''', unsafe_allow_html=True)

        # 뽐뿌 링크
        q_enc = urllib.parse.quote(d['name'])
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={q_enc}&category=1" target="_blank" style="text-decoration:none;"><div style="background-color:#1A1A1A; color:#00FF88; padding:15px; border-radius:10px; text-align:center; font-weight:700; border:1px solid #333;">🔗 뽐뿌 전체 결과 보기</div></a>', unsafe_allow_html=True)

    st.markdown('<div style="text-align:center; color:#555; font-size:0.75rem; margin-top:50px;">v7.2 | BLACK & WHITE CONTRAST</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()