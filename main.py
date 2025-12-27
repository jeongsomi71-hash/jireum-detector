import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. 시세 분석 엔진
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
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        filtered_results = [x for x in raw_results if lower_bound <= x['price'] <= upper_bound]

        categorized = {}
        for item in filtered_results:
            title = item['title']
            t_low = title.lower()
            spec_tag = "일반"
            if any(k in t_low for k in ["10인용", "10인"]): spec_tag = "10인용"
            elif any(k in t_low for k in ["6인용", "6인"]): spec_tag = "6인용"
            if "256" in t_low: spec_tag += " 256G"
            elif "512" in t_low: spec_tag += " 512G"
            if spec_tag not in categorized: categorized[spec_tag] = []
            categorized[spec_tag].append(item)
        return {k: v for k, v in categorized.items() if v}

    @staticmethod
    def summarize_sentiment(items):
        if not items: return None, "데이터 부족"
        pos_k = ["역대급", "최저가", "좋네요", "가성비", "지름", "추천", "만족"]
        neg_k = ["품절", "종료", "비싸", "아쉽", "비추", "불만"]
        txt = " ".join([i['title'] for i in items])
        p = sum(1 for k in pos_k if k in txt)
        n = sum(1 for k in neg_k if k in txt)
        if p > n: return "pos", "🔥 **긍정**: 실사용자들의 평이 좋고 가성비가 우수한 편입니다."
        if n > p: return "neg", "🧊 **주의**: 최근 평이 좋지 않거나 종료된 딜일 수 있습니다."
        return "neu", "💬 **안정**: 현재 시세와 실사용 여론은 평이한 수준입니다."

# ==========================================
# 2. UI 메인 로직
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v6.8", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .stTextInput label p { color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; }
        .price-highlight { color: #00FF88 !important; font-size: 2.2rem !important; font-weight: 900 !important; float: right; }
        .core-title { color: white; font-weight: 900; font-size: 1.1rem; display: block; width: 100%; line-height: 1.4; margin-bottom: 10px; }
        
        /* 버튼 스타일 - 가시성 강화 */
        .stButton>button { width: 100%; font-weight: 900 !important; height: 3.5rem; border-radius: 8px; font-size: 1.1rem !important; }
        
        /* 🔍 시세 판독 실행 버튼 (Green) */
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button {
            background-color: #00FF88 !important;
            color: #000000 !important;
            border: none !important;
        }
        
        /* 🔄 리셋 버튼 (Red Outline) */
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button {
            background-color: transparent !important;
            color: #FF4B4B !important;
            border: 2px solid #FF4B4B !important;
        }

        .sentiment-highlight { padding: 15px; border-radius: 10px; font-size: 1.1rem; font-weight: bold; margin-bottom: 20px; text-align: center; border: 1px solid; }
        .pos-box { background-color: rgba(0, 255, 136, 0.1); border-color: #00FF88; color: #00FF88; }
        .neg-box { background-color: rgba(255, 85, 85, 0.1); border-color: #FF5555; color: #FF5555; }
        .neu-box { background-color: rgba(255, 255, 255, 0.05); border-color: #FFFFFF; color: #FFFFFF; }
        .link-btn { background-color: #1A1A1A !important; color: #00FF88 !important; padding: 12px; border-radius: 5px; text-align: center; font-size: 1rem; border: 1px solid #00FF88; text-decoration: none; display: block; margin-bottom: 8px; font-weight: bold; }
        .guide-box { background-color: #332200; border: 1px solid #FFD700; color: #FFD700; padding: 15px; border-radius: 8px; margin: 10px 0; font-size: 0.9rem; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'input_q' not in st.session_state: st.session_state.input_q = ""

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO v6.8</div>', unsafe_allow_html=True)

    # UI 유지: 입력창은 원래 스타일대로 깔끔하게
    in_name = st.text_input("📦 제품명 입력", value=st.session_state.input_q, key="name_box")
    in_price = st.text_input("💰 나의 확인가 (숫자만)", key="price_box")
    in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고", key="exclude_box")

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("🔍 시세 판독 실행"):
            if in_name:
                st.session_state.input_q = in_name
                with st.spinner('최저가 추정중...'):
                    raw = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, in_exclude, in_name)
                    s_type, s_msg = AdvancedSearchEngine.summarize_sentiment(raw)
                    data = {"name": in_name, "user_price": in_price, "results": res, "s_type": s_type, "s_msg": s_msg, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    if data not in st.session_state.history: st.session_state.history.insert(0, data)
                    st.rerun()
    with c2:
        if st.button("🔄 리셋"):
            # 에러 방지를 위한 강제 리셋 로직
            st.session_state.input_q = ""
            st.session_state.current_data = None
            st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        
        if not d['results']:
            first_term = re.sub(r'[^a-zA-Z0-9가-힣]$', '', d['name'].split()[0])
            st.markdown(f'''
            <div class="guide-box">
                ⚠️ <b>시세 정보 추출 실패</b><br>
                입력하신 핵심 키워드 "{first_term}" 가 포함된 유효한 가격 정보가 없습니다<br>
                - 검색어를 더 단순하게 입력하거나 정확한 모델명을 입력해보세요
            </div>
            ''', unsafe_allow_html=True)
        else:
            box_class = f"{d['s_type']}-box" if d['s_type'] else "neu-box"
            st.markdown(f'<div class="sentiment-highlight {box_class}">{d["s_msg"]}</div>', unsafe_allow_html=True)

            for opt_key, items in sorted(d['results'].items(), reverse=True):
                items = sorted(items, key=lambda x: x['price'])
                best = items[0]
                st.markdown(f'''
                <div class="detail-card">
                    <span class="price-highlight">{best['price']:,}원</span>
                    <span class="core-title">{best['title']}</span>
                </div>
                ''', unsafe_allow_html=True)
                
                if d['user_price'].isdigit():
                    diff = int(d['user_price']) - best['price']
                    if diff <= 0: st.markdown('<div style="padding:12px; border-radius:8px; font-weight:900; text-align:center; margin-top:10px; background:#004d40; color:#00FF88;">✅ 즉시 지르세요!</div>', unsafe_allow_html=True)
                    else: st.markdown(f'<div style="padding:12px; border-radius:8px; font-weight:900; text-align:center; margin-top:10px; background:#4d0000; color:#FF5555;">❌ 차액 {diff:,}원 발생</div>', unsafe_allow_html=True)

        eq = urllib.parse.quote(d['name'])
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={eq}&category=1" class="link-btn" target="_blank">뽐뿌 게시판 바로가기</a>', unsafe_allow_html=True)

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력")
        for idx, h in enumerate(st.session_state.history[:10]):
            if st.button(f"[{h['time']}] {h['name']}", key=f"hi_{idx}"):
                st.session_state.input_q = h['name']
                st.session_state.current_data = h
                st.rerun()

    st.markdown('<div style="text-align:center; color:#444; font-size:0.8rem; margin-top:50px; font-weight:bold;">Version: v6.8 - Clean UI & Button Separation</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()