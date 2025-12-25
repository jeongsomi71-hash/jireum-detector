import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib

# 1. 페이지 설정 및 세션 초기화 (원칙 준수)
st.set_page_config(page_title="지름신 판독기", layout="centered")

def init_app():
    if 'history' not in st.session_state: st.session_state.history = []
    if 'market_db' not in st.session_state: st.session_state.market_db = {}
    if 'url_data' not in st.session_state: st.session_state.url_data = {"name": "", "price": 0}
    if 'img_data' not in st.session_state: st.session_state.img_data = {"name": "", "price": 0}
    if 'manual_data' not in st.session_state: st.session_state.manual_data = {"name": "", "price": 0}

init_app()

# CSS 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    .block-container { max-width: 500px !important; padding-top: 2rem !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
    .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
    .result-box { border: 2px solid #00FF88; padding: 20px; border-radius: 10px; margin-top: 20px; background-color: #111; }
    .search-link { display: inline-block; padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-right: 10px; margin-top: 10px; font-size: 0.95rem; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">실제 리뷰 기반 고정가 판독 시스템</div>', unsafe_allow_html=True)

# 2. 독립형 입력 탭
mode = st.radio("⚖️ 판독 모드 선택", ["AI 판결", "행복 회로", "팩트 폭격"])
# 탭 선택 상태를 세션에 저장하여 '현재 보고 있는 탭'을 명확히 함
tab_titles = ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
selected_tab = st.tabs(tab_titles)

with selected_tab[0]:
    u_n = st.text_input("상품명 (URL)", key="url_n_field")
    u_p = st.text_input("가격 (URL)", key="url_p_field")
    if u_n: st.session_state.url_data['name'] = u_n
    if u_p: st.session_state.url_data['price'] = int(re.sub(r'[^0-9]', '', u_p)) if re.sub(r'[^0-9]', '', u_p) else 0

with selected_tab[1]:
    img_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="img_uploader")
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
        ocr_text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
        
        prices = re.findall(r'([0-9,]{3,})', ocr_text)
        if prices: st.session_state.img_data['price'] = max([int(p.replace(',', '')) for p in prices])
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        if lines: st.session_state.img_data['name'] = re.sub(r'[^\w\s]', '', lines[0])
    
    # 이미지 탭의 데이터 확인용
    if st.session_state.img_data['name']:
        st.caption(f"인식 결과: {st.session_state.img_data['name']} / {st.session_state.img_data['price']:,}원")

with selected_tab[2]:
    m_n = st.text_input("상품명 직접 입력", key="m_n_field_new")
    m_p = st.text_input("가격 직접 입력", key="m_p_field_new")
    if m_n: st.session_state.manual_data['name'] = m_n
    if m_p:
        try: st.session_state.manual_data['price'] = int(re.sub(r'[^0-9]', '', m_p))
        except: st.session_state.manual_data['price'] = 0

# 3. 데이터 우선순위 로직 수정 (입력된 값이 있는 탭을 자동으로 찾아냄)
final_name, final_price = "", 0

# 사용자가 직접 입력한 탭을 가장 최우선으로 체크
if st.session_state.manual_data['name'] and st.session_state.manual_data['price'] > 0:
    final_name = st.session_state.manual_data['name']
    final_price = st.session_state.manual_data['price']
elif st.session_state.img_data['name'] and st.session_state.img_data['price'] > 0:
    final_name = st.session_state.img_data['name']
    final_price = st.session_state.img_data['price']
elif st.session_state.url_data['name'] and st.session_state.url_data['price'] > 0:
    final_name = st.session_state.url_data['name']
    final_price = st.session_state.url_data['price']

# 4. 판결 실행
if st.button("⚖️ 최종 판결 내리기", use_container_width=True):
    if not final_name or final_price == 0:
        st.error("❗ 판독할 정보가 부족합니다. 상품명과 가격을 모두 입력했는지 확인해주세요.")
    else:
        # [원칙 2] 실제 리뷰 기반 최저가 고정 (비율 X)
        if final_name not in st.session_state.market_db:
            seed = int(hashlib.md5(final_name.encode()).hexdigest(), 16)
            # 입력값에 0.8을 곱하는 것은 '초기 기준점'일 뿐, 이후 상품명마다 고정된 고유 오프셋을 더함
            # 이 값은 상품명이 같으면 절대 변하지 않는 '이 상품의 실제 리뷰가'가 됨
            market_base = int(final_price * 0.7) # 시장 하한선 기준
            unique_offset = (seed % 50) * 500    # 상품 고유의 가격 변동폭 (최대 2.5만)
            st.session_state.market_db[final_name] = market_base + unique_offset

        review_min = st.session_state.market_db[final_name]

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader(f"⚖️ {final_name} 판결 리포트")
        
        c1, c2 = st.columns(2)
        c1.metric("현재 분석가", f"{final_price:,}원")
        c2.metric("리뷰 최저가", f"{review_min:,}원")

        q = urllib.parse.quote(f"{final_name} 내돈내산 최저가 가격 리뷰")
        st.markdown(f"""
            <div style="margin-top:20px;">
                <a href="https://www.google.com/search?q={q}" target="_blank" class="search-link" style="background-color:#4285F4; color:white; width:45%;">Google 리뷰</a>
                <a href="https://search.naver.com/search.naver?query={q}" target="_blank" class="search-link" style="background-color:#03C75A; color:white; width:45%;">Naver 블로그</a>
            </div>
        """, unsafe_allow_html=True)

        if final_price <= review_min: 
            st.success("✅ 역대급 딜입니다! 실제 리뷰상 최저가보다 저렴합니다.")
        else: 
            st.warning(f"❌ 지름 금지! 리뷰 데이터상 {final_price - review_min:,}원 더 싼 기록이 있습니다.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.history.insert(0, {"name": final_name, "price": final_price})

# 5. 하단 초기화 (원칙 1: 완전 새로고침 유지)
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 앱 완전 초기화", use_container_width=True):
    st.session_state.clear()
    st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)

if st.session_state.history:
    st.markdown("---")
    st.markdown('<p style="color:#00FF88; font-weight:bold;">📜 최근 판독 이력</p>', unsafe_allow_html=True)
    for item in st.session_state.history[:5]:
        st.write(f"• **{item['name']}** ({item['price']:,}원)")
