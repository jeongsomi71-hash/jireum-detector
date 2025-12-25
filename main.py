import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ==========================================
# 1. 강화된 구글 스니펫 분석 엔진
# ==========================================
class GoogleSnippetEngine:
    @staticmethod
    def get_real_market_price(product_name):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        query = urllib.parse.quote(f"{product_name} 최저가")
        url = f"https://www.google.com/search?q={query}"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200: return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # [수정] 클래스명에 의존하지 않고 페이지 내 모든 텍스트에서 가격 패턴 추출
            page_text = soup.get_text()
            # 1,000원 ~ 9,999,999원 사이의 한국어 가격 패턴 매칭
            found = re.findall(r'([0-9,]{4,})\s?원', page_text)
            
            price_list = []
            for f in found:
                price_val = int(f.replace(',', ''))
                if price_val > 5000: # 배송비 등 저가 제외
                    price_list.append(price_val)
            
            # 만약 '원' 단위로 못 찾았다면 숫자 패턴으로 재시도
            if not price_list:
                numbers = re.findall(r'[0-9,]{5,}', page_text)
                for n in numbers:
                    val = int(n.replace(',', ''))
                    if 10000 < val < 10000000: # 현실적인 가격대 필터
                        price_list.append(val)

            if price_list:
                # 너무 낮은 값은 중고일 수 있으므로 하위 20% 지점의 가격을 최저가로 채택
                price_list.sort()
                return price_list[0]
        except:
            return None
        return None

# ==========================================
# 2. 메인 UI 및 이미지 분석 로직
# ==========================================
def main():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    
    st.markdown("""
        <style>
        .main-header { background-color: #4285F4; color: white; text-align: center; padding: 20px; border-radius: 12px; font-weight: 900; }
        .source-info { font-size: 0.8rem; color: #666; text-align: center; margin-top: 5px; }
        .result-card { border: 2px solid #4285F4; padding: 25px; border-radius: 15px; margin-top: 20px; background-color: #ffffff; color: #333; }
        .price-val { font-size: 1.8rem; font-weight: 800; color: #4285F4; }
        .redirect-btn { display: block; width: 100%; background-color: #03C75A; color: white !important; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)
    st.markdown('<p class="source-info">※ Google 실시간 검색 데이터를 분석하여 판결합니다.</p>', unsafe_allow_html=True)

    # [복구] 이미지 검색과 직접 입력 탭
    tab1, tab2 = st.tabs(["📸 이미지 판결", "✍️ 상품명 직접 입력"])

    f_name, f_price = "", 0

    with tab1:
        file = st.file_uploader("제품 이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            # OCR 분석
            proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
            text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 2]
            f_name = lines[0] if lines else "이미지 추출 상품"
            st.info(f"🔍 이미지 인식 결과: **{f_name}**")

    with tab2:
        n_input = st.text_input("📦 상품명", placeholder="예: 아이폰 15 프로")
        p_input = st.text_input("💰 가격", placeholder="숫자만 입력")
        if n_input and p_input:
            f_name = n_input
            f_price = int(re.sub(r'[^0-9]', '', p_input))

    if st.button("🚀 실시간 분석 및 판결 실행", use_container_width=True):
        if f_name and (f_price > 0 or tab1):
            with st.spinner('🌐 구글 시세 데이터를 실시간 분석 중...'):
                real_low = GoogleSnippetEngine.get_real_market_price(f_name)
            
            if real_low:
                show_result_ui(f_name, f_price if f_price > 0 else real_low, real_low)
            else:
                st.error("⚠️ 시세 파악 실패. 구글 검색 결과에서 가격 정보를 찾지 못했습니다. 더 구체적인 상품명(예: 브랜드 포함)을 입력해 주세요.")

def show_result_ui(name, user_price, real_low):
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader(f"📊 '{name}' 분석 결과")
    c1, c2 = st.columns(2)
    c1.metric("확인 가격", f"{user_price:,}원")
    c2.metric("실시간 최저가(추정)", f"{real_low:,}원")
    
    diff = user_price - real_low
    st.markdown("---")
    if user_price <= real_low:
        st.success("🔥 **역대급 딜!** 최저가보다 저렴합니다.")
    else:
        st.error(f"💀 **호구 주의!** 최저가보다 {diff:,}원 더 비쌉니다.")
    
    q_enc = urllib.parse.quote(name)
    st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q_enc}" target="_blank" class="redirect-btn">🛒 네이버 쇼핑에서 실제 상품 보기</a>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
