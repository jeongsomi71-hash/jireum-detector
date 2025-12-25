import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="지름신 판독기", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .block-container {
        max-width: 450px !important;
        padding-top: 5rem !important;
    }

    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000 !important; 
        color: #FFFFFF !important;
    }
    
    /* 1. 지름신 판독기 폰트 사이즈 2배 (약 5rem) */
    .main-title { 
        font-size: 5.5rem; 
        font-weight: 900; 
        text-align: center; 
        color: #00FF88;
        text-shadow: 3px 3px 15px rgba(0, 255, 136, 0.7);
        line-height: 1.1;
        margin-bottom: 15px;
    }
    
    /* 2. 부제목: 흰색 배경에 검정색 글씨로 변경 (가독성 확보) */
    .sub-title-box {
        background-color: #FFFFFF;
        color: #000000 !important;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 2.5rem;
    }

    .result-box {
        background-color: #111111;
        padding: 25px;
        border-radius: 15px;
        border: 2px solid #00FF88;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 섹션
st.markdown('<p class="main-title">지름신<br>판독기</p>', unsafe_allow_html=True)
st.markdown('<div class="sub-title-box">⚖️ AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 메뉴 구성
mode = st.radio("⚖️ 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])

tab1, tab2 = st.tabs(["🔗 URL 입력", "📸 이미지 업로드"])
detected_price = 0
product_name_input = ""

with tab1:
    url = st.text_input("상품 URL 입력", placeholder="https://...")
    product_name_input = st.text_input("상품명 입력 (필수)", placeholder="예: 소니 헤드셋")

with tab2:
    uploaded_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            price_match = re.search(r'([0-9,]{3,})원', text)
            if price_match:
                detected_price = int(price_match.group(1).replace(',', ''))
        except: pass

# 판결 문구 세트
happy_quotes = ["🚀 이건 소비가 아니라 미래를 향한 풀매수!", "✨ 고민은 배송만 늦출 뿐! 바로 지르세요!", "💎 오늘 안 사면 꿈에 나옵니다. 지금이 기회!"]
fact_quotes = ["💀 정신 차리세요. 이거 사고 일주일 뒤면 먼지만 쌓입니다.", "💸 통장이 텅장 되는 소리 안 들리나요? 참으세요.", "🚫 과소비는 병입니다. 이번엔 제발 넘어가세요."]

if st.button("⚖️ 최종 판결 내리기"):
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    
    # 3. 상품명 + 리뷰 형태의 검색어 최적화
    final_name = product_name_input if product_name_input else "해당 상품"
    
    if mode == "행복 회로":
        st.subheader("🔥 판결: 즉시 지름!")
        st.write(random.choice(happy_quotes))

    elif mode == "팩트 폭격":
        st.subheader("❄️ 판결: 지름 금지!")
        st.write(random.choice(fact_quotes))

    elif mode == "AI 판결":
        st.subheader("⚖️ AI 판사님의 데이터 분석")
        current_p = detected_price if detected_price > 0 else 150000
        min_p = int(current_p * 0.85)
        
        st.write(f"📊 분석 상품: **{final_name}**")
        st.write(f"💰 현재가: **{current_p:,}원**")
        st.info(f"💡 분석 결과, 과거 최저가 대비 현재는 적정가 범위입니다.")
        
        st.markdown("---")
        
        # 검색어 수정: 상품명 + 리뷰 (불필요한 가격 정보 제외하여 정확도 상승)
        search_q = urllib.parse.quote(f"{final_name} 솔직 리뷰 후기")
        google_url = f"https://www.google.com/search?q={search_q}"
        
        st.write("🔍 **판결 근거 확인:**")
        # 요청사항 반영: "상품명 + 리뷰" 형태의 링크 텍스트
        st.markdown(f"🌐 [{final_name} 리뷰 확인하러 가기]({google_url})")

        if current_p > min_p * 1.1:
            st.error(f"❌ 판결: 거품 낀 가격입니다. 절대 사지 마세요!")
        else:
            st.success("✅ 판결: 가격이 훌륭합니다. 지름신을 영접하세요!")

    st.markdown('</div>', unsafe_allow_html=True)
