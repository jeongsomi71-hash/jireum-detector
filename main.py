import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. 시세 분석 및 정보 필터링 엔진
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def sanitize_text(text):
        """작성자 ID, 닉네임, 이메일 등 민감 정보 제거 (v3.4 신규)"""
        # 1. 이메일 형식 제거
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        # 2. 아이디로 추정되는 패턴 제거 (예: ID: gildong123, 닉네임: 홍길동 등)
        text = re.sub(r'(ID|id|아이디|닉네임|작성자|글쓴이)\s*[:：]\s*\S+', '', text)
        # 3. 연속된 영문+숫자 (아이디 패턴) 6자리 이상 제거 (선별적 적용)
        text = re.sub(r'\b[a-z0-9]{8,}\b', '', text)
        return text.strip()

    @staticmethod
    def extract_core_keyword(full_title):
        """핵심 키워드 추출 및 민감 정보 정제"""
        clean_name = AdvancedSearchEngine.sanitize_text(full_title)
        # 특수문자 및 불필요한 수식어 제거
        clean_name = re.sub(r'\[.*?\]|\(.*?\)|\!|\?|\★|\☆', '', clean_name)
        # 가격 정보나 날짜 정보 제거
        clean_name = re.sub(r'[0-9,]{4,}원|[0-9]{1,2}\/[0-9]{1,2}', '', clean_name)
        
        words = clean_name.split()
        return " ".join(words[:6]) if len(words) > 6 else " ".join(words)

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
        raw_prices = [p[0] for p in price_list]
        prices_sorted = sorted(list(set(raw_prices)))
        if 1 < len(prices_sorted) <= 3:
            if prices_sorted[0] < prices_sorted[1] * 0.5: prices_sorted.pop(0)
        elif len(prices_sorted) >= 4:
            arr = np.array(prices_sorted)
            mean, std = np.mean(arr), np.std(arr)
            prices_sorted = [p for p in prices_sorted if (mean - 3*std) <= p <= (mean + 3*std)]
        final_data = [p for p in price_list if p[0] in prices_sorted]
        return sorted(final_data, key=lambda x: x[0])

    @staticmethod
    def summarize_sentiment(titles):
        if not titles: return "데이터 부족"
        pos_k, neg_k = ["역대급", "최저가", "좋네요", "가성비", "지름", "추천"], ["품절", "종료", "비싸", "아쉽", "비추"]
        txt = " ".join(titles)
        p, n = sum(1 for k in pos_k if k in txt), sum(1 for k in neg_k if k in txt)
        if p > n: return "🔥 **긍정**: 가성비가 훌륭하며 커뮤니티 추천 빈도가 높습니다."
        if n > p: return "🧊 **주의**: 최근 가격 상승이나 품절 이슈가 확인됩니다."
        return "💬 **안정**: 시세 변동이 적고 평이 무난한 상태입니다."

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
            spec_tag = "기본"
            if any(k in t_low for k in ["10인용", "10인"]): spec_tag = "10인용"
            elif any(k in t_low for k in ["6인용", "6인"]): spec_tag = "6인용"
            if "256" in t_low: spec_tag += " 256G"
            elif "512" in t_low: spec_tag += " 512G"
            elif "울트라" in t_low or "ultra" in t_low: spec_tag += " Ultra"

            if spec_tag not in categorized: categorized[spec_tag] = []
            # 저장 시점에 텍스트에서 민감 정보 제거
            safe_text = AdvancedSearchEngine.sanitize_text(text)
            categorized[spec_tag].append((num, safe_text))
        
        cleaned = {k: AdvancedSearchEngine.clean_prices_robust(v) for k, v in categorized.items()}
        if "10인용" in cleaned and "6인용" in cleaned:
            if cleaned["10인용"][0][0] < cleaned["6인용"][0][0] * 0.8:
                if len(cleaned["10인용"]) > 1: cleaned["10인용"].pop(0)
        return {k: v for k, v in cleaned.items() if v}

