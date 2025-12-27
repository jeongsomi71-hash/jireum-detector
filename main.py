
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. CORE ENGINE (v6.9 기능 100% 고정)
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
        # [v6.9] 첫 단어 필수 필터링 로직
        raw_first_word = search_query.strip().split()[0] if search_query else ""
        clean_first_word = re.sub(r'[^a-zA-Z0-9가-힣]', '', raw_first_word).lower()
        
        # [v6.9] 상품권 및 기본 제외 키워드
        gift_keywords = ["상품권", "증정", "페이백", "포인트", "캐시백", "이벤트", "경품"]
        base_excludes = ["중고", "사용감", "리퍼", "S급", "민팃", "삽니다", "매입"]
        total_excludes = base_excludes + [x.strip() for x in user_excludes.split(',') if x.strip()]
        
        exclude_pattern = re.compile('|'.join(map(re.escape, total_excludes)))
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        raw_results = []
        for item in items:
            title = item['title']
            clean_title = re.sub(r'[^a-zA-Z0-9가-힣]', '', title).lower()
            
            # 1. 첫 단어 포함 검사 (v6.9 핵심)
            if clean_first_word and clean_first_word not in clean_title: continue
            # 2. 제외어 검사
            if exclude_pattern.search(title): continue
            
            found = price_pattern.findall(title)
            if not found: continue
            
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            
            # 3. 비정상 저가 제외 (v6.9 로직)
            if num < 5000: continue 
            # 4. 소액 상품권형 게시물 제외
            if any(k in title for k in gift_keywords) and num < 100000: continue
            
            raw_results.append({"price": num, "title": title})

        if not raw_results: return {}

        # [v6.9] IQR 기반 이상치 제거 (정밀 시세 산출)
        prices = [x['price'] for x in raw_results]
        q1, q3 = np.percentile(prices, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        filtered_results = [x for x in raw_results if lower_bound <= x['price'] <= upper_bound]

        # [v6.9] 스펙/옵션 분류 로직
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
        return categorized

    @staticmethod
    def summarize_sentiment(items):
        if not items: return None, "데이터 부족"
        pos_k = ["역대급", "최저가", "좋네요", "가성비", "지름", "추천", "만족"]
        neg_k = ["품절", "종료", "비싸", "아쉽", "비추", "불만"]
        txt = " ".join([i['title'] for i in items])
        p = sum(1 for k in pos_k if k in txt)
        n = sum(1 for k in neg_k if k in txt)
        if p > n: return "pos", "🔥 구매 적기: 여론이 매우 긍정적입니다."
        if n > p: return "neg", "🧊 관망 추천: 최근 종료되거나 평이 좋지 않습니다."
        return "neu", "💬 안정 시세: 특이사항 없는 평이한 수준입니다."

# ==========================================
# 2. UI/UX (v7.0 트렌디 + v7.2 가독성 색상)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v7.5", layout="centered")
    st.markdown("""
        <style>
        /* [v7.2] 블랙 배경 */
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        
        /* [v7.0] 헤더 스타일 */
        .main-header { padding: 1.5rem 0; text-align: center; }
        .main-title { font-size: 2.3rem; font-weight: 900; color: #00FF88 !important; letter-spacing: -1px; }
        .sub-title { color: #888; font-size: 0.8rem; letter-spacing: 2px; text-transform: uppercase; }

        /* [v7.2] 입력창 가독성 극대화 (흰 배경/검정 글자) */
        label p { color: #FFFFFF !important; font-weight: 700 !important; font-size: 1rem !important; }
        .stTextInput input {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #333333 !important;
            border-radius: 12px !important;
            height: 3.2rem !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
        }
        .stTextInput input::placeholder { color: #999999 !important; }

        /* [v7.0] 버튼 디자인 */
        .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; font-weight: 800; font-size: 1.1rem; transition: 0.2s; }
        div[data-testid="stColumn"]:nth-of-type(1) .stButton>button { background: linear-gradient(90deg, #00FF88, #00BD65) !important; color: #000 !important; border: none !important; }
        div[data-testid="stColumn"]:nth-of-type(2) .stButton>button { background-color: transparent !important; color: #FF4B4B !important; border: 2px solid #FF4B4B !important; }
        
        /* [v7.0] 결과 카드 (글래스모피즘) */
        .result-card { 
            background: rgba(255, 255, 255, 0.05); 
            border: 1px solid rgba(0, 255, 136, 0.3); 
            border-radius: 16px; padding: 20px; margin-bottom: 15px; 
        }
        .price-tag { color: #00FF88 !important; font-size: 2.1rem; font-weight: 900; float: right; }
        .item-title { color: #FFFFFF !important; font-size: 1.05rem; font-weight: 400; line-height: 1.5; margin-bottom: 10px; display: block; }
        
        /* 상태 바 */
        .status-box { padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; margin-bottom: 20px; font-size: 1.1rem; border: 1px solid; }
        .pos-box { background: rgba(0, 255, 136, 0.1); color: #00FF88; border-color: #00FF88; }
        .neg-box { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; }
        .neu-box { background: #1A1A1A; color: #FFFFFF; border-color: #333; }
        
        /* 하단 버튼 */
        .footer-link { 
            background: #1A1A1A; color: #00FF88 !important; padding: 16px; border-radius: 12px; 
            text-align: center; text-decoration: none; display: block; font-weight: 800; border: 1px solid #333;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    apply_style()
    
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None
    if 'rk' not in st.session_state: st.session_state.rk = 0 # 리셋 키

    st.markdown('<div class="main-header"><div class="main-title">지름신 판독기 PRO</div><div class="sub-title">Ultimate Edition v7.5</div></div>', unsafe_allow_html=True)

    # 입력 섹션
    rk = st.session_state.rk
    in_name = st.text_input("📦 제품명 입력", key=f"n_{rk}", placeholder="예: 아이폰 15 프로")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        in_price = st.text_input("💰 확인 가격 (숫자만)", key=f"p_{rk}", placeholder="예: 1250000")
    with c_p2:
        in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고", key=f"e_{rk}")

    st.write("")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔍 판독 엔진 가동"):
            if in_name:
                with st.spinner('시세 데이터 정밀 분석 중...'):
                    raw_items = AdvancedSearchEngine.search_all(in_name)
                    categorized = AdvancedSearchEngine.categorize_deals(raw_items, in_exclude, in_name)
                    s_type, s_msg = AdvancedSearchEngine.summarize_sentiment(raw_items)
                    data = {"name": in_name, "user_price": in_price, "results": categorized, "s_type": s_type, "s_msg": s_msg, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    if data not in st.session_state.history: st.session_state.history.insert(0, data)
                    st.rerun()
    with col2:
        if st.button("🔄 리셋"):
            st.session_state.rk += 1
            st.session_state.current_data = None
            st.rerun()

    # 결과 출력 (v6.9 로직 기반)
    if st.session_state.current_data:
        d = st.session_state.current_data
        st.markdown("<hr style='border:0.5px solid #222'>", unsafe_allow_html=True)
        
        if not d['results']:
            # [v6.9] 쉼표 제거 안내 로직
            clean_term = re.sub(r'[^a-zA-Z0-9가-힣]$', '', d['name'].split()[0])
            st.warning(f"⚠️ '{clean_term}'(으)로 유효한 시세를 찾지 못했습니다. 모델명만 간단히 입력해 보세요.")
        else:
            # 상태 표시
            st.markdown(f'<div class="status-box {d["s_type"]}-box">{d["s_msg"]}</div>', unsafe_allow_html=True)

            for spec, items in sorted(d['results'].items(), reverse=True):
                best_item = sorted(items, key=lambda x: x['price'])[0]
                st.markdown(f'''
                    <div class="result-card">
                        <span class="price-tag">{best_item['price']:,}원</span>
                        <span class="item-title"><b>[{spec}]</b> {best_item['title']}</span>
                        <div style="clear:both;"></div>
                    </div>
                ''', unsafe_allow_html=True)
                
                # 차액 분석
                if d['user_price'].isdigit():
                    u_price = int(d['user_price'])
                    diff = u_price - best_item['price']
                    if diff <= 0:
                        st.success("✅ 역대급 가격입니다! 망설이지 말고 지르세요.")
                    else:
                        st.error(f"❌ 최저가 대비 {diff:,}원 더 비쌉니다. 관망을 추천합니다.")

        # 바로가기
        q_url = urllib.parse.quote(d['name'])
        st.markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={q_url}&category=1" target="_blank" class="footer-link">🔗 뽐뿌 실시간 게시글 확인</a>', unsafe_allow_html=True)

    # 히스토리
    if st.session_state.history:
        with st.expander("📜 최근 판독 기록"):
            for h in st.session_state.history[:5]:
                st.write(f"• {h['time']} | {h['name']}")

    st.markdown('<div style="text-align:center; color:#444; font-size:0.7rem; margin-top:60px; font-weight:bold;">PREMIUM ANALYTICS ENGINE v7.5</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()