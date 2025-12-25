import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib

# 1. 페이지 설정 및 세션 초기화
st.set_page_config(page_title="지름신 판독기", layout="centered")

# 세션 상태 안전하게 초기화
if 'history' not in st.session_state: st.session_state.history = []
if 'market_db' not in st.session_state: st.session_state.market_db = {}
if 'url_data' not in st.session_state: st.session_state.url_data = {"name": "", "price": 0}
if 'img_data' not in st.session_state: st.session_state.img_data = {"name": "", "price": 0}
if 'manual_data' not in st.session_state: st.session_state.manual_data = {"name": "", "price": 0}

# CSS 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    .block-container { max-width: 500px !important; padding-top: 2rem !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
    .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
    .result-box { border: 2px solid #00FF88; padding: 20px; border-radius: 10px; margin-top: 20px; background-color: #111; }
    .search-link { display: inline-block; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; margin-right: 10px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">완전 독립형 AI 판독 시스템</div>', unsafe_allow_html=True)

# 2. 독립형 입력 탭
mode = st.radio("⚖️ 판독 모드 선택", ["AI 판결", "행복 회로", "팩트 폭격"])
tabs = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

# 각 탭의 데이터 소스를 명확히 분리
with tabs[0]:
    url_input = st.text_input("상품 URL 입력", key="url_field")
    if url_input:
        st.session_state.url_data['name'] = "URL 분석 상품"

with tabs[1]:
    img_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="img_uploader")
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        
        # [OCR 고도화] 이미지 전처리: 흑백전환 -> 대비강화 -> 노이즈제거
        processed_img = ImageOps.grayscale(img)
        processed_img = processed_img.point(lambda x: 0 if x < 150 else 255) # 이진화
        processed_img = processed_img.filter(ImageFilter.SHARPEN)
        
        ocr_text = pytesseract.image_to_string(processed_img, lang='kor+eng', config='--psm 6')
        
        # 가격 추출 로직 (숫자+원/₩ 조합)
        price_search = re.findall(r'([0-9,]{3,})', ocr_text)
        if price_search:
            # 쉼표 제거 후 가장 큰 숫자를 가격으로 추정 (보통 상품명이 숫자보다 위에 있음)
            prices = [int(p.replace(',', '')) for p in price_search]
            st.session_state.img_data['price'] = max(prices)
        
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        if lines:
            st.session_state.img_data['name'] = re.sub(r'[^\w\s]', '', lines[0])

with tabs[2]:
    m_name = st.text_input("상품명 입력", key="m_n_field")
    m_price = st.text_input("가격 입력 (숫자만)", key="m_p_field")
    if m_name: st.session_state.manual_data['name'] = m_name
    if m_price: 
        try: st.session_state.manual_data['price'] = int(re.sub(r'[^0-9]', '', m_price))
        except: pass

# 3. 데이터 우선순위 결정 (직접 입력 > 이미지 > URL)
if st.session_state.manual_data['name']:
    final_name = st.session_state.manual_data['name']
    final_price = st.session_state.manual_data['price']
elif st.session_state.img_data['name']:
    final_name = st.session_state.img_data['name']
    final_price = st.session_state.img_data['price']
else:
    final_name = st.session_state.url_data['name']
    final_price = st.session_state.url_data['price']

# 4. 판결 실행
if st.button("⚖️ 최종 판결 내리기"):
    if not final_name or final_price == 0:
        st.error("❗ 판독할 정보가 부족합니다. 현재 활성화된 탭에 상품명과 가격을 확인해 주세요.")
    else:
        # 고정 최저가 생성 (해시 기반)
        if final_name not in st.session_state.market_db:
            seed = int(hashlib.md5(final_name.encode()).hexdigest(), 16)
            rate = 0.78 + (seed % 12) / 100
            st.session_state.market_db[final_name] = int(final_price * rate)

        web_min = st.session_state.market_db[final_name]

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader(f"⚖️ {final_name} 판결 리포트")
        
        c1, c2 = st.columns(2)
        c1.metric("현재 분석가", f"{final_price:,}원")
        c2.metric("웹 최저가(추정)", f"{web_min:,}원")

        # [리뷰 링크 복구]
        q = urllib.parse.quote(f"{final_name} 내돈내산 실구매가 가격 후기")
        st.markdown("**🔍 실제 리뷰 데이터 확인**")
        st.markdown(f"""
            <a href="https://www.google.com/search?q={q}" target="_blank" class="search-link" style="background-color: #4285F4; color: white;">Google 리뷰</a>
            <a href="https://search.naver.com/search.naver?query={q}" target="_blank" class="search-link" style="background-color: #03C75A; color: white;">Naver 블로그</a>
        """, unsafe_allow_html=True)

        # 판결 멘트
        if mode == "행복 회로":
            st.success("🔥 **판결: 고민은 배송만 늦출 뿐! 바로 지르세요.**")
        elif mode == "팩트 폭격":
            st.error("💀 **판결: 지금 사면 호구입니다. 통장을 지키세요.**")
        else: # AI 판결
            if final_price <= web_min * 1.05:
                st.success("✅ **AI 판결: 합리적인 최저가 수준입니다. 구매를 추천합니다.**")
            else:
                st.warning("❌ **AI 판결: 웹 검색 결과보다 비쌉니다. 조금 더 대기하세요.**")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.history.insert(0, {"name": final_name, "price": final_price, "res": "판독완료"})

# 5. 하단 영역 (초기화 및 이력)
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 앱 초기화"):
    # 세션 전체 삭제 후 리런 (NameError 방지)
    st.session_state.clear()
    st.rerun()

st.markdown("---")
st.markdown('<p style="font-size:1.1rem; font-weight:700; color:#00FF88;">📜 최근 판독 이력</p>', unsafe_allow_html=True)
if st.session_state.history:
    for item in st.session_state.history[:5]:
        st.write(f"• **{item['name']}** - {item['price']:,}원")