# ==========================================
# 2. UI 및 로직 통합
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v3.4", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .stTextInput label p { color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; }
        .price-highlight { color: #00FF88 !important; font-size: 2.2rem !important; font-weight: 900 !important; float: right; }
        .core-title { color: white; font-weight: 900; font-size: 1.25rem; display: block; margin-bottom: 5px; }
        .full-title-meta { color: #777777; font-size: 0.8rem; line-height: 1.2; display: block; margin-top: 8px; font-style: italic; }
        .judgment-box { padding: 10px; border-radius: 8px; font-weight: 900; text-align: center; margin-top: 10px; font-size: 1.1rem; }
        .stButton>button { width: 100%; border: 2px solid #00FF88 !important; background-color: #000000 !important; color: #00FF88 !important; font-weight: bold !important; height: 3.5rem; }
        .link-btn { background-color: #1A1A1A !important; color: #00FF88 !important; padding: 10px; border-radius: 5px; text-align: center; font-size: 0.9rem; border: 1px solid #00FF88; text-decoration: none; display: block; margin-bottom: 5px; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 's_name' not in st.session_state: st.session_state.s_name = ""
    if 's_price' not in st.session_state: st.session_state.s_price = ""
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span style="font-size:0.8rem; color:#444;">v3.4</span></div>', unsafe_allow_html=True)

    in_name = st.text_input("📦 제품명 입력", value=st.session_state.s_name)
    in_price = st.text_input("💰 나의 확인가 (숫자만)", value=st.session_state.s_price)
    in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고")

    col_run, col_reset = st.columns([3, 1])
    with col_run:
        if st.button("🔍 시세 판독 실행"):
            if in_name:
                st.session_state.s_name, st.session_state.s_price = in_name, in_price
                with st.spinner('🏘️ 보안 필터링 및 시세 분석 중...'):
                    raw = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, in_name, in_exclude)
                    data = {"name": in_name, "user_price": in_price, "results": res, "summary": AdvancedSearchEngine.summarize_sentiment(raw), "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    st.session_state.history = [h for h in st.session_state.history if h['name'] != in_name]
                    st.session_state.history.insert(0, data)
                    st.rerun()
    with col_reset:
        if st.button("🔄 리셋"):
            st.session_state.s_name, st.session_state.s_price, st.session_state.current_data = "", "", None
            st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        st.info(d["summary"])
        
        if not d['results']:
            st.warning("분석 결과가 없습니다.")
        else:
            for opt_key, items in sorted(d['results'].items(), reverse=True):
                min_p, best_title = items[0]
                # 핵심 키워드 추출 시에도 민감 정보 재확인
                core_title = AdvancedSearchEngine.extract_core_keyword(best_title)
                count = len(items)
                rel_col = "#00FF88" if count >= 4 else "#FF5555"
                
                st.markdown(f'''
                <div class="detail-card">
                    <span style="color:{rel_col}; font-weight:bold; font-size:0.8rem;">신뢰도: {("보통" if count>=4 else "낮음")} (표본 {count}건)</span><br>
                    <span class="core-title">{core_title}</span>
                    <span class="price-highlight">{min_p:,}원</span>
                    <span class="full-title-meta">옵션: {opt_key} | 데이터: {best_title[:45]}...</span>
                </div>
                ''', unsafe_allow_html=True)
                
                if d['user_price'].isdigit():
                    user_p, diff = int(d['user_price']), int(d['user_price']) - min_p
                    if diff <= 0: st.markdown('<div class="judgment-box" style="background:#004d40; color:#00FF88;">✅ 판결: 즉시 지르세요!</div>', unsafe_allow_html=True)
                    elif diff < min_p * 0.1: st.markdown(f'<div class="judgment-box" style="background:#424200; color:#FFD700;">⚠️ 판결: 나쁘지 않은 가격 (차액: {diff:,}원)</div>', unsafe_allow_html=True)
                    else: st.markdown(f'<div class="judgment-box" style="background:#4d0000; color:#FF5555;">❌ 판결: 아직 비쌉니다 (차액: {diff:,}원)</div>', unsafe_allow_html=True)

        st.write("")
        eq = urllib.parse.quote(d['name'])
        cl1, cl2 = st.columns(2)
        cl1.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={eq}&category=1" class="link-btn">뽐뿌 확인</a>', unsafe_allow_html=True)
        cl2.markdown(f'<a href="https://www.clien.net/service/search?q={eq}" class="link-btn">클리앙 확인</a>', unsafe_allow_html=True)

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력 (10개)")
        for idx, h in enumerate(st.session_state.history[:10]):
            hist_price = "결과없음"
            if h['results']:
                try:
                    first_item = next(iter(h['results'].values()))[0]
                    hist_price = f"{first_item[0]:,}원"
                except: pass
            
            if st.button(f"[{h['time']}] {h['name']} ({hist_price})", key=f"hi_{idx}"):
                st.session_state.current_data = h
                st.session_state.s_name, st.session_state.s_price = h['name'], h['user_price']
                st.rerun()

if __name__ == "__main__": main()
# Version: v3.4 - Privacy Enhancement: Sanitize IDs, Emails and Nicknames from titles.