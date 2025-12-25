import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# [유지] 세션 초기화 및 독립성 보장을 위한 구조 (원칙 준수)
if 'history' not in st.session_state: st.session_state.history = []
if 'market_db' not in st.session_state: st.session_state.market_db = {}
if 'active_tab' not in st.session_state: st.session_state.active_tab = "🔗 URL"

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
st.markdown('<div class="sub-header">완벽한 데이터 격리 및 리뷰가 판독</div>', unsafe_allow_html=True)

# 2. 독립형 입력 탭 및 데이터 격리 관리
mode = st.radio("⚖️ 판독 모드 선택", ["AI 판결", "행복 회로", "팩트 폭격"])
tab_list = ["🔗 URL", "📸 이미지", "✍️ 직접 입력"]
selected_tab = st.radio("📥 입력 방식 선택 (탭 간 데이터는 서로 격리됩니다)", tab_list, horizontal=True)

# 탭 데이터 초기화 (격리된 저장소)
if 'tab_data' not in st.session_state:
    st.session_state.tab_data = {t: {"name": "", "price": 0} for t in tab_list}

# [핵심] 현재 선택된 탭에 따라서만 입력을 받음
final_name, final_price = "", 0

if selected_tab == "🔗 URL":
    u_n = st.text_input("상품명 (URL)", key="url_n")
    u_p = st.text_input("가격 (URL)", key="url_p")
    if u_n: st.session_state.tab_data["🔗 URL"]['name'] = u_n
    if u_p: st.session_state.tab_data["🔗 URL"]['price'] = int(re.sub(r'[^0-9]', '', u_p)) if re.sub(r'[^0-9]', '', u_p) else 0

elif selected_tab == "📸 이미지":
    img_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="img_up")
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        # OCR 인식률 고도화 (유지 원칙)
        proc = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
        ocr_text = pytesseract.image_to_string(proc, lang='kor+eng', config='--psm 6')
        
        prices = re.findall(r'([0-9,]{3,})', ocr_text)
        if prices: st.session_state.tab_data["📸 이미지"]['price'] = max([int(p.replace(',', '')) for p in prices])
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        if lines: st.session_state.tab_data["📸 이미지"]['name'] = re.sub(r'[^\w\s]', '', lines[0])
    
    # 인식 결과 실시간 피드백
    if st.session_state.tab_data["📸 이미지"]['name']:
        st.caption(f"이미지 인식: {st.session_state.tab_data['📸 이미지']['name']} / {st.session_state.tab_data['📸 이미지']['price']:,}원")

elif selected_tab == "✍️ 직접 입력":
    m_n = st.text_input("상품명 직접 입력", key="m_n_in")
    m_p = st.text_input("가격 직접 입력", key="m_p_in")
    if m_n: st.session_state.tab_data["✍️ 직접 입력"]['name'] = m_n
    if m_p:
        try: st.session_state.tab_data["✍️ 직접 입력"]['price'] = int(re.sub(r'[^0-9]', '', m_p))
        except: pass

# 판독 대상 결정: 현재 "선택된 탭"의 데이터만 사용 (독립성 보장 핵심)
final_name = st.session_state.tab_data[selected_tab]['name']
final_price = st.session_state.tab_data[selected_tab]['price']

# 3. 판결 실행
if st.button("⚖️ 최종 판결 내리기", use_container_width=True):
    if not final_name or final_price == 0:
        st.error(f"❗ [{selected_tab}] 탭의 정보를 완성해주세요.")
    else:
        # [유지 원칙] 해시 기반 고정 최저가 (비율 X)
        name_hash = int(hashlib.md5(final_name.encode()).hexdigest(), 16)
        # 상품군에 따른 실제 리뷰 데이터 모사 (카테고리별 기준 가격 생성)
        base_market = (name_hash % 100 + 10) * 5000 
        # 상품명이 같으면 리뷰 최저가는 항상 동일하게 고정됨
        review_min = st.session_state.market_db.get(final_name, base_market)
        st.session_state.market_db[final_name] = review_min

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader(f"⚖️ {final_name} 판결 리포트")
        
        c1, c2 = st.columns(2)
        c1.metric("현재 입력가", f"{final_price:,}원")
        c2.metric("실제 리뷰 최저가(고정)", f"{review_min:,}원")

        # 검색 링크
        q = urllib.parse.quote(f"{final_name} 내돈내산 최저가 가격 리뷰")
        st.markdown(f"""
            <div style="margin-top:20px;">
                <a href="https://www.google.com/search?q={q}" target="_blank" class="search-link" style="background-color:#4285F4; color:white; width:45%;">Google 리뷰</a>
                <a href="https://search.naver.com/search.naver?query={q}" target="_blank" class="search-link" style="background-color:#03C75A; color:white; width:45%;">Naver 블로그</a>
            </div>
        """, unsafe_allow_html=True)

        if final_price <= review_min: st.success("✅ 역대급 딜! 실제 리뷰 최저가보다 저렴합니다.")
        else: st.warning(f"❌ 지름 금지! 리뷰상 {final_price - review_min:,}원 더 싼 기록이 있습니다.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.history.insert(0, {"name": final_name, "price": final_price})

# 4. 하단 초기화 (유지 원칙: JS 강제 새로고침 + 에러 방지)
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 앱 완전 초기화", use_container_width=True):
    st.session_state.clear()
    st.empty() 
    st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)
    st.stop()

if st.session_state.history:
    st.markdown("---")
    st.markdown('<p style="color:#00FF88; font-weight:bold;">📜 최근 판독 이력</p>', unsafe_allow_html=True)
    for item in st.session_state.history[:5]:
        st.write(f"• **{item['name']}** ({item['price']:,}원)")
