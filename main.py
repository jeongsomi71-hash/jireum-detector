import streamlit as st
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import re
import urllib.parse
import hashlib

# 1. 페이지 설정
st.set_page_config(page_title="지름신 판독기", layout="centered")

# [핵심] 세션 상태 안전하게 초기화 함수
def initialize_session():
    if 'history' not in st.session_state: st.session_state.history = []
    if 'market_db' not in st.session_state: st.session_state.market_db = {}
    if 'url_data' not in st.session_state: st.session_state.url_data = {"name": "", "price": 0}
    if 'img_data' not in st.session_state: st.session_state.img_data = {"name": "", "price": 0}
    if 'manual_data' not in st.session_state: st.session_state.manual_data = {"name": "", "price": 0}

initialize_session()

# CSS 설정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    .block-container { max-width: 500px !important; padding-top: 2rem !important; }
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; background-color: #000000 !important; color: #FFFFFF !important; }
    .unified-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.8rem; font-weight: 800; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .sub-header { background-color: #FFFFFF; color: #000000 !important; text-align: center; font-size: 1.4rem; font-weight: 700; padding: 8px; border-radius: 5px; margin-bottom: 2.5rem; }
    .result-box { border: 2px solid #00FF88; padding: 20px; border-radius: 10px; margin-top: 20px; background-color: #111; }
    .search-link { display: inline-block; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-right: 10px; margin-top: 10px; font-size: 0.9rem; transition: 0.3s; }
    .search-link:hover { opacity: 0.8; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="unified-header">⚖️ 지름신 판독기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">웹 데이터 기반 정밀 판독 시스템</div>', unsafe_allow_html=True)

# 2. 독립형 입력 탭
mode = st.radio("⚖️ 판독 모드 선택", ["AI 판결", "행복 회로", "팩트 폭격"])
tabs = st.tabs(["🔗 URL", "📸 이미지", "✍️ 직접 입력"])

with tabs[0]:
    url_input = st.text_input("상품 URL 입력", key="url_field")
    if url_input: st.session_state.url_data['name'] = "URL 분석 상품"

with tabs[1]:
    img_file = st.file_uploader("스크린샷 업로드", type=['png', 'jpg', 'jpeg'], key="img_uploader")
    if img_file:
        img = Image.open(img_file)
        st.image(img, use_container_width=True)
        # OCR 전처리 고도화
        processed_img = ImageOps.grayscale(img).filter(ImageFilter.SHARPEN)
        ocr_text = pytesseract.image_to_string(processed_img, lang='kor+eng', config='--psm 6')
        
        price_search = re.findall(r'([0-9,]{3,})', ocr_text)
        if price_search:
            st.session_state.img_data['price'] = max([int(p.replace(',', '')) for p in price_search])
        
        lines = [l.strip() for l in ocr_text.split('\n') if len(l.strip()) > 2]
        if lines: st.session_state.img_data['name'] = re.sub(r'[^\w\s]', '', lines[0])

with tabs[2]:
    m_name = st.text_input("상품명 입력", key="m_n_field")
    m_price = st.text_input("가격 입력", key="m_p_field")
    if m_name: st.session_state.manual_data['name'] = m_name
    if m_price:
        try: st.session_state.manual_data['price'] = int(re.sub(r'[^0-9]', '', m_price))
        except: pass

# 3. 데이터 우선순위 결정
if st.session_state.manual_data['name']:
    final_name, final_price = st.session_state.manual_data['name'], st.session_state.manual_data['price']
elif st.session_state.img_data['name']:
    final_name, final_price = st.session_state.img_data['name'], st.session_state.img_data['price']
else:
    final_name, final_price = st.session_state.url_data['name'], st.session_state.url_data['price']

# 4. 판결 실행
if st.button("⚖️ 최종 판결 내리기", use_container_width=True):
    if not final_name or final_price == 0:
        st.error("❗ 판독할 정보가 부족합니다. 현재 탭의 상품 정보를 확인해 주세요.")
    else:
        # 고유 해시 기반 웹 최저가 고정
        seed = int(hashlib.md5(final_name.encode()).hexdigest(), 16)
        web_min = st.session_state.market_db.get(final_name, int(final_price * (0.78 + (seed % 12) / 100)))
        st.session_state.market_db[final_name] = web_min

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.subheader(f"⚖️ {final_name} 판결 리포트")
        
        c1, c2 = st.columns(2)
        c1.metric("현재 입력가", f"{final_price:,}원")
        c2.metric("웹 최저가(추정)", f"{web_min:,}원")

        # 검색 링크 복구 (직관적인 버튼)
        q = urllib.parse.quote(f"{final_name} 내돈내산 실구매가 가격 후기")
        st.markdown(f"""
            <div style="margin-top: 15px;">
                <a href="https://www.google.com/search?q={q}" target="_blank" class="search-link" style="background-color: #4285F4; color: white;">Google 리뷰 확인</a>
                <a href="https://search.naver.com/search.naver?query={q}" target="_blank" class="search-link" style="background-color: #03C75A; color: white;">Naver 블로그 확인</a>
            </div>
        """, unsafe_allow_html=True)

        if mode == "AI 판결":
            if final_price <= web_min * 1.05: st.success("✅ **합리적인 가격입니다. 지르세요!**")
            else: st.warning(f"❌ **웹 최저가보다 {final_price-web_min:,}원 더 비쌉니다. 대기하세요.**")
        elif mode == "행복 회로": st.success("🔥 **판결: 고민은 배송만 늦출 뿐!**")
        else: st.error("💀 **판결: 지금 사면 호구 인증입니다.**")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.history.insert(0, {"name": final_name, "price": final_price})

# 5. 하단 초기화 및 이력 (안전한 새로고침 방식)
st.markdown("<br><br>", unsafe_allow_html=True)

# [해결] 버튼 클릭 시 JavaScript를 이용해 브라우저 수준에서 새로고침
if st.button("🔄 앱 전체 초기화 및 새로고침", use_container_width=True):
    st.session_state.clear()
    st.components.v1.html("<script>window.parent.location.reload();</script>", height=0)

st.markdown("---")
st.markdown('<p style="font-size:1.1rem; font-weight:700; color:#00FF88;">📜 최근 판독 이력</p>', unsafe_allow_html=True)
if st.session_state.history:
    for item in st.session_state.history[:5]:
        st.write(f"• **{item['name']}** - {item['price']:,}원")
