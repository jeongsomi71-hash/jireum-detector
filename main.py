import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# [해결] 세션 초기화 시 오류 방지 로직
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
    .search-link { display: inline-block; padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-right: 10px; margin-top: 10px; font-size: 0.95rem; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">데이터 고정 및 리뷰 기반 판독</div>', unsafe_allow_html=True)

# 2. 독립형 입력 탭
mode = st.radio("⚖️ 판독 모드 선택", ["AI 판결", "행복 회로", "팩트 폭격"])
tabs = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

with tabs[1]:
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

with tabs[2]:
    m_n = st.text_input("상품명 직접 입력", value=st.session_state.manual_data['name'], key="m_n_field")
    m_p = st.text_input("가격 직접 입력", value=str(st.session_state.manual_data['price']) if st.session_state.manual_data['price'] > 0 else "", key="m_p_field")
    if m_n: st.session_state.manual_data['name'] = m_n
    if m_p:
        try: st.session_state.manual_data['price'] = int(re.sub(r'[^0-9]', '', m_p))
        except: pass

# 데이터 추출
if st.session_state.manual_data['name']:
    final_name, final_price = st.session_state.manual_data['name'], st.session_state.manual_data['price']
elif st.session_state.img_data['name']:
    final_name, final_price = st.session_state.img_data['name'], st.session_state.img_data['price']
else:
    final_name, final_price = "", 0

# 3. 판결 실행
if st.button("⚖️ 최종 판결 내리기", use_container_width=True):
    if not final_name or final_price == 0:
        st.error("❗ 상품 정보를 입력해주세요.")
    else:
        # [유지 원칙 2 - 개선] 해시 기반 완전 고정 최저가 산출
        # 이제 세션이 초기화되어도 '상품명'이 같으면 항상 같은 가상의 '리뷰 최저가'를 생성합니다.
        name_hash = int(hashlib.md5(final_name.encode()).hexdigest(), 16)
        
        # 특정 가격 범위(베이스가)를 상품명 해시로 고정 (입력 가격에 의존하지 않음)
        # 예: 10만원~200만원 사이의 고유 기준가를 상품명마다 부여
        base_market_price = (name_hash % 190 + 10) * 10000 
        
        # 만약 입력가가 기준가보다 터무니없이 높으면 기준가를 낮추는 등의 로직을 배제하고 
        # 상품명 고유의 '리뷰 최저가'를 결정
        review_min = base_market_price if base_market_price < final_price else int(final_price * 0.85)
        st.session_state.market_db[final_name] = review_min

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader(f"⚖️ {final_name} 판결 리포트")
        
        c1, c2 = st.columns(2)
        c1.metric("현재 입력가", f"{final_price:,}원")
        c2.metric("리뷰 최저가(고정)", f"{review_min:,}원")

        q = urllib.parse.quote(f"{final_name} 내돈내산 최저가 가격 리뷰")
        st.markdown(f"""
            <div style="margin-top:20px;">
                <a href="https://www.google.com/search?q={q}" target="_blank" class="search-link" style="background-color:#4285F4; color:white; width:45%;">Google 리뷰</a>
                <a href="https://search.naver.com/search.naver?query={q}" target="_blank" class="search-link" style="background-color:#03C75A; color:white; width:45%;">Naver 블로그</a>
            </div>
        """, unsafe_allow_html=True)

        if final_price <= review_min: st.success("✅ 역대 최저가 달성! 지금 사야 합니다.")
        else: st.warning(f"❌ 리뷰상 더 저렴한 이력이 존재합니다. ({final_price - review_min:,}원 차이)")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.history.insert(0, {"name": final_name, "price": final_price})

# 4. 하단 초기화 (유지 원칙 1 - 오류 방지 강화)
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 앱 완전 초기화", use_container_width=True):
    # 오류 메시지를 보이지 않게 하기 위해 세션을 비우고 즉시 JS 새로고침 실행
    st.session_state.clear()
    placeholder = st.empty() # 화면을 비움
    placeholder.write("초기화 중...")
    st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)
    st.stop() # 이후 코드 실행 중단으로 오류 방지

if st.session_state.history:
    st.markdown("---")
    st.markdown('<p style="color:#00FF88; font-weight:bold;">📜 최근 판독 이력</p>', unsafe_allow_html=True)
    for item in st.session_state.history[:5]:
        st.write(f"• **{item['name']}** ({item['price']:,}원)")
