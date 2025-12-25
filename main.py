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
    
    .main-title { 
        font-size: 5.5rem; 
        font-weight: 900; 
        text-align: center; 
        color: #00FF88;
        text-shadow: 3px 3px 15px rgba(0, 255, 136, 0.7);
        line-height: 1.1;
        margin-bottom: 15px;
    }
    
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

# 세션 상태 초기화 (이전 결과 지우기용)
if 'last_input' not in st.session_state:
    st.session_state.last_input = ""

# 1. 상품 정보 입력 섹션 (최우선 순위)
st.subheader("🛒 상품 정보 직접 입력")
manual_name = st.text_input("상품명을 입력하세요", key="manual_name")
manual_price = st.text_input("가격을 입력하세요 (숫자만)", key="manual_price")

# 2. 판독 모드 및 추가 입력
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tab1, tab2 = st.tabs(["🔗 URL 입력", "📸 이미지 업로드"])

detected_price = 0
ocr_product_name = ""

with tab1:
    url = st.text_input("상품 URL 입력", placeholder="https://...")

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
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
            if lines: ocr_product_name = lines[0]
        except: pass

# 3. 판독 실행 로직
if st.button("⚖️ 최종 판결 내리기"):
    # 입력값 정제
    final_name = manual_name if manual_name else ocr_product_name
    final_price = 0
    try:
        if manual_price:
            final_price = int(re.sub(r'[^0-9]', '', manual_price))
        else:
            final_price = detected_price
    except: pass

    # 예외 처리: 정보 부족 시 단계별 요청
    if not final_name and not url and not uploaded_file:
        st.warning("🧐 분석할 상품이 없습니다. URL을 넣거나 상품 이미지를 업로드해 주세요.")
    elif (not final_name or final_price == 0) and (url or uploaded_file):
        if not final_name and not ocr_product_name:
            st.error("❓ 상품명을 인식하지 못했습니다. 상단의 입력창에 직접 상품명을 적어주세요.")
        if final_price == 0 and detected_price == 0:
            st.error("❓ 가격을 인식하지 못했습니다. 상단의 입력창에 직접 가격을 적어주세요.")
    else:
        # 정상 판결 출력 (이전 결과는 Streamlit 특성상 버튼 클릭 시 새로고침되어 자동 삭제됨)
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        
        happy_quotes = ["🚀 이건 소비가 아니라 미래를 향한 풀매수!", "✨ 고민은 배송만 늦출 뿐! 바로 지르세요!"]
        fact_quotes = ["💀 정신 차리세요. 일주일 뒤면 먼지만 쌓입니다.", "💸 통장이 텅장 되는 소리 안 들리나요?"]

        if mode == "행복 회로":
            st.subheader(f"🔥 {final_name}: 즉시 지름!")
            st.write(random.choice(happy_quotes))
        elif mode == "팩트 폭격":
            st.subheader(f"❄️ {final_name}: 지름 금지!")
            st.write(random.choice(fact_quotes))
        elif mode == "AI 판결":
            st.subheader(f"⚖️ AI 판사님의 분석")
            target_price = final_price if final_price > 0 else 100000
            min_p = int(target_price * 0.85)
            
            st.write(f"📊 분석 상품: **{final_name}**")
            st.write(f"💰 현재가: **{target_price:,}원**")
            
            search_q = urllib.parse.quote(f"{final_name} 리뷰")
            google_url = f"https://www.google.com/search?q={search_q}"
            
            st.markdown("---")
            st.markdown(f"🌐 [{final_name} 리뷰 확인하러 가기]({google_url})")

            if target_price > min_p * 1.1:
                st.error("❌ 판결: 거품 낀 가격입니다. 사지 마세요!")
            else:
                st.success("✅ 판결: 훌륭한 가격입니다. 지르세요!")
        
        st.markdown('</div>', unsafe_allow_html=True)
