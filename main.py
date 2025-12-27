import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# [1] 최상단 설정 - 아이콘 및 타이틀 (PWA 및 즐겨찾기 대응)
ICON_URL = "https://cdn-icons-png.flaticon.com/512/2933/2933116.png"
st.set_page_config(page_title="지름 판독기", page_icon=ICON_URL, layout="centered")

# ==========================================
# 2. CORE ENGINE (v8.2 무결성 완벽 복구)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        # 뽐뿌게시판(category=8) 경로 절대 고정
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
                p_title = re.sub(r'[\(\[]\d+[\)\]]$', '', p_title).strip()
                if p_title: all_data.append({"title": p_title})
        except: pass
        return all_data

    @staticmethod
    def categorize_deals(items, user_excludes, search_query):
        # [v8.2 복구] 이상치 제거 및 스펙 분류 엔진
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
        
        # IQR 로직 복구
        prices = [x['price'] for x in raw_results]
        q1, q3 = np.percentile(prices, [25, 75])
        iqr = q3 - q1
        filtered_results = [x for x in raw_results if (q1 - 1.5*iqr) <= x['price'] <= (q3 + 1.5*iqr)]

        # 스펙 분류 로직 복구
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
        p = sum(1 for k in ["역대급", "최저가", "좋네요", "가성비", "추천"] if k in txt)
        n = sum(1 for k in ["품절", "종료", "비싸", "아쉽"] if k in txt)
        if p > n: return "pos", "✅ 현재 가격이 매우 훌륭합니다.", "💬 구매 추천 의견이 지배적입니다."
        if n > p: return "neg", "❌ 지금 구매하기엔 아쉬운 가격입니다.", "💬 시기가 좋지 않다는 의견이 보입니다."
        return "neu", "⚖️ 적정 시세 범위 내에 있습니다.", "💬 전반적으로 평이한 수준입니다."

# ==========================================
# 3. UI/UX (v8.2 스타일 원복 및 메타데이터)
# ==========================================
def apply_style():
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{ background-color: #000000 !important; }}
        label p {{ color: #FFFFFF !important; font-weight: 500 !important; }}
        .main-header {{ padding: 1.5rem 0; text-align: center; }}
        .main-title {{ font-size: 1.8rem; font-weight: 800; color: #00FF88 !important; }}
        .stTextInput input {{ background-color: #FFFFFF !important; color: #000000 !important; border-radius: 8px; }}
        .stButton>button {{ width: 100%; border-radius: 8px; height: 3rem; font-weight: 700; }}
        /* 첫 번째 버튼(판독)은 연두색, 두 번째 버튼(리셋)은 투명 테두리 */
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button {{ background-color: #00FF88 !important; color: #000 !important; border: none; }}
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button {{ background-color: transparent !important; color: #FF4B4B !important; border: 1px solid #FF4B4B !important; }}
        .section-card {{ background: #111111; border: 1px solid #333; border-radius: 12px; padding: 18px; margin-bottom: 12px; }}
        .price-item {{ margin-bottom: 12px; border-bottom: 1px solid #222; padding-bottom: 10px; }}
        .price-tag {{ color: #00FF88 !important; font-size: 1.5rem; font-weight: 800; float: right; }}
        .footer-link {{ background: #1A1A1A; color: #00FF88 !important; padding: 14px; border-radius: 10px; text-align: center; text-decoration: none; display: block; font-weight: 700; border: 1px solid #333; margin-top: 20px; }}
        .version-tag-footer {{ text-align: center; color: #444; font-size: 0.7rem; margin-top: 40px; border-top: 1px solid #222; padding-top: 10px; }}
        </style>
        <head>
            <meta name="apple-mobile-web-app-title" content="지름 판독기">
            <link rel="apple-touch-icon" href="{ICON_URL}">
        </head>
    """, unsafe_allow_html=True)

def main():
    apply_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'input_name' not in st.session_state: st.session_state.input_name = ""
    if 'input_price' not in st.session_state: st.session_state.input_price = ""

    st.markdown('<div class="main-header"><div class="main-title">⚖️ 지름 판독기</div></div>', unsafe_allow_html=True)

    # 모델명 및 가격 입력창 (리셋 기능과 연동)
    st.session_state.input_name = st.text_input("📦 검색 모델명", value=st.session_state.input_name)
    st.session_state.input_price = st.text_input("💰 나의 가격 (숫자만)", value=st.session_state.input_price)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 판독 엔진 가동"):
            if st.session_state.input_name:
                with st.spinner('데이터 분석 중...'):
                    raw = AdvancedSearchEngine.search_all(st.session_state.input_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, "직구, 해외", st.session_state.input_name)
                    s_type, s_msg, s_review = AdvancedSearchEngine.summarize_sentiment(raw)
                    data = {"name": st.session_state.input_name, "price": st.session_state.input_price, "results": res, "s_msg": s_msg, "s_review": s_review, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    st.session_state.history.insert(0, data)
                    st.rerun()
    with col2:
        # [복구] 리셋 버튼
        if st.button("🔄 리셋"):
            st.session_state.current_data = None
            st.session_state.input_name = ""
            st.session_state.input_price = ""
            st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        st.write("---")
        if not d['results']:
            st.error("뽐뿌게시판에서 유효한 데이터를 찾지 못했습니다.")
        else:
            final_msg = d['s_msg']
            if d['price'].isdigit():
                all_p = [item['price'] for sublist in d['results'].values() for item in sublist]
                best_p = min(all_p)
                diff = int(d['price']) - best_p
                if diff <= 0: final_msg = "🔥 역대급 가격입니다! 즉시 구매를 추천합니다."
                else: final_msg = f"❌ 현재 최저가보다 {diff:,}원 더 비쌉니다."

            st.markdown(f'<div class="section-card"><span style="color:#888; font-size:0.8rem;">판단결과</span><br><div class="content-text" style="color:#FFF; font-weight:600;">{final_msg}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="section-card"><span style="color:#888; font-size:0.8rem;">만족도 요약</span><br><div class="content-text" style="color:#FFF; font-weight:600;">{d["s_review"]}</div></div>', unsafe_allow_html=True)
            
            for spec, items in sorted(d['results'].items(), reverse=True):
                best = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'<div class="price-item"><span class="price-tag">{best["price"]:,}원</span><b style="color:#00FF88;">[{spec}]</b> <span style="color:#CCC;">{best["title"]}</span></div>', unsafe_allow_html=True)

        q_url = urllib.parse.quote(d['name'])
        # [해결] 뽐뿌게시판 카테고리 8 고정 링크
        fixed_link = f"https://m.ppomppu.co.kr/new/search_result.php?category=8&search_type=sub_memo&keyword={q_url}"
        st.markdown(f'<a href="{fixed_link}" target="_blank" class="footer-link">🔗 뽐뿌게시판 실시간 원문 보기</a>', unsafe_allow_html=True)

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력")
        for h in st.session_state.history[:3]:
            if st.button(f"[{h['time']}] {h['name']}", key=f"h_{h['time']}_{h['name']}"):
                st.session_state.current_data = h
                st.session_state.input_name = h['name']
                st.session_state.input_price = h['price']
                st.rerun()

    # [복구] 하단 버전명 표시
    st.markdown('<div class="version-tag-footer">⚖️ 지름 판독기 PRO v8.3.5</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()