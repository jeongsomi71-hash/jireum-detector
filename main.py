import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# ==========================================
# 1. 구글 스니펫 실시간 분석 엔진
# ==========================================
class GoogleSnippetEngine:
    @staticmethod
    def get_real_market_price(product_name):
        """구글 검색 결과 스니펫에서 실시간 시세를 정밀 추출"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 검색 쿼리: 상품명 + 최저가
        query = urllib.parse.quote(f"{product_name} 최저가")
        url = f"https://www.google.com/search?q={query}"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 구글 검색 결과 텍스트 블록(스니펫) 추출
            # 클래스명은 구글 정책에 따라 변할 수 있으나 보통 VwiC3b 등을 사용
            snippets = soup.find_all("div", class_=re.compile("VwiC3b|yXMvU|MUwYbd"))
            
            price_list = []
            for s in snippets:
                text = s.get_text()
                # 텍스트 내에서 '1,230,000원' 또는 '1,230,000' 형태의 숫자 추출
                found = re.findall(r'([0-9,]{4,})\s?원?', text)
                for f in found:
                    price_val = int(f.replace(',', ''))
                    # 5,000원 이하는 부품/중고일 확률이 높으므로 필터링
                    if price_val > 5000:
                        price_list.append(price_val)
            
            if price_list:
                # 추출된 가격 중 최저값을 기준으로 산정 (가장 보수적인 판결을 위해)
                return min(price_list)
        except Exception:
            return None
        return None

# ==========================================
# 2. 메인 UI 및 판결 로직
# ==========================================
def main():
    st.set_page_config(page_title="지름신 판독기 PRO", layout="centered")
    
    # [꿀팁 1 반영] 하단 출처 명시를 포함한 헤더 스타일
    st.markdown("""
        <style>
        .main-header { background-color: #4285F4; color: white; text-align: center; padding: 20px; border-radius: 12px; font-weight: 900; }
        .source-info { font-size: 0.8rem; color: #666; text-align: center; margin-top: 5px; }
        .result-card { border: 2px solid #4285F4; padding: 25px; border-radius: 15px; margin-top: 20px; background-color: #f8f9fa; color: #333; }
        .price-label { font-size: 0.9rem; color: #555; }
        .price-val { font-size: 1.8rem; font-weight: 800; color: #4285F4; }
        .redirect-btn { display: block; width: 100%; background-color: #03C75A; color: white !important; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 15px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">⚖️ 지름신 판독기 PRO</div>', unsafe_allow_html=True)
    st.markdown('<p class="source-info">※ 본 서비스는 Google 검색 데이터를 실시간 분석한 시세를 제공합니다.</p>', unsafe_allow_html=True)

    # 입력 섹션
    name_input = st.text_input("🔍 분석할 상품명을 입력하세요", placeholder="예: 아이폰 15 프로 128GB")
    price_input = st.text_input("💰 내가 본 가격", placeholder="숫자만 입력")

    if st.button("🚀 실시간 시세 분석 및 판결", use_container_width=True):
        if name_input and price_input:
            user_price = int(re.sub(r'[^0-9]', '', price_input))
            
            with st.spinner('🌐 구글 시세 데이터를 실시간 분석 중...'):
                real_low = GoogleSnippetEngine.get_real_market_price(name_input)
            
            if real_low:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.subheader(f"📊 '{name_input}' 분석 결과")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p class="price-label">나의 입력가</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="price-val">{user_price:,}원</p>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<p class="price-label">실시간 최저가(추정)</p>', unsafe_allow_html=True)
                    st.markdown(f'<p class="price-val">{real_low:,}원</p>', unsafe_allow_html=True)
                
                diff = user_price - real_low
                st.markdown("---")
                
                if user_price <= real_low:
                    st.success("🔥 **판결: 역대급 딜!** 검색된 최저가보다 저렴합니다. 당장 사세요!")
                elif user_price <= real_low * 1.1:
                    st.info("✅ **판결: 적정 가격.** 온라인 시세 범위 내에 있습니다.")
                else:
                    st.error(f"💀 **판결: 호구 주의!** 실시간 최저가보다 {diff:,}원 더 비쌉니다.")
                
                # [꿀팁 2 반영] 리다이렉트 상생 버튼
                q_enc = urllib.parse.quote(name_input)
                st.markdown(f'<a href="https://search.shopping.naver.com/search/all?query={q_enc}" target="_blank" class="redirect-btn">🛒 네이버 쇼핑에서 실제 최저가 상품 보러가기</a>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 실시간 시세 파악이 어렵습니다. 상품명을 브랜드와 함께 더 정확하게 입력해주세요.")
        else:
            st.error("❗ 상품명과 가격을 모두 입력해주세요.")

if __name__ == "__main__":
    main()
