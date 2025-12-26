import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. 시세 분석 및 역전 방지 엔진 (기존 로직 유지)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        links = {
            "뽐뿌": f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=1",
            "클리앙": f"https://www.clien.net/service/search?q={encoded_query}"
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
    def summarize_sentiment(titles):
        if not titles: return "데이터가 부족하여 요약할 수 없습니다."
        pos_k = ["역대급", "최저가", "좋네요", "가성비", "지름", "추천", "구매"]
        neg_k = ["품절", "종료", "비싸요", "아쉽", "비추", "오름", "비싸"]
        full_text = " ".join(titles)
        pos_count = sum(1 for k in pos_k if k in full_text)
        neg_count = sum(1 for k in neg_k if k in full_text)
        if pos_count > neg_count: return "🔥 **긍정 여론**: 최근 가성비가 훌륭하며 커뮤니티 추천 빈도가 높습니다."
        elif neg_count > pos_count: return "🧊 **주의 여론**: 최근 가격 상승이나 품절 정보가 확인되니 주의하세요."
        return "💬 **일반 여론**: 큰 이슈 없이 꾸준한 시세를 형성하고 있습니다."

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
            if tag not in categorized: categorized[tag] = []
            categorized[tag].append(num)
        cleaned = {k: AdvancedSearchEngine.clean_prices_robust(v) for k, v in categorized.items()}
        if "10인용" in cleaned and "6인용" in cleaned:
            if cleaned["10인용"][0] < cleaned["6인용"][0] * 0.8:
                if len(cleaned["10인용"]) > 1: cleaned["10인용"].pop(0)
        return {k: v for k, v in cleaned.items() if v}

# ==========================================
# 2. UI 및 세션 제어 로직
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v2.9", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .main .block-container { max-width: 550px !important; padding-top: 5rem !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        /* 입력칸 제목(Label) 흰색 강조 */
        .stTextInput label p { color: #FFFFFF !important; font-size: 1.1rem !important; font-weight: bold !important; }
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; color: white; }
        .price-highlight { color: #00FF88 !important; font-size: 2rem !important; font-weight: 900 !important; float: right; }
        .judgment-box { padding: 10px; border-radius: 8px; font-weight: 900; text-align: center; margin-top: 10px; }
        .summary-box { background-color: #002b36 !important; border-left: 5px solid #00FF88 !important; padding: 15px; border-radius: 8px; margin: 20px 0; color: #93a1a1; font-size: 0.95rem; }
        .stButton>button { width: 100%; border: 2px solid #00FF88 !important; background-color: #000000 !important; color: #00FF88 !important; font-weight: bold !important; }
        .history-btn>button { background-color: #111 !important; color: #ccc !important; border: 1px solid #444 !important; text-align: left !important; font-size: 0.85rem !important; margin-bottom: 5px !important; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    
    # 세션 상태 초기화 (충돌 방지를 위해 위젯 key와 분리)
    if 's_name' not in st.session_state: st.session_state.s_name = ""
    if 's_price' not in st.session_state: st.session_state.s_price = ""
    if 's_exclude' not in st.session_state: st.session_state.s_exclude = "직구, 해외, 렌탈, 당근, 중고"
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span style="font-size:0.8rem; color:#444;">v2.9</span></div>', unsafe_allow_html=True)

    # 위젯 (key를 사용하지 않고 상태 변수와 직접 매핑하여 오류 방지)
    in_name = st.text_input("📦 제품명 입력", value=st.session_state.s_name)
    in_price = st.text_input("💰 나의 확인가 (숫자만)", value=st.session_state.s_price)
    in_exclude = st.text_input("🚫 제외 단어", value=st.session_state.s_exclude)

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("🔍 시세 판독 실행"):
            if in_name:
                # 현재 입력값 세션에 저장
                st.session_state.s_name = in_name
                st.session_state.s_price = in_price
                st.session_state.s_exclude = in_exclude
                
                with st.spinner('🏘️ AI 분석 중...'):
                    raw_titles = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw_titles, in_name, in_exclude)
                    summ = AdvancedSearchEngine.summarize_sentiment(raw_titles)
                    
                    data = {"name": in_name, "user_price": in_price, "results": res, "summary": summ, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    
                    # 히스토리 업데이트
                    st.session_state.history = [h for h in st.session_state.history if h['name'] != in_name]
                    st.session_state.history.insert(0, data)
                    if len(st.session_state.history) > 10: st.session_state.history.pop()
                    st.rerun()

    with c2:
        if st.button("🔄 리셋"):
            # 세션 상태만 초기화하고 rerun하여 위젯 강제 갱신 (API 오류 해결)
            st.session_state.s_name = ""
            st.session_state.s_price = ""
            st.session_state.s_exclude = "직구, 해외, 렌탈, 당근, 중고"
            st.session_state.current_data = None
            st.rerun()

    # 결과 출력
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown(f"### 📊 '{d['name']}' 분석 리포트")
        st.markdown(f'<div class="summary-box">{d["summary"]}</div>', unsafe_allow_html=True)
        
        for key, prices in sorted(d['results'].items(), reverse=True):
            min_p, count = prices[0], len(prices)
            rel_txt, rel_col = ("🟢 신뢰도 높음", "#00FF88") if count >= 4 else ("🔴 신뢰도 낮음", "#FF5555")
            
            st.markdown(f'''
            <div class="detail-card">
                <span style="color:{rel_col}; font-weight:bold; font-size:0.8rem;">{rel_txt} (표본 {count}건)</span><br>
                <span style="color:white; font-weight:bold; font-size:1.1rem;">{key}</span>
                <span class="price-highlight">{min_p:,}원</span>
            </div>
            ''', unsafe_allow_html=True)
            
            if d['user_price'].isdigit():
                user_p = int(d['user_price'])
                diff = user_p - min_p
                if diff <= 0: st.markdown('<div class="judgment-box" style="background:#004d40; color:#00FF88;">✅ 판결: 즉시 지르세요!</div>', unsafe_allow_html=True)
                elif diff < min_p * 0.1: st.markdown(f'<div class="judgment-box" style="background:#424200; color:#FFD700;">⚠️ 준수한 가격 (차액: {diff:,}원)</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="judgment-box" style="background:#4d0000; color:#FF5555;">❌ 아직 비쌈 (차액: {diff:,}원)</div>', unsafe_allow_html=True)

    # 히스토리 영역
    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력 (클릭 시 복구)")
        for idx, h in enumerate(st.session_state.history):
            if st.button(f"[{h['time']}] {h['name']} - {next(iter(h['results'].values()))[0]:,}원", key=f"h_{idx}"):
                st.session_state.current_data = h
                # 히스토리 클릭 시 입력 필드도 해당 값으로 동기화
                st.session_state.s_name = h['name']
                st.session_state.s_price = h['user_price']
                st.rerun()

if __name__ == "__main__": main()

# Version: v2.9 - Fixed Reset API Error, Enhanced Label Visibility (White Labels), Maintained All Previous Features