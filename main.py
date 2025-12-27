import streamlit as st
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# [1] 설정
VERSION = "8.3.8"
ICON_URL = "https://cdn-icons-png.flaticon.com/512/2933/2933116.png"

st.set_page_config(page_title="지름 판독기", page_icon=ICON_URL, layout="centered")

# [2] PWA 이름/아이콘 강제 주입 (Iframe 우회 스크립트)
components.html(
    f"""
    <script>
    function forcePWA() {{
        const target = window.parent.document;
        // 타이틀 설정
        target.title = "지름 판독기";
        // 아이콘 설정
        let icon = target.querySelector("link[rel='apple-touch-icon']") || target.createElement('link');
        icon.rel = 'apple-touch-icon';
        icon.href = '{ICON_URL}';
        target.getElementsByTagName('head')[0].appendChild(icon);
        // PWA 이름 설정
        let meta = target.querySelector("meta[name='apple-mobile-web-app-title']") || target.createElement('meta');
        meta.name = 'apple-mobile-web-app-title';
        meta.content = '지름 판독기';
        target.getElementsByTagName('head')[0].appendChild(meta);
    }}
    forcePWA();
    setTimeout(forcePWA, 2000); // 로딩 후 다시 시도
    </script>
    """,
    height=0,
)

# ==========================================
# 3. CORE ENGINE (v8.2 정밀 복구)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        # [핵심] category=8을 가장 앞으로 배치하여 필터 고정
        url = f"https://m.ppomppu.co.kr/new/search_result.php?category=8&search_type=sub_memo&keyword={encoded_query}"
        all_data = []
        try:
            res = requests.get(url, headers=AdvancedSearchEngine.get_mobile_headers(), timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.select('.title')
            for item in items:
                for extra in item.find_all(['span', 'em', 'font']):
                    extra.decompose()
                p_title = item.get_text(strip=True)
                if p_title: all_data.append({"title": p_title})
        except: pass
        return all_data

    @staticmethod
    def categorize_deals(items, user_excludes, search_query):
        # IQR 로직 및 필터링
        base_excludes = ["중고", "사용감", "리퍼", "S급", "민팃", "삽니다", "매입"]
        total_excludes = base_excludes + [x.strip() for x in user_excludes.split(',') if x.strip()]
        exclude_pattern = re.compile('|'.join(map(re.escape, total_excludes)))
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        raw_results = []
        for item in items:
            title = item['title']
            if exclude_pattern.search(title): continue
            found = price_pattern.findall(title)
            if not found: continue
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            if num < 5000: continue 
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
# 4. UI/UX (디자인/리셋/버전)
# ==========================================
def apply_style():
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
        .main-header {{ padding: 1.5rem 0; text-align: center; }}
        .main-title {{ font-size: 1.8rem; font-weight: 800; color: #00FF88 !important; }}
        .stButton>button {{ width: 100%; border-radius: 8px; height: 3rem; font-weight: 700; }}
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button {{ background-color: #00FF88 !important; color: #000 !important; }}
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button {{ background-color: transparent !important; color: #FF4B4B !important; border: 1px solid #FF4B4B !important; }}
        .section-card {{ background: #111111; border: 1px solid #333; border-radius: 12px; padding: 18px; margin-bottom: 12px; }}
        .price-tag {{ color: #00FF88 !important; font-size: 1.5rem; font-weight: 800; float: right; }}
        .footer-link {{ background: #1A1A1A; color: #00FF88 !important; padding: 14px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: 700; border: 1px solid #333; margin-top: 20px; }}
        .version-tag {{ text-align: center; color: #444; font-size: 0.7rem; margin-top: 40px; }}
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'input_name' not in st.session_state: st.session_state.input_name = ""
    if 'input_price' not in st.session_state: st.session_state.input_price = ""

    st.markdown('<div class="main-header"><div class="main-title">⚖️ 지름 판독기</div></div>', unsafe_allow_html=True)

    st.session_state.input_name = st.text_input("📦 검색 모델명", value=st.session_state.input_name)
    st.session_state.input_price = st.text_input("💰 나의 가격 (숫자)", value=st.session_state.input_price)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 판독 엔진 가동"):
            if st.session_state.input_name:
                raw = AdvancedSearchEngine.search_all(st.session_state.input_name)
                res = AdvancedSearchEngine.categorize_deals(raw, "직구, 해외", st.session_state.input_name)
                data = {"name": st.session_state.input_name, "price": st.session_state.input_price, "results": res, "time": datetime.now().strftime('%H:%M')}
                st.session_state.current_data = data
                st.session_state.history.insert(0, data)
                st.rerun()
    with col2:
        if st.button("🔄 리셋"):
            st.session_state.current_data = None
            st.session_state.input_name = ""
            st.session_state.input_price = ""
            st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        if d['results']:
            for spec, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'<div class="section-card"><span class="price-tag">{best["price"]:,}원</span><b>[{spec}]</b><br>{best["title"]}</div>', unsafe_allow_html=True)

        # 뽐뿌게시판 카테고리 고정 링크
        q_url = urllib.parse.quote(d['name'])
        fixed_link = f"https://m.ppomppu.co.kr/new/search_result.php?category=8&search_type=sub_memo&keyword={q_url}"
        st.markdown(f'<a href="{fixed_link}" target="_blank" class="footer-link">🔗 뽐뿌게시판 실시간 결과 보기</a>', unsafe_allow_html=True)

    st.markdown(f'<div class="version-tag">⚖️ 지름 판독기 PRO v{VERSION}</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()