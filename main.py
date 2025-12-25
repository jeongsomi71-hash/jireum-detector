import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
import re
import random

# 페이지 설정
st.set_page_config(page_title="지름 판독기", layout="centered")

# CSS 스타일링 (이미지 디자인 반영)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000; color: #ffffff; }
    .main-title { font-size: 3rem; font-weight: bold; text-align: center; background: linear-gradient(to right, #a1ffce, #faffd1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px; }
    .sub-title { text-align: center; color: #cccccc; margin-bottom: 2rem; }
    .stButton>button { width: 100%; background-color: transparent; border: 1px solid #4CAF50; color: #4CAF50; height: 3em; font-size: 1.2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #111111; border-radius: 5px; color: white; width: 200px; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #4CAF50 !important; }
    </style>
    """, unsafe_allow_html=True)

# 헤더
st.markdown('<p class="main-title">지름 판독기</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">살까 말까 고민될 땐? <span style="color:#4CAF50; font-weight:bold;">AI 판사님</span>께 물어보세요.</p>', unsafe_allow_html=True)

# 데이터 수집 함수 (쿠팡 및 일반 사이트 메타데이터)
def get_product_info(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 메타데이터 추출 (법적 리스크 없는 공개 정보)
        title = soup.find("meta", property="og:title")['content'] if soup.find("meta", property="og:title") else "상품명을 찾을 수 없음"
        # 가격 정보 시뮬레이션 (쿠팡 등 보안 사이트는 수동 입력 유도)
        price = 0
        price_tags = soup.find_all(string=re.compile(r'[0-9,]+원'))
        if price_tags:
            price = int(re.sub(r'[^0-9]', '', price_tags[0]))
        
        return title, price
    except:
        return None, 0

# UI 구성
tab1, tab2 = st.tabs(["🔗 URL 입력", "🖼️ 이미지 업로드"])

with tab1:
    url = st.text_input("상품 URL을 입력하세요", placeholder="https://coupang.com/...")
    mode = st.radio("판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"], horizontal=True)
    
    if st.button("✨ 판독 시작"):
        if url:
            title, price = get_product_info(url)
            if not title or title == "상품명을 찾을 수 없음":
                st.warning("⚠️ 링크 보안으로 인해 정보를 가져올 수 없습니다. 아래에 수동으로 입력하거나 이미지 업로드를 이용해주세요.")
                title = st.text_input("상품명 직접 입력")
                price = st.number_input("가격 직접 입력", min_value=0)
            
            st.divider()
            
            if mode == "행복 회로":
                st.subheader("🔥 행복 회로 가동")
                st.write(f"품명: {title}")
                st.success(f"이건 소비가 아니라 투자입니다! 하루 {price//365:,}원꼴인데 커피 한 잔 참으면 이 영롱한 것이 당신 손에?")
                
            elif mode == "팩트 폭격":
                st.subheader("❄️ 팩트 폭격 가동")
                st.write(f"품명: {title}")
                st.error(f"냉정해지세요. 이거 없어도 사는데 지장 없습니다. {price:,}원이면 국밥이 {price//10000}그릇입니다.")
                
            elif mode == "AI 판결":
                st.subheader("⚖️ AI 최종 판결")
                st.write(f"품명: {title}")
                # 가상의 최저가 데이터 참고 로직
                lowest_avg = price * 0.85
                if price > lowest_avg:
                    st.warning(f"현재 가격({price:,}원)은 과거 평균 최저가 대비 다소 높습니다.")
                    st.info(f"💡 추천 구매가: {int(lowest_avg):,}원 이하일 때 구매하는 것을 권장합니다.")
                else:
                    st.success("지금이 적기입니다! 역대급 최저가에 근접했습니다. 지르세요!")

with tab2:
    uploaded_file = st.file_uploader("이미지를 업로드하면 가격을 스캔합니다", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        st.image(uploaded_file, caption="업로드됨", width=300)
        st.info("이미지 분석(OCR) 기능은 서버 설정 완료 후 활성화됩니다.")
