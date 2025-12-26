import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time

# ==========================================
# 1. 시세 분석 엔진 (자전거 검색 최적화)
# ==========================================
class DeepAnalysisEngine:
    @staticmethod
    def get_mobile_headers():
        return {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }

    @staticmethod
    def search_all_sites(product_name):
        # 자전거는 브랜드명과 모델명이 혼용되므로 검색어를 쪼개서 시도
        keywords = product_name.replace(',', ' ').split()
        search_query = "+".join(keywords)
        
        sites = {
            "ppomppu": f"https://m.ppomppu.co.kr/new/bbs_list.php?id=ppomppu&search_type=sub_memo&keyword={search_query}",
            "ruliweb": f"https://m.bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={search_query}",
            "clien": f"https://www.clien.net/service/search/board/jirum?sk=title&sv={search_query}"
        }
        
        all_titles = []
        for name, url in sites.items():
            try:
                res = requests.get(url, headers=DeepAnalysisEngine.get_mobile_headers(), timeout=10)
                # 자전거는 데이터가 적을 수 있어 딜레이를 주어 안정적으로 가져옴
                time.sleep(0.5)
                soup = BeautifulSoup(res.text, 'html.parser')
                if name == "ppomppu": titles = [t.get_text(strip=True) for t in soup.select('.title')]
                elif name == "ruliweb": titles = [t.get_text(strip=True) for t in soup.select('.subject_inner_text, .subject')]
                elif name == "clien": titles = [t.get_text(strip=True) for t in soup.select('.list_subject .subject_fixed')]
                all_titles.extend(titles)
            except: continue
        return all_titles

    @staticmethod
    def categorize_deal(titles):
        # 자전거는 '중고' 검색어가 매우 많으므로 필터링 필수
        exclude_pattern = re.compile(r'중고|사용감|S급|A급|B급|매입|삽니다|민팃|리퍼')
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        categorized_results = {}

        for text in titles:
            if exclude_pattern.search(text): continue
            found = price_pattern.findall(text)
            if not found: continue
            
            f_val, unit = found[0]
            num = int(f_val.replace(',', ''))
            if unit == '만': num *= 10000
            if num < 10000: continue # 너무 낮은 가격(소모품 등) 제외

            t_lower = text.lower()
            # 미니벨로 등 모델 특징 분류 (자전거용으로 커스텀)
            model = "일반/모델미상"
            if any(k in t_lower for k in ["울트라", "p10", "d9", "버지", "verge"]): model = "상급/버지급"
            elif any(k in t_lower for k in ["플러스", "d8", "링크", "link"]): model = "중급/링크급"
            
            # 자전거 옵션 (연식이나 용량 대신 단수/자급제 등)
            opt = ""
            if "자급제" in t_lower or "신품" in t_lower: opt = "(신품)"
            elif "성지" in t_lower or "현완" in t_lower: opt = "(특가)"

            category_key = f"{model} {opt}".strip()
            if category_key not in categorized_results: categorized_results[category_key] = []
            categorized_results[category_key].append(num)

        return {k: sorted(list(set(v))) for k, v in categorized_results.items()}

# ==========================================
# 2. UI 스타일 및 물리적 리셋 로직
# ==========================================
def apply_custom_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
        .block-container { max-width: 550px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .detail-card { border: 2px solid #00FF88; padding: 15px; border-radius: 12px; margin-bottom: 12px; background-color: #0A0A0A; }
        .tag-model { color: #00FF88; font-weight: 900; font-size: 1rem; }
        .tag-price { color: #FFFFFF; font-size: 1.3rem; font-weight: 700; float: right; }
        .warning-footer { color: #FF4B4B; font-size: 0.8rem; text-align: center; margin-top: 30px; font-style: italic; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)

    # [수정] 리셋 버튼 클릭 시 세션 키를 변경하여 입력창을 강제로 비움
    if "reset_key" not in st.session_state:
        st.session_state.reset_key = 0

    col_t, col_r = st.columns([4, 1])
    with col_r:
        if st.button("🔄 리셋"):
            st.session_state.reset_key += 1 # 키 변경으로 위젯 재생성
            st.rerun()

    # [수정] key 파라미터에 reset_key를 포함하여 리셋 시 위젯이 완전히 초기화되도록 함
    f_name = st.text_input("📦 분석할 자전거/제품 시리즈", placeholder="예: 턴 버지 P10, 리카", key=f"input_name_{st.session_state.reset_key}")
    p_val = st.text_input("💰 나의 확인가 (선택)", placeholder="숫자만 입력", key=f"input_price_{st.session_state.reset_key}")

    if st.button("🔍 시세 정밀 분석 실행"):
        if not f_name:
            st.error("❗ 상품명을 입력해주세요.")
        else:
            with st.spinner('🏘️ 3대 커뮤니티에서 자전거/제품 시세를 추적 중...'):
                raw_titles = DeepAnalysisEngine.search_all_sites(f_name)
                categorized_data = DeepAnalysisEngine.categorize_deal(raw_titles)

            if categorized_data:
                st.write("### 📊 정밀 분류 시세 리포트")
                for key, prices in categorized_data.items():
                    st.markdown(f'''
                    <div class="detail-card">
                        <span class="tag-model">▣ {key}</span>
                        <span class="tag-price">{prices[0]:,}원</span>
                        <div style="color:#888; font-size:0.8rem; margin-top:8px;">기타 기록: {", ".join([f"{p:,}" for p in prices[1:3]])}원...</div>
                    </div>
                    ''', unsafe_allow_html=True)
                st.markdown('<div class="warning-footer">⚠️ 최근 1년 내 최저가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 데이터를 찾지 못했습니다. 자전거의 경우 모델명을 영어와 한글로 섞어보세요 (예: Tern, 턴).")

if __name__ == "__main__":
    main()
