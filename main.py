import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ==========================================
# 1. 시세 추적 엔진 (강제 쿼리 & 와이드 스캔)
# ==========================================
class CommunityHotDealEngine:
    @staticmethod
    def fetch_from_google(query, headers):
        """구글 검색 결과의 모든 텍스트 노드에서 가격 데이터 추출"""
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        try:
            # 타임아웃 연장 및 모바일 에이전트 활용으로 차단 회피
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 429: return "BOT_DETECTED"
            if response.status_code != 200: return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 텍스트 추출 전 불필요한 태그 제거 (데이터 노이즈 제거)
            for s in soup(["script", "style", "iframe", "head", "nav", "footer"]):
                s.extract()
            
            all_content = soup.get_text(separator=' ')
            
            # 정교한 가격 패턴 매칭 (연도 제외, 콤마/단위 대응)
            price_list = []
            # 202X 연도를 피하면서 4~10자리 숫자와 단위(원/만)를 포착
            pattern = re.compile(r'(?<!\d)(?!202[456])([0-9,]{4,10})\s?(원|만)')
            found = pattern.findall(all_content)
            
            for f_val, unit in found:
                num_str = f_val.replace(',', '')
                if not num_str: continue
                val = int(num_str)
                
                # '만' 단위 보정
                if unit == '만': val *= 10000
                
                # 현실적인 가격대 필터 (1만원 ~ 2,000만원)
                if 10000 < val < 20000000:
                    price_list.append(val)
            
            return price_list
        except:
            return None

    @staticmethod
    def get_realtime_price(product_name):
        # 차단 확률이 낮은 모바일 사파리 헤더 활용
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept-Language": "ko-KR,ko;q=0.9"
        }
        
        # 상품명 키워드화 및 가격 유도 키워드 추가
        keywords = product_name.replace(" ", ", ")
        communities = "(뽐뿌 OR 루리웹 OR 클리앙)"

        # --- [1단계] 정밀 강제 탐색 (단위 키워드 포함) ---
        # "아이폰, 15, 원, 만, (뽐뿌 OR 루리웹 OR 클리앙)" 형태로 검색 유도
        and_query = f"{keywords}, 원, 만, {communities}"
        with st.spinner('🎯 가격 데이터 정밀 추적 중 (1/2)...'):
            res_and = CommunityHotDealEngine.fetch_from_google(and_query, headers)
            
        if res_and == "BOT_DETECTED": return "BOT_DETECTED"
        if res_and and len(res_and) > 0:
            res_and.sort()
            return res_and[0]

        # --- [2단계] 광역 흔적 스캔 (보수적 폴백) ---
        or_query = f"{product_name} 시세 가격 {communities}"
        with st.spinner('🌐 시세 흔적 광역 스캔 중 (2/2)...'):
            res_or = CommunityHotDealEngine.fetch_from_google(or_query, headers)
            
        if res_or == "BOT_DETECTED": return "BOT_DETECTED"
        if res_or and len(res_or) > 0:
            res_or.sort()
            return res_or[0]

        return "INFO_NOT_FOUND"

# ==========================================
# 2. UI 및 리셋 기능 (기존 디자인 원칙 준수)
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
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #00FF88; }
        .stButton>button[kind="secondary"] { width: 100%; background-color: #333; color: white; border: none; margin-top: 10px; }
        </style>
        """, unsafe_allow_html=True)

def reset_state():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# ==========================================
# 3. 메인 로직
# ==========================================
def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    
    col_empty, col_reset = st.columns([4, 1])
    with col_reset:
        if st.button("🔄 리셋"): reset_state()

    tabs = ["📸 이미지 판결", "✍️ 직접 상품명 입력"]
    sel_tab = st.radio("📥 판독 방식", tabs, horizontal=True)

    f_name, f_price = "", 0

    if sel_tab == "📸 이미지 판결":
        file = st.file_uploader("이미지 업로드", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
            text_raw = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            lines = [l.strip() for l in text_raw.split('\n') if len(l.strip()) > 2]
            f_name = lines[0] if lines else ""
            if f_name: st.info(f"🔍 인식 결과: **{f_name}**")
            
    elif sel_tab == "✍️ 직접 상품명 입력":
        f_name = st.text_input("📦 상품명", placeholder="예: 아이폰, 15, 자급제")
        p_val = st.text_input("💰 현재 확인 가격", placeholder="숫자만 입력")
        if f_name and p_val:
            try:
                f_price = int(re.sub(r'[^0-9]', '', p_val))
            except: f_price = 0

    if st.button("⚖️ 실시간 데이터 기반 판결 실행", use_container_width=True):
        if not f_name:
            st.error("❗ 상품명을 입력해주세요.")
        else:
            result = CommunityHotDealEngine.get_realtime_price(f_name)
            
            if isinstance(result, int):
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 판결 리포트")
                c1, c2 = st.columns(2)
                c1.metric("나의 확인가", f"{f_price:,}원")
                c2.metric("커뮤니티 시세", f"{result:,}원")
                st.markdown("---")
                if f_price <= result:
                    st.success("🔥 **역대급 가격!** 지금 바로 탑승하세요.")
                else:
                    st.error(f"💀 **주의!** 시세보다 {f_price - result:,}원 더 비쌉니다.")
                
                q_enc = urllib.parse.quote(f_name)
                st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q_enc}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 확인</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu&keyword={q_enc}" target="_blank" class="ppomppu-btn">🔥 뽐뿌 실시간 핫딜 글 보기</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            elif result == "BOT_DETECTED":
                st.error("🚫 **봇 감지로 실패**: 구글 접속이 일시 차단되었습니다. 잠시 후 재시도 바랍니다.")
            else:
                st.warning(f"**⚠️ 정보 수집 실패**: '{f_name}'에 대한 명확한 가격 기록을 찾지 못했습니다.\n\n**💡 팁**: 상품명에 '자급제', '128GB' 같은 사양을 추가하거나 영어 이름을 섞어보세요!")

if __name__ == "__main__":
    main()
