import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime

# ==========================================
# 1. 시세 분석 및 추천 리뷰 검색 엔진
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
    def categorize_deals(titles, search_query, user_excludes):
        # 기본 제외어 + 사용자 입력 제외어 (OR 처리)
        base_excludes = ["중고", "사용감", "리퍼", "S급", "민팃", "삽니다", "매입"]
        custom_excludes = [x.strip() for x in user_excludes.split(',') if x.strip()]
        total_excludes = base_excludes + custom_excludes
        
        exclude_pattern = re.compile('|'.join(map(re.escape, total_excludes)))
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        categorized = {}
        
        search_query_low = search_query.lower()

        for text in titles:
            if exclude_pattern.search(text): continue
            found = price_pattern.findall(text)
            if not found: continue
            
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            if num < 10000: continue
            
            t_low = text.lower()
            model_tag = "일반/기본"
            
            if any(k in search_query_low for k in ["s24", "아이폰", "갤럭시", "버지", "p10"]):
                if any(k in t_low for k in ["울트라", "ultra", "p10", "버지"]): model_tag = "상급/Ultra"
                elif any(k in t_low for k in ["플러스", "plus", "d8", "링크"]): model_tag = "중급/Plus"
            
            specs = ""
            if "256" in t_low: specs = " 256G"
            elif "512" in t_low: specs = " 512G"
            elif "10인용" in t_low: specs = " 10인용"
            elif "6인용" in t_low: specs = " 6인용"

            opt = ""
            if "자급제" in t_low: opt = " (자급제)"
            elif any(k in t_low for k in ["현완", "성지"]): opt = " (특가/성지)"

            key = f"{model_tag}{specs}{opt}".strip()
            if key not in categorized: categorized[key] = []
            categorized[key].append(num)
            
        return {k: sorted(list(set(v))) for k, v in categorized.items()}

# ==========================================
# 2. UI 스타일링 (v2.0 유지 및 확장)
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v2.0", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .main .block-container { max-width: 550px !important; padding-top: 5rem !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .version-tag { font-size: 0.8rem; color: #444444 !important; font-weight: bold; margin-left: 5px; }
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; color: #FFFFFF !important; }
        .price-highlight { color: #00FF88 !important; font-size: 2rem !important; font-weight: 900 !important; float: right; text-shadow: 1px 1px 2px #000; }
        .link-btn-box { background-color: #333333 !important; color: #FFFFFF !important; padding: 12px; border-radius: 8px; text-align: center; font-size: 0.9rem; border: 1px solid #FFFFFF !important; font-weight: bold; display: block; margin-bottom: 5px; }
        .review-btn-box { background-color: #004d40 !important; color: #00FF88 !important; padding: 12px; border-radius: 8px; text-align: center; font-size: 0.9rem; border: 1px solid #00FF88 !important; font-weight: bold; display: block; }
        .history-item { border-left: 4px solid #00FF88 !important; padding: 12px; margin-bottom: 10px; background-color: #111111 !important; font-size: 0.9rem; border-radius: 0 8px 8px 0; color: #DDDDDD !important; }
        label p { color: #FFFFFF !important; font-weight: bold !important; font-size: 1.1rem !important; }
        h3 { color: #00FF88 !important; margin-top: 20px; }
        .stButton>button { width: 100%; border: 2px solid #00FF88 !important; background-color: #000000 !important; color: #00FF88 !important; font-weight: bold !important; height: 3.5rem; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 'history' not in st.session_state: st.session_state.history = []

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span class="version-tag">v2.0</span></div>', unsafe_allow_html=True)

    with st.form(key='search_form'):
        f_name = st.text_input("📦 제품명", placeholder="예: 쿠쿠 6인용 밥솥, 갤럭시 S24")
        p_val = st.text_input("💰 나의 확인가", placeholder="숫자만 입력")
        # [추가] 제외 단어 입력 (OR 처리용)
        f_exclude = st.text_input("🚫 제외할 단어 (쉼표로 구분)", placeholder="예: 직구, 해외, 렌탈, 당근")
        
        cols = st.columns(2)
        submit_button = cols[0].form_submit_button(label='🔍 시세 판독 실행')
        reset_button = cols[1].form_submit_button(label='🔄 리셋')

    if reset_button: st.rerun()

    if submit_button and f_name:
        with st.spinner('🏘️ 필터링된 데이터를 정밀 분석 중...'):
            raw_titles = AdvancedSearchEngine.search_all(f_name)
            cat_data = AdvancedSearchEngine.categorize_deals(raw_titles, f_name, f_exclude)

            if cat_data:
                st.markdown("### 📊 옵션별 최저가(추정) 리포트")
                sorted_keys = sorted(cat_data.keys(), key=lambda x: cat_data[x][0])
                
                for key in sorted_keys:
                    prices = cat_data[key]
                    count = len(prices)
                    rel_color = "#00FF88" if count >= 5 else ("#FFD700" if count >= 2 else "#FF5555")
                    st.markdown(f'''
                    <div class="detail-card">
                        <span style="color:{rel_color}; font-size:0.9rem; font-weight:bold;">● 데이터 {count}건</span><br>
                        <span style="font-weight:bold; font-size:1.2rem; color:#FFFFFF;">{key}</span>
                        <span class="price-highlight">{prices[0]:,}원</span>
                    </div>
                    ''', unsafe_allow_html=True)

                # 시세 근거 데이터 링크
                st.write("")
                st.markdown("### 🔗 실시간 시세 근거")
                e_query = urllib.parse.quote(f_name)
                l_cols = st.columns(2)
                l_cols[0].markdown(f'<a href="https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={e_query}&category=1" target="_blank" style="text-decoration:none;"><div class="link-btn-box">뽐뿌 실시간 검색</div></a>', unsafe_allow_html=True)
                l_cols[1].markdown(f'<a href="https://www.clien.net/service/search?q={e_query}" target="_blank" style="text-decoration:none;"><div class="link-btn-box">클리앙 실시간 검색</div></a>', unsafe_allow_html=True)

                # [추가] 추천 리뷰/후기 링크 섹션
                st.markdown("### ⭐ 추천 리뷰 및 실사용 후기")
                st.info("커뮤니티 내 추천수가 높은 베스트 게시글 위주로 연결됩니다.")
                r_cols = st.columns(2)
                # 뽐뿌 팁게/사용기 전용 검색
                r_cols[0].markdown(f'<a href="https://www.ppomppu.co.kr/zboard/zboard.php?id=free_picture&category=2&sn1=&divpage=32&sn=off&ss=on&sc=off&keyword={e_query}" target="_blank" style="text-decoration:none;"><div class="review-btn-box">뽐뿌 추천 사용기</div></a>', unsafe_allow_html=True)
                # 클리앙 사용기 전용 검색
                r_cols[1].markdown(f'<a href="https://www.clien.net/service/search/board/use?sk=title&sv={e_query}" target="_blank" style="text-decoration:none;"><div class="review-btn-box">클리앙 베스트 리뷰</div></a>', unsafe_allow_html=True)
                
                st.markdown('<div style="color:#FF5555; font-size:0.9rem; margin-top:30px; text-align:center; font-weight:bold;">⚠️ 최근 1년 내 낮은 가격들의 평균가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
            else: st.warning("⚠️ 필터링 후 남은 데이터가 없습니다. 제외 단어를 줄여보세요.")

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 조회 이력 (Top 10)")
        for item in st.session_state.history:
            st.markdown(f'<div class="history-item">{item}</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()

# Version: v2.0 - Custom Exclude Filter & Best Review Links