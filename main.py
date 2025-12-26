import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# ==========================================
# 1. 용량/옵션/모델 정밀 분석 엔진
# ==========================================
class DeepAnalysisEngine:
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
                res = requests.get(url, headers=DeepAnalysisEngine.get_mobile_headers(), timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                if name == "ppomppu": titles = [t.get_text(strip=True) for t in soup.select('.title')]
                elif name == "ruliweb": titles = [t.get_text(strip=True) for t in soup.select('.subject_inner_text, .subject')]
                elif name == "clien": titles = [t.get_text(strip=True) for t in soup.select('.list_subject .subject_fixed')]
                all_titles.extend(titles)
            except: continue
        return all_titles

    @staticmethod
    def categorize_deal(titles):
        exclude_pattern = re.compile(r'중고|민팃|리퍼|S급|A급|B급|사용감|매입|삽니다')
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        # 정밀 분류 딕셔너리
        categorized_results = {}

        for text in titles:
            if exclude_pattern.search(text): continue
            found = price_pattern.findall(text)
            if not found: continue
            
            f_val, unit = found[0]
            num = int(f_val.replace(',', ''))
            if unit == '만': num *= 10000
            if num < 5000: continue 

            # 키워드 추출 (모델 + 용량 + 옵션)
            t_lower = text.lower()
            
            # 1. 모델 판별
            model = "일반"
            if "울트라" in t_lower or "ultra" in t_lower: model = "울트라"
            elif "플러스" in t_lower or "plus" in t_lower or "+" in t_lower: model = "플러스"
            
            # 2. 용량 판별
            storage = "기타/미지정"
            if "128" in t_lower: storage = "128GB"
            elif "256" in t_lower: storage = "256GB"
            elif "512" in t_lower: storage = "512GB"
            elif "1tb" in t_lower or "1티라" in t_lower: storage = "1TB"
            
            # 3. 옵션 판별 (자급제 vs 성지)
            opt = ""
            if "자급제" in t_lower: opt = "(자급제)"
            elif any(k in t_lower for k in ["현완", "번이", "기변", "성지"]): opt = "(성지/통신사)"

            # 최종 키 생성
            category_key = f"{model} {storage} {opt}".strip()
            
            if category_key not in categorized_results:
                categorized_results[category_key] = []
            categorized_results[category_key].append(num)

        # 중복 제거 및 정렬
        final_data = {}
        for key, prices in categorized_results.items():
            final_data[key] = sorted(list(set(prices)))
        return final_data

# ==========================================
# 2. UI 및 고대비 스타일
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
        .tag-history { color: #888; font-size: 0.8rem; margin-top: 8px; border-top: 1px solid #333; padding-top: 5px; }
        .warning-footer { color: #FF4B4B; font-size: 0.8rem; text-align: center; margin-top: 30px; font-style: italic; }
        .stButton>button { width: 100%; border: 2px solid #00FF88; background-color: #000; color: #00FF88; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)

    col_t, col_r = st.columns([4, 1])
    with col_r:
        if st.button("🔄 리셋"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

    f_name = st.text_input("📦 분석할 제품 시리즈", placeholder="예: 갤럭시 S24, 아이폰 15")
    p_val = st.text_input("💰 나의 확인가 (선택)", placeholder="숫자만 입력")

    if st.button("🔍 용량/옵션별 정밀 시세 분석"):
        if not f_name:
            st.error("❗ 상품명을 입력해주세요.")
        else:
            with st.spinner('🏘️ 3대 커뮤니티 2개년 데이터를 용량별로 분류 중...'):
                raw_titles = DeepAnalysisEngine.search_all_sites(f_name)
                categorized_data = DeepAnalysisEngine.categorize_deal(raw_titles)

            if categorized_data:
                st.write("### 📊 정밀 분류 시세 리포트")
                # 최저가 순으로 정렬하여 표시
                sorted_keys = sorted(categorized_data.keys(), key=lambda x: categorized_data[x][0])
                
                for key in sorted_keys:
                    prices = categorized_data[key]
                    st.markdown(f'''
                    <div class="detail-card">
                        <span class="tag-model">▣ {key}</span>
                        <span class="tag-price">{prices[0]:,}원</span>
                        <div class="tag-history">탐지된 기록: {", ".join([f"{p:,}" for p in prices[1:4]])}원...</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                st.markdown('<div class="warning-footer">⚠️ 최근 1년 내 최저가로 추정되지만 부정확할 수 있어요.</div>', unsafe_allow_html=True)
                
                if p_val:
                    f_price = int(re.sub(r'[^0-9]', '', p_val))
                    min_overall = min([p[0] for p in categorized_data.values()])
                    if f_price <= min_overall:
                        st.success(f"🔥 **역대급 확인**: 입력하신 {f_price:,}원은 전체 옵션 중 최저가보다 저렴합니다!")
            else:
                st.warning("⚠️ 유의미한 데이터를 찾지 못했습니다. 상품명을 단순하게 입력해보세요.")

if __name__ == "__main__":
    main()
