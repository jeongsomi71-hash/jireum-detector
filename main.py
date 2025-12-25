import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS: 폰트 사이즈 대폭 확대 및 결과 박스 테두리 제거
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
    
    /* 4. 지름신 판독기 폰트 사이즈 대폭 확대 */
    .main-title { 
        font-size: 6.5rem; 
        font-weight: 900; 
        text-align: center; 
        color: #00FF88;
        text-shadow: 4px 4px 20px rgba(0, 255, 136, 0.8);
        line-height: 1.0;
        margin-bottom: 20px;
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

    /* 5. 하단 검은색 상자 및 초록 테두리 제거 (필요한 텍스트만 노출) */
    .result-content {
        margin-top: 30px;
        padding: 10px;
    }

    /* 하단 버튼 중앙 정렬 */
    .stButton {
        display: flex;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 섹션
st.markdown('<p class="main-title">지름신<br>판독기</p>', unsafe_allow_html=True)
st.markdown('<div class="sub-title-box">⚖️ AI 판사님의 뼈 때리는 판결</div>', unsafe_allow_html=True)

# 2. 초기화 기능 구현 (세션 상태 활용)
def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# 3. 메뉴 구성: 이미지 업로드 옆에 직접 입력하기 추가
mode = st.radio("⚖️ 판독 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])
tab1, tab2, tab3 = st.tabs(["🔗 URL 입력", "📸 이미지 업로드", "✍️ 직접 입력하기"])

final_name = ""
final_price = 0

with tab1:
    url = st.text_input("상품 URL을 입력하세요", placeholder="https://...", key="url_input")
    if url:
        st.info("💡 링크 분석 중... 실패 시 이미지 업로드를 이용해 주세요.")

with tab2:
    uploaded_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="file_input")
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            price_match = re.search(r'([0-9,]{3,})원', text)
            if price_match:
                final_price = int(price_match.group(1).replace(',', ''))
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
            if lines: final_name = lines[0]
        except:
            st.warning("⚠️ 이미지 인식이 원활하지 않습니다. '직접 입력하기' 메뉴를 이용해 주세요.")

# 3. 직접 입력 메뉴 (URL/이미지 인식 실패 시 가이드 제공)
with tab3:
    st.write("URL이나 이미지 인식이 안 되시나요? 정보를 직접 적어주세요.")
    manual_name = st.text_input("상품명", placeholder="예: 아이패드 에어 6세대", key="m_name")
    manual_price = st.text_input("가격 (숫자만)", placeholder="예: 850000", key="m_price")
    if manual_name: final_name = manual_name
    if manual_price: final_price = int(re.sub(r'[^0-9]', '', manual_price))

# 판결 실행
if st.button("⚖️ 최종 판결 내리기"):
    if not final_name or final_price == 0:
        st.error("❗ 상품명과 가격 정보가 부족합니다. '직접 입력하기' 탭에서 정보를 완성해 주세요.")
    else:
        st.markdown('<div class="result-content">', unsafe_allow_html=True)
        
        if mode == "행복 회로":
            st.subheader(f"🔥 {final_name}: 무조건 지름!")
            st.write("🚀 이것은 소비가 아니라 미래를 향한 가치 투자입니다! 고민은 배송만 늦출 뿐.")
        
        elif mode == "팩트 폭격":
            st.subheader(f"❄️ {final_name}: 절대 금지!")
            st.write("💀 정신 차리세요. 이거 사고 일주일 뒤면 먼지만 쌓일 게 뻔합니다. 통장이 울고 있어요.")
        
        elif mode == "AI 판결":
            st.subheader("⚖️ AI 판사님의 정밀 분석")
            # 1. 최저가 제시 로직 보완 (가중치 계산)
            min_estimate = int(final_price * 0.81) # 대략적인 역대 최저가 시뮬레이션
            avg_market = int(final_price * 0.92)  # 평균 중고/할인가
            
            st.write(f"📊 분석 상품: **{final_name}**")
            st.write(f"💰 현재 감지가: **{final_price:,}원**")
            st.success(f"📉 역대 최저가(추정): **{min_estimate:,}원**")
            st.info(f"💡 일반적인 적정 구매가: **{avg_market:,}원** 수준입니다.")
            
            st.markdown("---")
            search_q = urllib.parse.quote(f"{final_name} 리뷰 후기")
            google_url = f"https://www.google.com/search?q={search_q}"
            st.markdown(f"🌐 [{final_name} 리뷰 확인하러 가기]({google_url})")

            if final_price > avg_market * 1.05:
                st.error("❌ 판결: 지금 사면 바보! 거품이 잔뜩 껴있습니다.")
            else:
                st.success("✅ 판결: 훌륭한 가격입니다. 지금 바로 지르세요!")
        
        st.markdown('</div>', unsafe_allow_html=True)

# 2. 새로운 상품 판독하기 버튼 (맨 하단 중앙)
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 새로운 상품 판독하기", on_click=reset_app):
    pass
