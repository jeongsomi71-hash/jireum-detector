
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. CORE ENGINE (뽐뿌게시판 category=8 정밀 고정)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        # category=8 (뽐뿌게시판) 파라미터 우선순위 고정
        url = f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&category=8&keyword={encoded_query}"
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
        if not items: return "neu", "⚖️ 판단 보류", "확인된 후기가 없습니다."
        txt = " ".join([i['title'] for i in items])
        p = sum(1 for k in ["역대급", "최저가", "좋네요", "가성비", "지름", "추천", "만족"] if k in txt)
        n = sum(1 for k in ["품절", "종료", "비싸", "아쉽", "비추", "불만"] if k in txt)
        if p > n: return "pos", "✅ 현재 가격이 매우 훌륭합니다.", "💬 실사용자들의 만족도가 높고 구매 추천 의견이 지배적입니다."
        if n > p: return "neg", "❌ 지금 구매하기엔 아쉬운 가격입니다.", "💬 품절이 잦거나 가격 대비 아쉽다는 의견이 보입니다."
        return "neu", "⚖️ 적정 시세 범위 내에 있습니다.", "💬 전반적으로 평이하며 실사용 만족도는 무난한 수준입니다."

# ==========================================
# 2. UI/UX (v8.2 원복 및 PWA 아이콘 수정)
# ==========================================
def apply_style():
    # 브라우저 아이콘 및 타이틀 고정
    st.set_page_config(page_title="지름 판독기", page_icon="⚖️", layout="centered")
    
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        label p { color: #FFFFFF !important; font-weight: 500 !important; font-size: 0.95rem !important; }
        .main-header { padding: 1.5rem 0 1rem 0; text-align: center; }
        .main-title { font-size: 1.8rem; font-weight: 800; color: #00FF88 !important; display: inline-block; }
        .version-badge { color: #555; font-size: 0.75rem; font-weight: 800; margin-left: 8px; vertical-align: middle; border: 1px solid #333; padding: 2px 6px; border-radius: 4px; }
        .stTextInput input { background-color: #FFFFFF !important; color: #000000 !important; border: 1px solid #CCCCCC !important; border-radius: 8px; height: 2.8rem; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3rem; font-weight: 700; }
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button { background-color: #00FF88 !important; color: #000 !important; }
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button { background-color: transparent !important; color: #FF4B4B !important; border: 1px solid #FF4B4B !important; }
        .section-card { background: #111111; border: 1px solid #333; border-radius: 12px; padding: 18px; margin-bottom: 12px; }
        .section-label { color: #888; font-size: 0.8rem; font-weight: 800; margin-bottom: 8px; display: block; border-left: 3px solid #00FF88; padding-left: 8px; }
        .content-text { color: #FFFFFF !important; font-size: 1.05rem; font-weight: 600; }
        .price-item { margin-bottom: 12px; border-bottom: 1px solid #222; padding-bottom: 10px; padding-left: 5px; }
        .price-tag { color: #00FF88 !important; font-size: 1.5rem; font-weight: 800; float: right; }
        .item-title { color: #CCCCCC !important; font-size: 0.9rem; line-height: 1.4; display: block; }
        .footer-link { background: #1A1A1A; color: #00FF88 !important; padding: 14px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: 700; border: 1px solid #333; margin-top: 20px; }
        .version-tag-footer { text-align: center; color: #333; font-size: 0.65rem; margin-top: 30px; letter-spacing: 1px; }
        </style>
        
        <meta name="apple-mobile-web-app-title" content="지름 판독기">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2933/2933116.png">
        <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/512/2933/2933116.png">
    """, unsafe_allow_html=True)

def main():
    apply_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'input_val_name' not in st.session_state: st.session_state.input_val_name = ""
    if 'input_val_price' not in st.session_state: st.session_state.input_val_price = ""
    if 'input_val_exclude' not in st.session_state: st.session_state.input_val_exclude = "직구, 해외, 렌탈, 당근, 중고"

    # 타이틀 및 버전 (상단 유지)
    st.markdown('<div class="main-header"><div class="main-title">⚖️ 지름 판독기</div><span class="version-badge">v8.2.7</span></div>', unsafe_allow_html=True)

    in_name = st.text_input("📦 검색 모델명", value=st.session_state.input_val_name)
    c_p1, c_p2 = st.columns(2)
    with c_p1: in_price = st.text_input("💰 나의 가격 (숫자)", value=st.session_state.input_val_price)
    with c_p2: in_exclude = st.text_input("🚫 제외 단어", value=st.session_state.input_val_exclude)

    col1, col2 = st.columns([3, 1])
    with col1:
        # 문구 v8.2 버전으로 원복
        if st.button("🔍 판독 엔진 가동"):
            if in_name:
                with st.spinner('데이터 분석 중...'):
                    st.session_state.input_val_name = in_name
                    st.session_state.input_val_price = in_price
                    st.session_state.input_val_exclude = in_exclude
                    raw = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, in_exclude, in_name)
                    s_type, s_msg, s_review = AdvancedSearchEngine.summarize_sentiment(raw)
                    data = {"name": in_name, "user_price": in_price, "exclude": in_exclude, "results": res, "s_type": s_type, "s_msg": s_msg, "s_review": s_review, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    if data not in st.session_state.history: st.session_state.history.insert(0, data)
                    st.rerun()
    with col2:
        if st.button("🔄 리셋"):
            st.session_state.current_data = None
            st.session_state.input_val_name = ""
            st.session_state.input_val_price = ""
            st.session_state.input_val_exclude = "직구, 해외, 렌탈, 당근, 중고"
            st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        st.write("---")
        if not d['results']:
            st.error("뽐뿌게시판에서 분석 가능한 유효 데이터가 부족합니다.")
        else:
            final_msg = d['s_msg']
            if d['user_price'].isdigit():
                all_p = [item['price'] for sublist in d['results'].values() for item in sublist]
                best_p = min(all_p)
                diff = int(d['user_price']) - best_p
                if diff <= 0: final_msg = "🔥 역대급 가격입니다! 망설임 없이 지르세요."
                elif diff < best_p * 0.05: final_msg = "✅ 최저가와 비슷합니다. 충분히 메리트 있습니다."
                else: final_msg = f"❌ 관망 추천: 최저가보다 {diff:,}원 더 비쌉니다."

            st.markdown(f'<div class="section-card"><span class="section-label">판단결과</span><div class="content-text">{final_msg}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="section-card"><span class="section-label">만족도 후기 요약</span><div class="content-text">{d["s_review"]}</div></div>', unsafe_allow_html=True)
            
            for spec, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'''
                    <div class="price-item">
                        <span class="price-tag">{best['price']:,}원</span>
                        <span class="item-title"><b>[{spec}]</b> {best['title']}</span>
                        <div style="clear:both;"></div>
                    </div>
                ''', unsafe_allow_html=True)

        q_url = urllib.parse.quote(d['name'])
        # [뽐뿌게시판 정밀 링크] category=8 및 search_type 고정 적용
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&category=8&keyword={q_url}" target="_blank" class="footer-link">🔗 뽐뿌게시판 원문 결과 확인</a>', unsafe_allow_html=True)

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

    st.markdown('<div class="version-tag-footer">⚖️ 지름 판독기 PRO v8.2.7</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()