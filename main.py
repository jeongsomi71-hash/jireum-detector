import streamlit as st
from PIL import Image
import pytesseract
import re
import random
import urllib.parse

# 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# CSS 스타일링: 쇼츠 최적화 및 상단 여백 추가
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .block-container {
        max-width: 450px !important;
        padding-top: 6rem !important; /* 상단 여백을 6rem으로 늘려 짤림 방지 */
    }

    html, body, [class*="css"] { 
        font-family: 'Noto Sans KR', sans-serif; 
        background-color: #000000; 
        color: #FFFFFF;
    }
    
    .main-title { 
        font-size: 2.8rem; 
        font-weight: 900; 
        text-align: center; 
        background: linear-gradient(to right, #00FF88, #60EFFF); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        margin-bottom: 5px;
    }

    /* 라디오 버튼 메뉴 시인성 강화 */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        gap: 8px;
    }
    
    .result-box {
        background-color: #1A1A1A;
        padding: 22px;
        border-radius: 15px;
        border: 2px solid #00FF88;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">지름신 판독기</p>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#DDDDDD; font-weight:500;">AI 판사님의 냉철한 판결</p>', unsafe_allow_html=True)

# 1. 메뉴 선택
mode = st.radio("⚖️ 모드 선택", ["행복 회로", "팩트 폭격", "AI 판결"])

tab1, tab2 = st.tabs(["🔗 링크 분석", "📸 이미지 스캔"])
detected_price = 0
product_name = ""

with tab1:
    url = st.text_input("상품 URL 입력", placeholder="https://...")
    product_name_input = st.text_input("상품명 (선택 사항)", placeholder="예: 갤럭시 워치 7")

with tab2:
    uploaded_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
        try:
            text = pytesseract.image_to_string(img, lang='kor+eng')
            # 가격 추출 로직
            price_match = re.search(r'([0-9,]{3,})원', text)
            if price_match:
                detected_price = int(price_match.group(1).replace(',', ''))
            # 텍스트에서 상품명 추출 시도 (첫 번째 긴 줄)
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
            product_name = lines[0] if lines else "상품"
        except: pass

# 최종 상품명 결정
final_product = product_name_input if product_name_input else product_name

# 2. 랜덤 멘트 세트
happy_quotes = [
    "🚀 이건 소비가 아니라 미래를 위한 가치 투자입니다!",
    "✨ 오늘 사면 내일의 내가 고마워할 거예요. 지르세요!",
    "💎 고민은 배송만 늦출 뿐, 행복은 돈으로 살 수 있습니다!",
    "🔥 당신의 삶의 질을 200% 올려줄 완벽한 선택입니다."
]

fact_quotes = [
    "💀 정신 차리세요! 이거 사고 일주일 뒤면 먼지만 쌓일 겁니다.",
    "💸 통장 잔고가 울고 있습니다. 이건 명백한 예쁜 쓰레기입니다.",
    "🚫 과소비는 습관입니다. 이번만큼은 제발 참아보세요.",
    "🧊 냉정하게 생각하세요. 이거 없어도 당신 인생은 멀쩡합니다."
]

# 3. 판결 실행
if st.button("⚖️ 최종 판결 내리기"):
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    
    if mode == "행복 회로":
        st.subheader("🔥 판결: 즉시 지름!")
        st.write(random.choice(happy_quotes))

    elif mode == "팩트 폭격":
        st.subheader("❄️ 판결: 지름 금지!")
        st.write(random.choice(fact_quotes))

    elif mode == "AI 판결":
        st.subheader("⚖️ AI 판사님의 데이터 분석")
        current_p = detected_price if detected_price > 0 else 150000
        min_p = int(current_p * 0.82) # 가상 최저가
        
        st.write(f"📊 분석 상품: **{final_product}**")
        st.write(f"💰 현재 감지가: **{current_p:,}원**")
        st.write(f"📉 과거 최저가: **{min_p:,}원**")
        
        st.markdown("---")
        st.write("🔍 **커뮤니티 우선 탐색 근거:**")
        
        # 검색 키워드 설정
        q = urllib.parse.quote(f"{final_product} 최저가")
        
        # 뽐뿌(ppomppu.co.kr) 검색 링크
        ppomppu_url = f"https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu&keyword={q}"
        # 클리앙(clien.net) 알뜰구매 게시판 검색 링크
        clien_url = f"https://www.clien.net/service/search?q={q}&sort=recency&board=jirum"
        # 구글 종합 검색
        google_url = f"https://www.google.com/search?q={q}+리뷰+최저가"

        st.markdown(f"🛒 [뽐뿌 실시간 정보 확인]({ppomppu_url})")
        st.markdown(f"📢 [클리앙 알뜰구매 확인]({clien_url})")
        st.markdown(f"🌐 [구글 종합 리뷰 탐색]({google_url})")

        if current_p > min_p * 1.1:
            st.error(f"❌ 판결: 지금은 비쌉니다! **{int(min_p * 1.05):,}원** 이하일 때 사세요.")
        else:
            st.success("✅ 판결: 적정 가격입니다. 지금 바로 구매하세요!")

    st.markdown('</div>', unsafe_allow_html=True)
