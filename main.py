import streamlit as st
from PIL import Image
import pytesseract
import re

# 페이지 설정
st.set_page_config(page_title="지름 판독기", layout="centered")

# CSS 스타일링 (이미지 디자인 반영)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000; color: #ffffff; }
    .main-title { font-size: 3rem; font-weight: bold; text-align: center; background: linear-gradient(to right, #a1ffce, #faffd1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .sub-title { text-align: center; color: #cccccc; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">지름 판독기</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">살까 말까 고민될 땐? <span style="color:#4CAF50; font-weight:bold;">AI 판사님</span>께 물어보세요.</p>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔗 URL 입력", "🖼️ 이미지 업로드"])

with tab1:
    url = st.text_input("상품 URL을 입력하세요")
    if st.button("🔗 링크 판독"):
        st.info("링크 분석은 현재 준비 중입니다. 이미지 업로드를 먼저 사용해 보세요!")

with tab2:
    uploaded_file = st.file_uploader("영수증이나 상품 스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="분석할 이미지", width=300)
        
        # 실제 OCR 분석 시작
        with st.spinner("이미지에서 텍스트를 추출하는 중..."):
            try:
                # 리눅스 서버용 Tesseract 설정 (packages.txt가 설치해줌)
                text = pytesseract.image_to_string(img, lang='kor+eng')
                
                # 금액 추출 (숫자+원 패턴 찾기)
                prices = re.findall(r'[0-9,]{3,}원', text)
                
                st.success("✅ 분석 완료!")
                st.subheader("🧐 AI 판사님의 소견")
                
                if prices:
                    st.write(f"감지된 가격: **{prices[0]}**")
                    st.warning("판결: 이 가격이면 조금 더 참아보시는 게 어떨까요? (팩트 폭격)")
                else:
                    st.write("텍스트 추출 내용:", text[:100] + "...")
                    st.info("가격이 명확히 보이지 않지만, 일단 지르고 보는 건 어떨까요? (행복 회로)")
            except Exception as e:
                st.error(f"OCR 엔진 설정 중입니다. 잠시만 기다려주세요! (에러: {e})")
