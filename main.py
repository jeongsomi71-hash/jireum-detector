import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. CORE ENGINE (고정된 핵심 로직)
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

    @staticmethod
    def summarize_sentiment(items):
        if not items: return None, "데이터 부족"
        txt = " ".join([i['title'] for i in items])
        p = sum(1 for k in ["역대급", "최저가", "좋네요", "가성비", "지름"] if k in txt)
        n = sum(1 for k in ["품절", "종료", "비싸", "아쉽", "비추"] if k in txt)
        if p > n: return "pos", "🔥 구매 적기: 실사용자 여론이 매우 긍정적입니다."
        if n > p: return "neg", "🧊 관망 추천: 최근 부정적인 의견이나 종료된 딜이 많습니다."
        return "neu", "💬 평이함: 시세가 안정적이며 특이사항이 없습니다."

# ==========================================
# 2. TRENDY UI COMPONENTS
# ==========================================
def apply_premium_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Spoqa+Han+Sans+Neo:wght@100;400;700&display=swap');
        * { font-family: 'Spoqa Han Sans Neo', sans-serif; }
        [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #0f1115 0%, #000000 100%); }
        
        /* Header Area */
        .main-header { padding: 2rem 0; text-align: center; }
        .main-title { font-size: 2.2rem; font-weight: 800; background: linear-gradient(90deg, #00FF88, #60efff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
        .sub-title { color: #888; font-size: 0.9rem; letter-spacing: 2px; }

        /* Card System */
        .glass-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 20px; margin-bottom: 15px; }
        .price-tag { color: #00FF88; font-size: 1.8rem; font-weight: 700; }
        .product-name { color: #fff; font-size: 1rem; line-height: 1.5; font-weight: 400; margin-bottom: 8px; }
        
        /* Buttons */
        .stButton>button { border-radius: 12px; height: 3.5rem; font-weight: 700; transition: all 0.2s; border: none; }
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button { background: linear-gradient(90deg, #00FF88, #00BD65) !important; color: #000 !important; }
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 255, 136, 0.3); }
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button { background: transparent !important; color: #FF4B4B !important; border: 1px solid #FF4B4B !important; }
        
        /* Indicators */
        .sentiment-badge { padding: 8px 16px; border-radius: 50px; font-weight: 700; font-size: 0.85rem; display: inline-block; margin-bottom: 1rem; }
        .pos-badge { background: rgba(0, 255, 136, 0.1); color: #00FF88; border: 1px solid #00FF88; }
        .neg-badge { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid #FF4B4B; }
        .neu-badge { background: rgba(255, 255, 255, 0.1); color: #fff; border: 1px solid #fff; }
        
        /* Input Styling */
        .stTextInput>div>div>input { background-color: rgba(255,255,255,0.05) !important; border-color: rgba(255,255,255,0.1) !important; color: white !important; border-radius: 10px !important; }
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_premium_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

    # Header Section
    st.markdown('<div class="main-header"><div class="main-title">지름신 판독기 PRO</div><div class="sub-title">SMART SHOPPING AI ADVISOR v7.0</div></div>', unsafe_allow_html=True)

    # Input Section
    with st.container():
        rk = st.session_state.reset_key
        in_name = st.text_input("🎯 검색 모델명", key=f"n_{rk}", placeholder="예: 아이폰 15 프로")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            in_price = st.text_input("💵 나의 확인가", key=f"p_{rk}", placeholder="숫자만 입력")
        with col_p2:
            in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고", key=f"e_{rk}")

    st.write("") # 스페이서
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("🔍 판독 시작"):
            if in_name:
                with st.spinner('데이터 분석 중...'):
                    raw = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, in_exclude, in_name)
                    s_type, s_msg = AdvancedSearchEngine.summarize_sentiment(raw)
                    data = {"name": in_name, "user_price": in_price, "results": res, "s_type": s_type, "s_msg": s_msg, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    if data not in st.session_state.history: st.session_state.history.insert(0, data)
                    st.rerun()
    with c2:
        if st.button("🔄 리셋"):
            st.session_state.reset_key += 1
            st.session_state.current_data = None
            st.rerun()

    # Result Section
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("---")
        
        if not d['results']:
            # 쉼표 제거 로직 포함
            clean_term = re.sub(r'[^a-zA-Z0-9가-힣]$', '', d['name'].split()[0])
            st.error(f'⚠️ 핵심 키워드 "{clean_term}" 에 대한 유효한 시세 정보가 없습니다.')
        else:
            # Sentiment Badge
            badge_class = f"{d['s_type']}-badge"
            st.markdown(f'<div class="sentiment-badge {badge_class}">{d["s_msg"]}</div>', unsafe_allow_html=True)

            for opt, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'''
                    <div class="glass-card">
                        <div class="product-name">[{opt}] {best['title']}</div>
                        <div class="price-tag">{best['price']:,}원</div>
                    </div>
                ''', unsafe_allow_html=True)
                
                if d['user_price'].isdigit():
                    diff = int(d['user_price']) - best['price']
                    if diff <= 0: st.success("✅ 현재 확인하신 가격이 핫딜보다 저렴하거나 비슷합니다! 지르세요.")
                    else: st.warning(f"❌ 핫딜 대비 {diff:,}원 비쌉니다. 조금 더 기다려보세요.")

        # Action Link
        q_enc = urllib.parse.quote(d['name'])
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={q_enc}&category=1" target="_blank" style="text-decoration:none;"><div style="background:rgba(255,255,255,0.05); color:#00FF88; padding:15px; border-radius:12px; text-align:center; font-weight:700; border:1px solid rgba(0,255,136,0.3);">🔗 뽐뿌 검색 결과 전체 보기</div></a>', unsafe_allow_html=True)

    # History Footer
    if st.session_state.history:
        with st.expander("📜 최근 판독 이력 보기"):
            for h in st.session_state.history[:5]:
                st.text(f"[{h['time']}] {h['name']}")

    st.markdown('<div style="text-align:center; color:#444; font-size:0.75rem; margin-top:50px;">PREMIUM ANALYTICS ENGINE v7.0</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
