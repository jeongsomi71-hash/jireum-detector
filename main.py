import streamlit as st
from PIL import Image
import pytesseract
import re

# 페이지 설정: 레이아웃을 'centered'로 유지하되 CSS로 너비를 강제 조정
st.set_page_config(page_title="지름 판독기", layout="centered")

# CSS 스타일링: 쇼츠(세로형) 최적화 및 고대비 색상 적용
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    /* 쇼츠 전용 모바일 뷰 설정 (너비를 좁게 제한) */
    .block-container {
        max-width: 450px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000; 
        color: #FFFFFF;
    }
    
    /* 제목 강조: 쇼츠에서 눈에 확 띄도록 크게 */
    .main-title { 
        font-size: 3rem; 
        font-weight: 900; 
        text-align: center; 
        background: linear-gradient(to right, #00FF88, #60EFFF); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        margin-bottom: 0px;
    }
    .sub-title { 
        text-align: center; 
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 2rem; 
    }
    
    /* 버튼 및 입력창 가시성 강화 */
    .stButton>button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        background-color: #00FF88 !important;
        color: #000000 !important;
        border-radius: 12px;
    }
    
    /* 결과 박스 강조 */
    .result-box {
        background-color: #1A1A1A;
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #00FF88;
        margin-top: 25px;
    }
    
    /* 탭 메뉴 글자 크기 */
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 영역
st.markdown('<p class="main-title">지름 판독기</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">살까 말까 고민될 땐? AI 판사님께.</p>', unsafe_allow_html=True)

# 메뉴 구성
mode = st.selectbox("⚖️ 판독 모드를 선택하세요", ["1) 행복 회로", "2) 팩트 폭격", "3) AI 판결"])

tab1, tab2 = st.tabs(["🔗 링크 분석", "📸 이미지 스캔"])

detected_price = 0

with tab1:
    url = st.text_input("상품 URL을 입력하세요", placeholder="링크를 붙여넣으세요")
    if url:
        st.info("💡 팁: 쿠팡 등 일부 사이트는 이미지 업로드가 더 정확합니다.")

with tab2:
    uploaded_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True) # 쇼츠 화면에 꽉 차게 변경
        
        with st.spinner("정보 추출 중..."):
            try:
                text = pytesseract.image_to_string(img, lang='kor+eng')
                price_match = re.search(r'([0-9,]{3,})원', text)
                if price_match:
                    detected_price = int(price_match.group(1).replace(',', ''))
                    st.success(f"금액 감지: {detected_price:,}원")
            except:
                st.error("OCR 엔진 오류가 발생했습니다.")

# 판결 로직
if st.button("⚖️ 최종 판결 내리기"):
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    
    if mode == "1) 행복 회로":
        st.subheader("🔥 행복 회로 가동!")
        st.markdown(f"### **\"이것은 소비가 아니라 투자입니다!\"**")
        st.write("당신의 삶의 질을 200% 올려줄 기회입니다. 하루 커피 한 잔 값으로 얻는 행복, 고민은 배송만 늦출 뿐입니다!")

    elif mode == "2) 팩트 폭격":
        st.subheader("❄️ 냉정한 팩트 폭격")
        st.markdown(f"### **\"정신 차리세요!\"**")
        st.write(f"지금 통장 잔고를 확인하셨나요? {detected_price:,}원이면 국밥이 몇 그릇입니까? 이거 없어도 당신 인생에 아무 지장 없습니다.")

    elif mode == "3) AI 판결":
        st.subheader("⚖️ AI 판사님의 선고")
        # 가상의 데이터 비교 로직
        base_p = detected_price if detected_price > 0 else 150000
        min_p = int(base_p * 0.85)
        
        st.write(f"현재 분석가: **{base_p:,}원**")
        st.write(f"역대 최저가: **{min_p:,}원**")
        
        if base_p > min_p * 1.1:
            st.error("❌ 판결: 지금 사면 바보입니다!")
            st.info(f"💡 추천가: **{int(min_p * 1.05):,}원** 이하일 때 구매하세요.")
        else:
            st.success("✅ 판결: 적정 가격입니다. 지금 지르세요!")

    st.markdown('</div>', unsafe_allow_html=True)
