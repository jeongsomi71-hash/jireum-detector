import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ==========================================
# 1. 커뮤니티 제목/체감가 분석 엔진
# ==========================================
class CommunityHotDealEngine:
    @staticmethod
    def get_realtime_price(product_name):
        """구글 검색 결과 중 커뮤니티 게시글 제목의 '체감가' 추출"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        # 검색 쿼리: 체감가, 최종가 키워드로 커뮤니티 기록 유도
        query = urllib.parse.quote(f"{product_name} 뽐뿌 체감가 최종가")
        url = f"https://www.google.com/search?q={query}"
        
        try:
            response = requests.get(url, headers=headers, timeout=7)
            if response.status_code != 200: return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # 검색 결과의 제목(h3) 및 요약 텍스트 추출
            elements = soup.find_all(['h3', 'div'], class_=re.compile("vvsyf|VwiC3b|LC20lb"))
            
            price_list = []
            for item in elements:
                text = item.get_text()
                # 패턴: 숫자+원 또는 숫자+만 (202X 연도 제외)
                found = re.findall(r'(?<!202)([0-9,]{2,})\s?(원|만)', text)
                
                for f_val, unit in found:
                    num_str = f_val.replace(',', '')
                    val = int(num_str)
                    if unit == '만': val *= 10000 # '85만' -> 850,000 변환
                    
                    # 현실적인 가격대 필터 (5,000원 ~ 2,000만원)
                    if 5000 < val < 20000000:
                        price_list.append(val)
            
            if price_list:
                price_list.sort()
                return price_list[0] # 가장 낮은 '역대급 체감가' 반환
        except:
            return None
        return None

# ==========================================
# 2. UI 스타일 정의 (블랙 & 그린 테마 유지)
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
        .naver-btn { display: block; width: 100%; background-color: #03C75A; color: white !important; text-align: center; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 1.1rem; margin: 10px 0; }
        .ppomppu-btn { display: block; width: 100%; background-color: #FF6600; color: white !important; text-align: center; padding: 15px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 1.1rem; margin: 10px 0; }
        .stat-label { color: #888; font-size: 0.9rem; }
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #00FF88; }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# 3. 메인 어플리케이션 로직
# ==========================================
def main():
    apply_custom_style()
    
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888; font-size:0.8rem; margin-top:-20px; margin-bottom:20px;">커뮤니티 실시간 핫딜 & 체감가 분석 기반</p>', unsafe_allow_html=True)

    # 방식 선택 메뉴
    tabs = ["📸 이미지 판결", "✍️ 직접 상품명 입력"]
    sel_tab = st.radio("📥 판독 방식", tabs, horizontal=True)

    f_name, f_price = "", 0

    if sel_tab == "📸 이미지 판결":
        file = st.file_uploader("제품 이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            # OCR 전처리 및 추출
            proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
            text_raw = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            lines = [l.strip() for l in text_raw.split('\n') if len(l.strip()) > 2]
            f_name = lines[0] if lines else ""
            if f_name: st.info(f"🔍 이미지 인식 결과: **{f_name}**")

    elif sel_tab == "✍️ 직접 상품명 입력":
        n_val = st.text_input("📦 상품명", placeholder="정확한 모델명을 입력하세요")
        p_val = st.text_input("💰 현재 확인 가격", placeholder="숫자만 입력")
        if n_val and p_val:
            f_name = n_val
            f_price = int(re.sub(r'[^0-9]', '', p_val))

    if st.button("⚖️ 핫딜 데이터 기반 판결 실행", use_container_width=True):
        if not f_name:
            st.error("❗ 상품 정보를 입력하거나 이미지를 업로드해주세요.")
        else:
            with st.spinner('🌐 커뮤니티 시세 및 체감가 분석 중...'):
                real_low = CommunityHotDealEngine.get_realtime_price(f_name)
            
            if real_low:
                # [판결 리포트 UI]
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 판결 리포트")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p class="stat-label">나의 확인가</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="stat-value">{f_price:,}원</p>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<p class="stat-label">역대급 체감가</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="stat-value">{real_low:,}원</p>', unsafe_allow_html=True)
                
                st.markdown("---")
                if f_price <= real_low:
                    st.success("🔥 **미친 가격 발견!** 커뮤니티 역대 핫딜보다 저렴합니다. 당장 타세요!")
                else:
                    st.error(f"💀 **주의!** 고수들이 공유한 체감가보다 {f_price - real_low:,}원 비쌉니다.")
                
                # 링크 버튼
                q_enc = urllib.parse.quote(f_name)
                st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q_enc}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 확인</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu&keyword={q_enc}" target="_blank" class="ppomppu-btn">🔥 뽐뿌 실시간 핫딜 글 보기</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # [솔직한 안내 및 실전 검색 팁]
                st.warning("""
                **⚠️ 시세를 분석할 수 있는 '데이터 흔적'을 찾지 못했습니다.**
                
                구글이 수집한 커뮤니티 기록 중 가격 정보가 명확하지 않습니다. 
                검색 엔진이 **핫딜 게시글의 제목**을 더 잘 찾도록 아래 팁을 참고해 보세요.
                
                **🛠️ 실전 검색 성공률 높이는 법 (Power Search)**
                1. **불필요한 조사 제거 (키워드 중심)**: 
                   * (예) **갤럭시, S24, 울트라** (쉼표로 구분하면 엔진이 더 넓게 탐색합니다)
                2. **모델명/용량 구체화**: 
                   * 가격은 스펙에 따라 게시글 제목이 다릅니다. (예: **아이폰, 15, 프로, 256GB**)
                3. **특수문자 제외**: 괄호나 특수문자는 빼고 순수 키워드만 입력해 보세요.
                4. **브랜드명 포함**: **삼성, LG, 애플** 등 브랜드명을 꼭 넣어주세요.
                """)

if __name__ == "__main__":
    main()
