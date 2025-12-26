import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from PIL import Image, ImageOps, ImageFilter
import pytesseract

# ==========================================
# 1. 커뮤니티 제목/체감가 분석 엔진 (진단 기능 강화)
# ==========================================
class CommunityHotDealEngine:
    @staticmethod
    def get_realtime_price(product_name):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        # [업데이트] '최저가'를 필수가 아닌 검색 결과 확장을 위한 쿼리로 구성
        # 커뮤니티 이름만으로 검색하여 더 많은 게시글 제목을 노출시킴
        query = urllib.parse.quote(f"{product_name} (뽐뿌 OR 루리웹 OR 클리앙)")
        url = f"https://www.google.com/search?q={query}"
        
        try:
            response = requests.get(url, headers=headers, timeout=7)
            
            # [진단 로직 1] 봇 감지 여부 체크 (429: Too Many Requests)
            if response.status_code == 429:
                return "BOT_DETECTED"
            if response.status_code != 200:
                return "SERVER_ERROR"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            all_text = soup.get_text(separator=' ')
            
            # 가격 패턴 추출
            price_list = []
            found = re.findall(r'(?<!202)([0-9,]{2,})\s?(원|만)', all_text)
            
            for f_val, unit in found:
                num_str = f_val.replace(',', '')
                val = int(num_str)
                if unit == '만': val *= 10000
                if 10000 < val < 20000000:
                    price_list.append(val)
            
            if price_list:
                price_list.sort()
                return price_list[0]
            else:
                # [진단 로직 2] 접속은 성공했으나 가격 데이터가 없음
                return "INFO_NOT_FOUND"
                
        except Exception:
            return "CONNECTION_FAILED"

# (중략: apply_custom_style 함수는 기존 블랙&그린 테마를 절대적으로 유지함)
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
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_custom_style()
    st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#888; font-size:0.8rem; margin-top:-20px; margin-bottom:20px;">커뮤니티 실시간 분석 시스템</p>', unsafe_allow_html=True)

    tabs = ["📸 이미지 판결", "✍️ 직접 상품명 입력"]
    sel_tab = st.radio("📥 판독 방식", tabs, horizontal=True)

    f_name, f_price = "", 0

    if sel_tab == "📸 이미지 판결":
        file = st.file_uploader("제품 이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])
        if file:
            img = Image.open(file)
            st.image(img, use_container_width=True)
            proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
            text_raw = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
            lines = [l.strip() for l in text_raw.split('\n') if len(l.strip()) > 2]
            f_name = lines[0] if lines else ""
            if f_name: st.info(f"🔍 이미지 인식 결과: **{f_name}**")
    elif sel_tab == "✍️ 직접 상품명 입력":
        n_val = st.text_input("📦 상품명")
        p_val = st.text_input("💰 현재 확인 가격")
        if n_val and p_val:
            f_name = n_val
            f_price = int(re.sub(r'[^0-9]', '', p_val))

    if st.button("⚖️ 핫딜 데이터 기반 판결 실행", use_container_width=True):
        if not f_name:
            st.error("❗ 정보를 입력해주세요.")
        else:
            with st.spinner('🌐 데이터를 분석 중입니다...'):
                result = CommunityHotDealEngine.get_realtime_price(f_name)
            
            # [판결 결과 핸들링]
            if isinstance(result, int):
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                st.subheader(f"📊 '{f_name}' 판결 리포트")
                c1, c2 = st.columns(2)
                c1.metric("나의 확인가", f"{f_price:,}원")
                c2.metric("분석된 시세", f"{result:,}원")
                st.markdown("---")
                if f_price <= result:
                    st.success("🔥 **역대급 딜!** 당장 구매를 추천합니다.")
                else:
                    st.error(f"💀 **주의!** 분석된 시세보다 비쌉니다.")
                q_enc = urllib.parse.quote(f_name)
                st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q_enc}" target="_blank" class="naver-btn">🛒 네이버 쇼핑 실시간 확인</a>', unsafe_allow_html=True)
                st.markdown(f'<a href="https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu&keyword={q_enc}" target="_blank" class="ppomppu-btn">🔥 뽐뿌 실시간 핫딜 글 보기</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            elif result == "BOT_DETECTED":
                st.error("🚫 **봇 감지로 실패**: 구글이 짧은 시간 내 잦은 요청으로 접속을 차단했습니다. 약 5~10분 후 다시 시도해 주세요.")
            
            else: # INFO_NOT_FOUND 또는 기타 실패
                st.warning(f"""
                **⚠️ 정보 수집 실패**: 구글 검색 결과에서 유효한 가격 데이터를 찾지 못했습니다.
                
                **🛠️ 실전 검색 성공률 높이는 법**
                1. **키워드 나열**: 단어 사이에 쉼표를 넣어보세요 (예: **아이폰, 15, 자급제**)
                2. **모델명 구체화**: 용량이나 스펙을 포함하세요 (예: **256GB**)
                3. **불필요한 단어 제거**: '최저가', '구매' 등의 단어 없이 상품명 위주로 입력해 보세요.
                """)

if __name__ == "__main__":
    main()
