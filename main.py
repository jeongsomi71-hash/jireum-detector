import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# ==========================================
# 1. 3대 커뮤니티 통합 및 멀티 모델 분석 엔진
# ==========================================
class MultiModelEngine:
    @staticmethod
    def get_mobile_headers():
        return {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Referer": "https://m.ppomppu.co.kr/"
        }

    @staticmethod
    def search_all_sites(product_name):
        sites = {
            "ppomppu": f"https://m.ppomppu.co.kr/new/bbs_list.php?id=ppomppu&search_type=sub_memo&keyword={urllib.parse.quote(product_name)}",
            "ruliweb": f"https://m.bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={urllib.parse.quote(product_name)}",
            "clien": f"https://www.clien.net/service/search/board/jirum?sk=title&sv={urllib.parse.quote(product_name)}"
        }
        
        all_titles = []
        for name, url in sites.items():
            try:
                res = requests.get(url, headers=MultiModelEngine.get_mobile_headers(), timeout=7)
                soup = BeautifulSoup(res.text, 'html.parser')
                if name == "ppomppu": titles = [t.get_text(strip=True) for t in soup.select('.title')]
                elif name == "ruliweb": titles = [t.get_text(strip=True) for t in soup.select('.subject_inner_text, .subject')]
                elif name == "clien": titles = [t.get_text(strip=True) for t in soup.select('.list_subject .subject_fixed')]
                all_titles.extend(titles)
            except: continue
        return all_titles

    @staticmethod
    def analyze_by_models(titles):
        """모델명 키워드별로 분류하여 최저가 추출"""
        # 중고 키워드 제외
        exclude_pattern = re.compile(r'중고|민팃|리퍼|S급|A급|B급|사용감')
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        # 모델 그룹 정의
        groups = {
            "Ultra / 울트라": [],
            "Plus / 플러스": [],
            "기본 / 일반": []
        }
        
        for text in titles:
            if exclude_pattern.search(text): continue
            
            # 가격 추출
            found = price_pattern.findall(text)
            if not found: continue
            
            # 수치 변환
            f_val, unit = found[0]
            num = int(f_val.replace(',', ''))
            if unit == '만': num *= 10000
            if num < 1000: continue # 너무 낮은 노이즈 제거
            
            # 모델 분류
            lower_text = text.lower()
            if "울트라" in lower_text or "ultra" in lower_text:
                groups["Ultra / 울트라"].append(num)
            elif "플러스" in lower_text or "plus" in lower_text or "+" in lower_text:
                groups["Plus / 플러스"].append(num)
            else:
                groups["기본 / 일반"].append(num)
                
        # 중복 제거 및 정렬
        result = {}
        for model, prices in groups.items():
            if prices:
                result[model] = sorted(list(set(prices))) # 중복 제거 후 오름차순 정렬
        return result

# ==========================================
# 2. UI 및 레이아웃
# ==========================================
def apply_custom_style():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
        .block-container { max-width: 500px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .model-card { border: 1px solid #00FF88; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #111; }
        .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #00FF88; background-color: #000; color: #00FF88; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)

    # 우측 상단 리셋 버튼
    col_t, col_r = st.columns([4, 1])
    with col_r:
        if st.button("🔄 리셋"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

    f_name = st.text_input("📦 시리즈명 입력", placeholder="예: 갤럭시 S24, 아이폰 15")
    p_val = st.text_input("💰 나의 확인가 (선택)", placeholder="숫자만 입력")

    if st.button("⚖️ 모델별 통합 시세 판독"):
        if not f_name:
            st.error("❗ 상품명을 입력해주세요.")
        else:
            with st.spinner('🏘️ 3대 커뮤니티에서 모델별 데이터를 정밀 분석 중...'):
                raw_titles = MultiModelEngine.search_all_sites(f_name)
                model_results = MultiModelEngine.analyze_by_models(raw_titles)

            if model_results:
                st.write("### 📊 모델별 역대 최저가 리스트")
                for model, prices in model_results.items():
                    with st.container():
                        st.markdown(f'''
                        <div class="model-card">
                            <span style="color:#00FF88; font-weight:900;">[{model}]</span><br>
                            최저가: <span style="font-size:1.2rem;">{prices[0]:,}원</span><br>
                            <small style="color:#888;">최근 기록된 다른 시세: {", ".join([f"{p:,}" for p in prices[1:3]])}원...</small>
                        </div>
                        ''', unsafe_allow_html=True)
                
                # 입력한 가격이 있을 경우 판결
                if p_val:
                    f_price = int(re.sub(r'[^0-9]', '', p_val))
                    # 가장 유사한 모델의 최저가와 비교 (기본적으로 가장 낮은 가격과 비교)
                    min_overall = min([p[0] for p in model_results.values()])
                    if f_price <= min_overall:
                        st.success(f"🔥 **판결**: 어떤 모델 기준이든 역대급 최저가입니다!")
                    else:
                        st.warning(f"ℹ️ 확인하신 {f_price:,}원은 위 리스트의 최저가들과 비교해 보세요.")
            else:
                st.warning("⚠️ 해당 시리즈의 유의미한 정보를 찾지 못했습니다.")

if __name__ == "__main__":
    main()
