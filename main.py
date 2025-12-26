import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime

# ==========================================
# 1. 시세 분석 엔진 (구조적 필터링 적용)
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        sites = {
            "뽐뿌": f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=1",
            "클리앙": f"https://www.clien.net/service/search?q={encoded_query}"
        }
        all_data = []
        for name, url in sites.items():
            try:
                res = requests.get(url, headers=AdvancedSearchEngine.get_mobile_headers(), timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # [수집 범위 복구]
                if name == "뽐뿌":
                    # 뽐뿌는 .title 안에 닉네임이 섞여 있으므로 자식 태그를 제거하는 방식 사용
                    items = soup.select('.title')
                    for item in items:
                        # 닉네임이나 기타 정보가 담긴 span/em 태그 제거 (구조적 제거)
                        for extra in item.find_all(['span', 'em']):
                            extra.decompose() 
                        
                        raw_text = item.get_text(strip=True)
                        if not raw_text: continue
                        
                        # 댓글 수 추출 [00]
                        comment_match = re.search(r'\[(\d+)\]$', raw_text)
                        comment_count = int(comment_match.group(1)) if comment_match else 0
                        pure_title = re.sub(r'\[\d+\]$', '', raw_text).strip()
                        
                        # 일자 정보 가져오기
                        date_text = datetime.now().strftime('%y/%m/%d')
                        info_row = item.find_next('span', class_='hi')
                        if info_row:
                            d_match = re.search(r'\d{2}/\d{2}/\d{2}', info_row.get_text())
                            if d_match: date_text = d_match.group(0)
                        
                        all_data.append({"title": pure_title, "comments": comment_count, "date": date_text})
                
                else: # 클리앙
                    items = soup.select('.list_subject .subject_fixed')
                    for item in items:
                        raw_text = item.get_text(strip=True)
                        comment_match = re.search(r'\[(\d+)\]$', raw_text)
                        comment_count = int(comment_match.group(1)) if comment_match else 0
                        pure_title = re.sub(r'\[\d+\]$', '', raw_text).strip()
                        all_data.append({"title": pure_title, "comments": comment_count, "date": "클리앙"})
            except: continue
        return all_data

    @staticmethod
    def summarize_sentiment(items):
        if not items: return "데이터 부족"
        pos_k, neg_k = ["역대급", "최저가", "좋네요", "가성비", "지름", "추천"], ["품절", "종료", "비싸", "아쉽", "비추"]
        txt = " ".join([i['title'] for i in items])
        p, n = sum(1 for k in pos_k if k in txt), sum(1 for k in neg_k if k in txt)
        if p > n: return "🔥 **긍정**: 실구매자 반응이 좋고 가성비가 뛰어납니다."
        if n > p: return "🧊 **주의**: 가격이 올랐거나 이미 품절된 경우가 많습니다."
        return "💬 **안정**: 현재 시세는 평이하며 재고가 안정적입니다."

    @staticmethod
    def categorize_deals(items, user_excludes):
        base_excludes = ["중고", "사용감", "리퍼", "S급", "민팃", "삽니다", "매입"]
        total_excludes = base_excludes + [x.strip() for x in user_excludes.split(',') if x.strip()]
        exclude_pattern = re.compile('|'.join(map(re.escape, total_excludes)))
        price_pattern = re.compile(r'([0-9,]{1,10})\s?(원|만)')
        
        categorized = {}
        for item in items:
            text = item['title']
            if exclude_pattern.search(text): continue
            found = price_pattern.findall(text)
            if not found: continue
            
            num = int(found[0][0].replace(',', ''))
            if found[0][1] == '만': num *= 10000
            if num < 5000: continue 

            t_low = text.lower()
            spec_tag = "일반"
            if any(k in t_low for k in ["10인용", "10인"]): spec_tag = "10인용"
            elif any(k in t_low for k in ["6인용", "6인"]): spec_tag = "6인용"
            if "256" in t_low: spec_tag += " 256G"
            elif "512" in t_low: spec_tag += " 512G"

            if spec_tag not in categorized: categorized[spec_tag] = []
            categorized[spec_tag].append({
                "price": num, "title": text, "comments": item['comments'], "date": item['date']
            })
        return {k: v for k, v in categorized.items() if v}

# ==========================================
# 2. UI 및 메인 로직
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v4.1", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .stTextInput label p { color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; }
        .price-highlight { color: #00FF88 !important; font-size: 2.2rem !important; font-weight: 900 !important; float: right; }
        .core-title { color: white; font-weight: 900; font-size: 1.1rem; display: block; width: 70%; line-height: 1.3; }
        .meta-info { color: #888888; font-size: 0.8rem; margin-top: 10px; display: flex; gap: 12px; }
        .badge { background: #333; padding: 2px 8px; border-radius: 4px; color: #00FF88; font-weight: bold; }
        .judgment-box { padding: 10px; border-radius: 8px; font-weight: 900; text-align: center; margin-top: 10px; font-size: 1.1rem; }
        .stButton>button { width: 100%; border: 2px solid #00FF88 !important; background-color: #000000 !important; color: #00FF88 !important; font-weight: bold !important; height: 3.5rem; }
        .version-footer { text-align: center; color: #444444; font-size: 0.8rem; margin-top: 50px; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 's_name' not in st.session_state: st.session_state.s_name = ""
    if 's_price' not in st.session_state: st.session_state.s_price = ""
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span style="font-size:0.8rem; color:#444;">v4.1</span></div>', unsafe_allow_html=True)

    in_name = st.text_input("📦 제품명 입력", value=st.session_state.s_name)
    in_price = st.text_input("💰 나의 확인가 (숫자만)", value=st.session_state.s_price)
    in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고")

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("🔍 시세 판독 실행"):
            if in_name:
                st.session_state.s_name, st.session_state.s_price = in_name, in_price
                with st.spinner('🏘️ 닉네임 제거 및 데이터 복구 중...'):
                    raw = AdvancedSearchEngine.search_all(in_name)
                    res = AdvancedSearchEngine.categorize_deals(raw, in_exclude)
                    summ = AdvancedSearchEngine.summarize_sentiment(raw)
                    data = {"name": in_name, "user_price": in_price, "results": res, "summary": summ, "time": datetime.now().strftime('%H:%M')}
                    st.session_state.current_data = data
                    st.session_state.history = [h for h in st.session_state.history if h['name'] != in_name]
                    st.session_state.history.insert(0, data)
                    st.rerun()
    with c2:
        if st.button("🔄 리셋"):
            st.session_state.s_name, st.session_state.s_price, st.session_state.current_data = "", "", None
            st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        st.info(d["summary"])
        for opt_key, items in sorted(d['results'].items(), reverse=True):
            items = sorted(items, key=lambda x: x['price'])
            best = items[0]
            avg_c = sum(i['comments'] for i in items) / len(items)
            
            # [신뢰도 등급 로직]
            score = len(items) * 1.5 + avg_c
            if score >= 10: rel_txt, rel_col = "높음", "#00FF88"
            elif score >= 5: rel_txt, rel_col = "보통", "#FFD700"
            else: rel_txt, rel_col = "낮음", "#FF5555"

            st.markdown(f'''
            <div class="detail-card">
                <span style="color:{rel_col}; font-weight:bold; font-size:0.8rem;">신뢰도: {rel_txt} (점수: {score:.1f})</span><br>
                <span class="price-highlight">{best['price']:,}원</span>
                <span class="core-title">{best['title']}</span>
                <div class="meta-info">
                    <span>📅 {best['date']}</span>
                    <span>💬 댓글 <span class="badge">{best['comments']}</span></span>
                    <span>🏷️ {opt_key}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            if d['user_price'].isdigit():
                diff = int(d['user_price']) - best['price']
                if diff <= 0: st.markdown('<div class="judgment-box" style="background:#004d40; color:#00FF88;">✅ 즉시 지르세요!</div>', unsafe_allow_html=True)
                else: st.markdown(f'<div class="judgment-box" style="background:#4d0000; color:#FF5555;">❌ 차액 {diff:,}원 발생</div>', unsafe_allow_html=True)

    if st.session_state.history:
        st.write("---")
        st.subheader("📜 최근 판독 이력")
        for idx, h in enumerate(st.session_state.history[:10]):
            if st.button(f"[{h['time']}] {h['name']}", key=f"hi_{idx}"):
                st.session_state.current_data = h
                st.session_state.s_name, st.session_state.s_price = h['name'], h['user_price']
                st.rerun()

    st.markdown('<div class="version-footer">Version: v4.1 - Tag Decompose Fix & Search Restored</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()