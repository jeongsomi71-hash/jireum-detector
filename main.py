import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. CORE ENGINE (v6.9 기능 고정)
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
        if p > n: return "pos", "🔥 구매 적기: 여론이 매우 긍정적입니다."
        if n > p: return "neg", "🧊 관망 추천: 최근 종료되거나 평이 좋지 않습니다."
        return "neu", "💬 안정 시세: 특이사항 없는 평이한 수준입니다."

# ==========================================
# 2. UI/UX (가독성 & 밸런스 최적화)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        label p { color: #FFFFFF !important; font-weight: 500 !important; font-size: 0.95rem !important; }
        
        /* 헤더 스타일 */
        .main-header { padding: 1rem 0; text-align: center; }
        .main-title { font-size: 2rem; font-weight: 800; color: #00FF88 !important; }

        /* 입력창 디자인 (v7.2 색상 유지 + 굵기 조정) */
        .stTextInput input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #DDDDDD !important; /* 테두리 굵기 완화 */
            border-radius: 8px !important;
            height: 2.8rem !important;
            font-weight: 500 !important; /* 폰트 굵기 완화 */
        }
        .stTextInput input::placeholder { color: #888888 !important; }

        /* 버튼 디자인 */
        .stButton>button { width: 100%; border-radius: 8px; height: 3rem; font-weight: 700; font-size: 1rem; }
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button { background-color: #00FF88 !important; color: #000 !important; border: none !important; }
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button { background-color: transparent !important; color: #FF4B4B !important; border: 1px solid #FF4B4B !important; }
        
        /* 판독 결과 멘트 강조 (중요!) */
        .analysis-status { 
            padding: 18px; border-radius: 12px; text-align: center; font-weight: 900; 
            font-size: 1.25rem; margin-bottom: 25px; border: 2px solid;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .pos-box { background: rgba(0, 255, 136, 0.15); color: #00FF88; border-color: #00FF88; }
        .neg-box { background: rgba(255, 75, 75, 0.15); color: #FF4B4B; border-color: #FF4B4B; }
        .neu-box { background: #1A1A1A; color: #FFFFFF; border-color: #444; }
        
        /* 결과 카드 */
        .result-card { 
            background: #111111; border: 1px solid #333; 
            border-radius: 12px; padding: 18px; margin-bottom: 12px; 
        }
        .price-tag { color: #00FF88 !important; font-size: 1.8rem; font-weight: 800; float: right; }
        .item-title { color: #EEEEEE !important; font-size: 1rem; line-height: 1.4; display: block; margin-bottom: 5px; }
        
        /* 하단 링크 */
        .footer-link { background: #1A1A1A; color: #00FF88 !important; padding: 14px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: 700; border: 1px solid #333; }
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'rk' not in st.session_state: st.session_state.rk = 0 
    if 'input_q' not in st.session_state: st.session_state.input_q = ""

    st.markdown('<div class="main-header"><div class="main-title">⚖️ 지름신 판독기 PRO</div></div>', unsafe_allow_html=True)

    # 입력창
    rk = st.session_state.rk
    in_name = st.text_input("📦 검색 모델명", key=f"n_{rk}", value=st.session_state.input_q, placeholder="제품명 입력")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        in_price = st.text_input("💰 확인 가격", key=f"p_{rk}", placeholder="숫자만")
    with c_p2:
        in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고", key=f"e_{rk}")

    st.write("")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 판독 시작"):
            if in_name:
                with st.spinner('시세 분석 중...'):
                    raw = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, in_exclude, in_name)
                    s_type, s_msg = AdvancedSearchEngine.summarize_sentiment(raw)
                    data = {"name": in_name, "user_price": in_price, "results": res, "s_type": s_type, "s_msg": s_msg, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    st.session_state.input_q = in_name
                    if data not in st.session_state.history: st.session_state.history.insert(0, data)
                    st.rerun()
    with col2:
        if st.button("🔄 리셋"):
            st.session_state.rk += 1
            st.session_state.current_data = None
            st.session_state.input_q = ""
            st.rerun()

    # 결과 화면
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not d['results']:
            clean_term = re.sub(r'[^a-zA-Z0-9가-힣]$', '', d['name'].split()[0])
            st.error(f"'{clean_term}'에 대한 유효한 시세 정보가 없습니다.")
        else:
            # 판독 멘트 강조 표시 (v7.6 개선)
            st.markdown(f'<div class="analysis-status {d["s_type"]}-box">{d["s_msg"]}</div>', unsafe_allow_html=True)

            for spec, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'''
                    <div class="result-card">
                        <span class="price-tag">{best['price']:,}원</span>
                        <span class="item-title"><b>[{spec}]</b> {best['title']}</span>
                        <div style="clear:both;"></div>
                    </div>
                ''', unsafe_allow_html=True)
                
                if d['user_price'].isdigit():
                    diff = int(d['user_price']) - best['price']
                    if diff <= 0: st.success("✅ 역대급 가격입니다! 지금 지르셔도 좋습니다.")
                    else: st.error(f"❌ 최저가보다 {diff:,}원 더 비쌉니다. 조금 더 기다려보세요.")

        q_url = urllib.parse.quote(d['name'])
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={q_url}&category=1" target="_blank" class="footer-link">🔗 뽐뿌에서 게시글 직접 확인하기</a>', unsafe_allow_html=True)

    # 이력 관리 (기능 복구)
    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력 (클릭 시 복원)")
        for idx, h in enumerate(st.session_state.history[:5]):
            if st.button(f"[{h['time']}] {h['name']}", key=f"hist_{idx}"):
                st.session_state.current_data = h
                st.session_state.input_q = h['name'] # 검색어 복원
                st.rerun()

    st.markdown('<div style="text-align:center; color:#444; font-size:0.7rem; margin-top:50px; font-weight:bold;">v7.6 | BALANCED UX & HISTORY RESTORE</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()