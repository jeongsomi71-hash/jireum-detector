import streamlit as st
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# 1. PWA 메타 태그 및 아이콘 강제 주입 (앱 설치 최적화)
components.html(
    """
    <script>
    const metaTitle = document.createElement('meta');
    metaTitle.name = "apple-mobile-web-app-title";
    metaTitle.content = "지름 판독기";
    document.getElementsByTagName('head')[0].appendChild(metaTitle);

    const metaCapable = document.createElement('meta');
    metaCapable.name = "apple-mobile-web-app-capable";
    metaCapable.content = "yes";
    document.getElementsByTagName('head')[0].appendChild(metaCapable);

    const linkIcon = document.createElement('link');
    linkIcon.rel = "apple-touch-icon";
    linkIcon.href = "https://cdn-icons-png.flaticon.com/512/2933/2933116.png";
    document.getElementsByTagName('head')[0].appendChild(linkIcon);
    </script>
    """,
    height=0,
)

# ==========================================
# 2. CORE ENGINE (뽐뿌게시판 category=8 고정)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        # category=8: 뽐뿌게시판 전용
        url = f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=8"
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
# 3. UI/UX (전체 스타일 고정)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름 판독기", page_icon="⚖️", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        label p { color: #FFFFFF !important; font-weight: 500 !important; }
        .main-header { padding: 1.5rem 0 1rem 0; text-align: center; }
        .main-title { font-size: 1.8rem; font-weight: 800; color: #00FF88 !important; display: inline-block; }
        .version-badge { color: #555; font-size: 0.75rem; font-weight: 800; margin-left: 8px; vertical-align: middle; border: 1px solid #333; padding: 2px 6px; border-radius: 4px; }
        .stTextInput input { background-color: #FFFFFF !important; color: #000000 !important; border-radius: 8px; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3rem; font-weight: 700; background-color: #00FF88 !important; color: #000 !important; }
        .section-card { background: #111111; border: 1px solid #333; border-radius: 12px; padding: 18px; margin-bottom: 12px; }
        .section-label { color: #888; font-size: 0.8rem; font-weight: 800; margin-bottom: 8px; display: block; border-left: 3px solid #00FF88; padding-left: 8px; }
        .content-text { color: #FFFFFF !important; font-size: 1.05rem; font-weight: 600; }
        .price-item { margin-bottom: 12px; border-bottom: 1px solid #222; padding-bottom: 10px; }
        .price-tag { color: #00FF88 !important; font-size: 1.5rem; font-weight: 800; float: right; }
        .item-title { color: #CCCCCC !important; font-size: 0.9rem; }
        .footer-link { background: #1A1A1A; color: #00FF88 !important; padding: 14px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: 700; border: 1px solid #333; margin-top: 20px; }
        .version-tag-footer { text-align: center; color: #333; font-size: 0.65rem; margin-top: 30px; }
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'input_val_name' not in st.session_state: st.session_state.input_val_name = ""
    if 'input_val_price' not in st.session_state: st.session_state.input_val_price = ""
    if 'input_val_exclude' not in st.session_state: st.session_state.input_val_exclude = "직구, 해외, 렌탈, 당근, 중고"

    st.markdown('<div class="main-header"><div class="main-title">⚖️ 지름 판독기</div><span class="version-badge">v8.2.6</span></div>', unsafe_allow_html=True)

    in_name = st.text_input("📦 검색 모델명", value=st.session_state.input_val_name)
    c_p1, c_p2 = st.columns(2)
    with c_p1: in_price = st.text_input("💰 나의 가격", value=st.session_state.input_val_price)
    with c_p2: in_exclude = st.text_input("🚫 제외 단어", value=st.session_state.input_val_exclude)

    if st.button("🔍 뽐뿌게시판 판독 시작"):
        if in_name:
            with st.spinner('뽐뿌게시판 실시간 분석 중...'):
                st.session_state.input_val_name = in_name
                st.session_state.input_val_price = in_price
                st.session_state.input_val_exclude = in_exclude
                raw = AdvancedSearchEngine.search_all(in_name)
                res = AdvancedSearchEngine.categorize_deals(raw, in_exclude, in_name)
                
                txt = " ".join([i['title'] for i in raw])
                p = sum(1 for k in ["역대급", "최저가", "좋네요", "추천"] if k in txt)
                n = sum(1 for k in ["품절", "종료", "비싸"] if k in txt)
                s_msg = "✅ 구매 추천" if p > n else "❌ 관망 추천" if n > p else "⚖️ 적정가"
                
                data = {"name": in_name, "user_price": in_price, "exclude": in_exclude, "results": res, "s_msg": s_msg, "time": datetime.now().strftime('%H:%M')}
                st.session_state.current_data = data
                if data not in st.session_state.history: st.session_state.history.insert(0, data)
                st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        st.write("---")
        if not d['results']:
            st.error("뽐뿌게시판 카테고리(category=8)에서 유효한 결과가 없습니다.")
        else:
            final_msg = d['s_msg']
            if d['user_price'].isdigit():
                all_p = [item['price'] for sublist in d['results'].values() for item in sublist]
                best_p = min(all_p)
                diff = int(d['user_price']) - best_p
                if diff <= 0: final_msg = "🔥 역대급 가격! 즉시 지름을 추천합니다."
                else: final_msg = f"❌ 현재 최저가보다 {diff:,}원 더 비쌉니다."

            st.markdown(f'<div class="section-card"><span class="section-label">판단결과</span><div class="content-text">{final_msg}</div></div>', unsafe_allow_html=True)
            
            for spec, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'<div class="price-item"><span class="price-tag">{best["price"]:,}원</span><span class="item-title"><b>[{spec}]</b> {best["title"]}</span><div style="clear:both;"></div></div>', unsafe_allow_html=True)

        q_url = urllib.parse.quote(d['name'])
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={q_url}&category=8" target="_blank" class="footer-link">🔗 뽐뿌게시판 원문 확인</a>', unsafe_allow_html=True)

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력")
        for idx, h in enumerate(st.session_state.history[:5]):
            if st.button(f"[{h['time']}] {h['name']}", key=f"hist_{idx}"):
                st.session_state.input_val_name = h['name']
                st.session_state.input_val_price = h['user_price']
                st.session_state.input_val_exclude = h['exclude']
                st.session_state.current_data = h
                st.rerun()

    st.markdown('<div class="version-tag-footer">⚖️ 지름 판독기 PRO v8.2.6</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
