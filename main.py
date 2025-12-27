import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# [1] v8.2 순정 설정
st.set_page_config(page_title="지름 판독기", page_icon="⚖️", layout="centered")

# ==========================================
# 2. CORE ENGINE (v8.2 원본 로직 완벽 복구)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
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
    def summarize_sentiment(items):
        # [복구] v8.2의 감성 분석 엔진
        if not items: return "neu", "⚖️ 판단 보류", "확인된 후기가 없습니다."
        txt = " ".join([i['title'] for i in items])
        p = sum(1 for k in ["역대급", "최저가", "좋네요", "가성비", "추천"] if k in txt)
        n = sum(1 for k in ["품절", "종료", "비싸", "아쉽"] if k in txt)
        if p > n: return "pos", "✅ 현재 가격이 매우 훌륭합니다.", "💬 구매 추천 의견이 지배적입니다."
        if n > p: return "neg", "❌ 지금 구매하기엔 아쉬운 가격입니다.", "💬 시기가 좋지 않다는 의견이 보입니다."
        return "neu", "⚖️ 적정 시세 범위 내에 있습니다.", "💬 전반적으로 평이한 수준입니다."

    @staticmethod
    def categorize_deals(items, user_excludes, search_query):
        # [복구] v8.2의 IQR 및 스펙 분류 엔진
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
# 3. UI/UX (v8.2 순정 스타일)
# ==========================================
def apply_style():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        label p { color: #FFFFFF !important; font-weight: 500 !important; }
        .main-header { padding: 1.5rem 0; text-align: center; }
        .main-title { font-size: 1.8rem; font-weight: 800; color: #00FF88 !important; }
        .stTextInput input { border-radius: 8px; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3rem; font-weight: 700; background-color: #00FF88 !important; color: #000 !important; }
        .section-card { background: #111111; border: 1px solid #333; border-radius: 12px; padding: 18px; margin-bottom: 12px; }
        .price-tag { color: #00FF88 !important; font-size: 1.5rem; font-weight: 800; float: right; }
        .footer-link { background: #1A1A1A; color: #00FF88 !important; padding: 14px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: 700; border: 1px solid #333; margin-top: 20px; }
        .version-tag { text-align: center; color: #333; font-size: 0.7rem; margin-top: 50px; }
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None

    st.markdown('<div class="main-header"><div class="main-title">⚖️ 지름 판독기</div></div>', unsafe_allow_html=True)

    in_name = st.text_input("📦 검색 모델명", value=st.session_state.get('last_name', ""))
    in_price = st.text_input("💰 나의 가격 (숫자만)", value=st.session_state.get('last_price', ""))

    if st.button("🔍 판독 엔진 가동"):
        if in_name:
            with st.spinner('데이터 분석 중...'):
                raw = AdvancedSearchEngine.search_all(in_name)
                res = AdvancedSearchEngine.categorize_deals(raw, "직구, 해외", in_name)
                s_type, s_msg, s_review = AdvancedSearchEngine.summarize_sentiment(raw)
                data = {"name": in_name, "price": in_price, "results": res, "s_msg": s_msg, "s_review": s_review, "time": datetime.now().strftime('%H:%M:%S')}
                st.session_state.current_data = data
                st.session_state.history.insert(0, data)
                st.session_state.last_name = in_name
                st.session_state.last_price = in_price
                st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        st.write("---")
        if d['results']:
            # [복구] 최저가 대비 가격 분석 로직
            final_msg = d['s_msg']
            if d['price'].isdigit():
                all_prices = [item['price'] for sublist in d['results'].values() for item in sublist]
                min_p = min(all_prices)
                diff = int(d['price']) - min_p
                if diff <= 0: final_msg = "🔥 역대급 가격입니다! 즉시 구매를 추천합니다."
                else: final_msg = f"❌ 현재 최저가보다 {diff:,}원 더 비쌉니다."

            st.markdown(f'<div class="section-card"><span style="color:#888; font-size:0.8rem;">판단결과</span><br><div style="color:#FFF; font-weight:600;">{final_msg}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="section-card"><span style="color:#888; font-size:0.8rem;">만족도 요약</span><br><div style="color:#FFF; font-weight:600;">{d["s_review"]}</div></div>', unsafe_allow_html=True)

            for spec, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'<div class="section-card"><span class="price-tag">{best["price"]:,}원</span><b>[{spec}]</b><br>{best["title"]}</div>', unsafe_allow_html=True)

        q_url = urllib.parse.quote(d['name'])
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?category=8&search_type=sub_memo&keyword={q_url}" target="_blank" class="footer-link">🔗 뽐뿌게시판 실시간 결과 보기</a>', unsafe_allow_html=True)

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력")
        for idx, h in enumerate(st.session_state.history[:3]):
            if st.button(f"[{h['time']}] {h['name']}", key=f"h_v824_{idx}"):
                st.session_state.current_data = h
                st.session_state.last_name = h['name']
                st.session_state.last_price = h['price']
                st.rerun()

    st.markdown('<div class="version-tag">⚖️ 지름 판독기 PRO v8.2.4</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()