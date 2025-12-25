import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ==========================================
# 1. 고성능 구글 스니펫 시세 엔진
# ==========================================
class GooglePriceEngine:
    @staticmethod
    def get_realtime_price(product_name):
        """구글 검색 결과에서 실시간 가격 텍스트를 정밀 추출"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 검색 쿼리 최적화
        query = urllib.parse.quote(f"{product_name} 최저가")
        url = f"https://www.google.com/search?q={query}"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200: return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # 클래스에 구애받지 않고 모든 텍스트 본문 추출
            content = soup.get_text(separator=' ')
            
            # 패턴 1: 숫자 + 원 (예: 1,230,000원)
            # 패턴 2: ₩ + 숫자 (예: ₩1,230,000)
            patterns = [
                r'([0-9,]{4,})\s?원',
                r'₩\s?([0-9,]{4,})'
            ]
            
            price_list = []
            for p in patterns:
                found = re.findall(p, content)
                for f in found:
                    val = int(f.replace(',', ''))
                    if val > 1000: # 의미 없는 소액 제외
                        price_list.append(val)
            
            if price_list:
                # 추출된 시세 중 가장 합리적인 하위 가격을 최저가로 채택
                price_list.sort()
                return price_list[0]
        except:
            return None
        return None

# ==========================================
# 2. UI 스타일 및 세션 관리
# ==========================================
def apply_custom_style():
    st.set_page_config(page_title="지름신 판독기", layout="centered")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
        .block-container { max-width: 500px !important; padding-top: 1.5rem !important; }
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
        .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 900; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .result-box { border: 2px solid #00FF88; padding: 25px; border-radius: 15px; margin-top: 20px; background-color: #0A0A0A; }
        .naver-btn { display: block; width: 100%; background-color: #03C75A; color: white !important; text-align: center; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 1.2rem; margin: 15px 0; }
        .stat-label { color: #888; font-size: 0.9rem; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #00FF88; }
        .source-tag { font-size: 0.75rem; color: #888; text-align: center; display: block; margin-top: -15px; margin-bottom: 20px; }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# 3. 메인 인터페이스
# ==========================================
def main():
    apply_custom_style()
    
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    st.markdown('<p class="source-info" style="text-align:center; color:#888; font-size:0.8rem; margin-top:-20px; margin-bottom:20px;">Google 실시간 검색 데이터 분석 기반</p>', unsafe_allow_html=True)

    # 이전의 라디오 버튼 메뉴 UX 유지
    tabs = ["📸 이미지 판결", "✍️ 직접 상품명 입력"]
    sel_tab = st.radio("📥 판독 방식", tabs, horizontal=True)

    f_name, f_price = "", 0

    if sel_tab == "📸 이미지 판결":
        file = st.file_uploader("제품 이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            # OCR 분석 수행
            proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
            text_raw = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            lines = [l.strip() for l in text_raw.split('\n') if len(l.strip()) > 2]
            f_name = lines[0] if lines else "이미지 추출 상품"
            st.info(f"🔍 이미지 인식 결과: **{f_name}**")

    elif sel_tab == "✍️ 직접 상품명 입력":
        n_val = st.text_input("📦 상품명", placeholder="정확한 상품명을 입력하세요")
        p_val = st.text_input("💰 현재 확인 가격", placeholder="숫자만 입력")
        if n_val and p_val:
            f_name = n_val
            f_price = int(re.sub(r'[^0-9]', '', p_val))

    if st.button("⚖️ 실시간 데이터 기반 판결 실행", use_container_width=True):
        if not f_name:
            st.error("❗ 상품 정보가 부족합니다.")
        else:
            with st.spinner('🌐 구글 실시간 시세 분석 중...'):
                real_low = GooglePriceEngine.get_realtime_price(f_name)
            
            if real_low:
                # 판결 화면 (이전 UI 유지)
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 판결 리포트")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p class="stat-label">확인 가격</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="stat-value">{f_price:,}원</p>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<p class="stat-label">실시간 최저가(추정)</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="stat-value">{real_low:,}원</p>', unsafe_allow_html=True)
                
                diff = f_price - real_low
                st.markdown("---")
                
                if f_price <= real_low:
                    st.success("🔥 **역대급 딜!** 실시간 최저가보다 저렴합니다.")
                elif f_price <= real_low * 1.1:
                    st.info("✅ **적정 가격** 온라인 시세와 비슷합니다.")
                else:
                    st.error(f"💀 **호구 주의!** 최저가보다 {diff:,}원 더 비쌉니다.")
                
                q_enc = urllib.parse.quote(f_name)
                st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q_enc}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 데이터 대조</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("⚠️ 시세 정보를 찾지 못했습니다. 상품명을 더 구체적으로(브랜드 포함) 입력해주세요.")

if __name__ == "__main__":
    main()
