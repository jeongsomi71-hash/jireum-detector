import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime

# ==========================================
# 1. 정밀 분류 및 시세 분석 엔진 (v1.5 기능 유지)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        links = {
            "뽐뿌(통합)": f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=1",
            "클리앙(전체)": f"https://www.clien.net/service/search?q={encoded_query}"
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
    def categorize_deals(titles):
        exclude_pattern = re.compile(r'중고|사용감|리퍼|S급|민팃|삽니다|매입')
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
            model = "일반/기본"
            if any(k in t_low for k in ["울트라", "ultra", "p10", "버지"]): model = "상급/Ultra"
            elif any(k in t_low for k in ["플러스", "plus", "d8", "링크"]): model = "중급/Plus"

            storage = ""
            if "256" in t_low: storage = " 256G"
            elif "512" in t_low: storage = " 512G"
            elif "1tb" in t_low or "1티라" in t_low: storage = " 1TB"

            opt = ""
            if "자급제" in t_low: opt = " (자급제)"
            elif any(k in t_low for k in ["현완", "번이", "기변", "성지"]): opt = " (성지)"

            key = f"{model}{storage}{opt}".strip()
            if key not in categorized: categorized[key] = []
            categorized[key].append(num)
        
        return {k: sorted(list(set(v))) for k, v in categorized.items()}

# ==========================================
# 2. UI 및 고대비 스타일링 (v1.6 최적화)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v1.6", layout="centered")
    st.markdown("""
        <style>
        .block-container { max-width: 550px !important; padding-top: 1rem !important; }
        html, body, [class*="css"] { background-color: #000000 !important; color: #FFFFFF !important; }
        
        /* [수정] 헤더 높이 축소 및 상단 잘림 방지 */
        .unified-header { 
            background-color: #FFFFFF; 
            color: #000000 !important; 
            text-align: center; 
            font-size: 1.5rem; 
            font-weight: 900; 
            padding: 12px; 
            border-radius: 10px; 
            margin-bottom: 5px; 
            border: 3px solid #00FF88;
            line-height: 1.2;
        }
        .version-tag { font-size: 0.7rem; color: #444; margin-left: 5px; font-weight: bold; }
        
        /* [수정] 고대비 카드 디자인 */
        .detail-card { 
            border: 2px solid #00FF88; 
            padding: 18px; 
            border-radius: 12px; 
            margin-top: 12px; 
            background-color: #111111; /* 배경 대비 강화 */
            box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        }
        
        /* [수정] 최저가 가독성 극대화 */
        .price-highlight { 
            color: #00FF88 !important; 
            font-size: 1.9rem !important; 
            font-weight: 900 !important; 
            float: right; 
            text-shadow: 1px 1px 2px #000;
        }
        
        /* [수정] 흰색 텍스트 링크 버튼 */
        .link-btn-box { 
            background:#222222; 
            color:#FFFFFF !important; 
            padding:12px; 
            border-radius:8px; 
            text-align:center; 
            font-size:0.85rem; 
            border: 1px solid #FFFFFF; /* 흰색 테두리로 가독성 보완 */
            font-weight: bold;
        }
        
        .history-item { border-left: 4px solid #00FF88; padding: 10px 15px; margin-bottom: 8px; background: #151515; font-size: 0.9rem; border-radius: 0 8px 8px 0; color: #EEEEEE; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; height: 3.2rem; font-size: 1rem; }
        
        /* 입력창 라벨 가독성 */
        label { color: #FFFFFF !important; font-weight: bold !important; font-size: 1rem !important; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 'history' not in st.session_state: st.session_state.history = []

    # 상단 헤더 (높이 축소 반영)
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span class="version-tag">v1.6</span></div>', unsafe_allow_html=True)

    with st.form(key='search_form', clear_on_submit=False):
        f_name = st.text_input("📦 제품명 입력", placeholder="예: 갤럭시 S24, 턴 버지 P10")
        p_val = st.text_input("💰 나의 확인가 (숫자만)", placeholder="예: 950000")
        cols = st.columns(2)
        submit_button = cols[0].form_submit_button(label='🔍 시세 판독 실행')
        reset_button = cols[1].form_submit_button(label='🔄 리셋')

    if reset_button: st.rerun()

    if submit_button and f_name:
        with st.spinner('🏘️ 옵션별 최저가 데이터를 정밀 분석 중...'):
            raw_titles = AdvancedSearchEngine.search_all(f_name)
            cat_data = AdvancedSearchEngine.categorize_deals(raw_titles)

            if cat_data:
                # [수정] 요청하신 문구로 변경
                st.markdown("### 📊 옵션별 최저가(추정) 리포트")
                sorted_keys = sorted(cat_data.keys(), key=lambda x: cat_data[x][0])
                
                for key in sorted_keys:
                    prices = cat_data[key]
                    count = len(prices)
                    # 고대비 색상 선정
                    rel_color = "#00FF88" if count >= 5 else ("#FFD700" if count >= 2 else "#FF5555")
                    
                    st.markdown(f'''
                    <div class="detail-card">
                        <span style="color:{rel_color}; font-size:0.85rem; font-weight:bold;">● 데이터 {count}건</span><br>
                        <span style="font-weight:bold; font-size:1.15rem; color:#FFFFFF;">{key}</span>
                        <span class="price-highlight">{prices[0]:,}원</span>
                    </div>
                    ''', unsafe_allow_html=True)

                best_price = min([p[0] for p in cat_data.values()])
                now = datetime.now().strftime("%H:%M:%S")
                st.session_state.history.insert(0, f"[{now}] {f_name} → {best_price:,}원")
                st.session_state.history = st.session_state.history[:10]

                st.write("\n🔗 **실시간 근거 데이터 확인**")
                links = {"뽐뿌(통합)": f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={urllib.parse.quote(f_name)}&category=1",
                         "클리앙(전체)": f"https://www.clien.net/service/search?q={urllib.parse.quote(f_name)}"}
                l_cols = st.columns(len(links))
                for i, (site, url) in enumerate(links.items()):
                    l_cols[i].markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div class="link-btn-box">{site}</div></a>', unsafe_allow_html=True)
                
                st.markdown('<div style="color:#FF5555; font-size:0.85rem; margin-top:30px; text-align:center; font-weight:bold;">⚠️ 최근 1년 내 낮은 가격들의 평균가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
            else: st.warning("⚠️ 데이터를 찾지 못했습니다. 키워드를 더 단순하게 시도해 보세요.")

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 조회 이력 (Top 10)")
        for item in st.session_state.history:
            st.markdown(f'<div class="history-item">{item}</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()

# Version: v1.6 - Header Height Fix, Enhanced Contrast & Custom Labels