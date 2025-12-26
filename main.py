import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from datetime import datetime
import numpy as np

# ==========================================
# 1. 시세 분석 및 뽐뿌 구조 특화 엔진
# ==========================================
class AdvancedSearchEngine:
    @staticmethod
    def get_mobile_headers():
        return {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    @staticmethod
    def parse_ppomppu_item(soup_item):
        """뽐뿌 검색 결과에서 제목, 댓글수, 일자 추출 (닉네임 제거)"""
        try:
            # 제목 및 댓글수 (보통 '제목 [5]' 형식)
            full_text = soup_item.get_text(strip=True)
            comment_match = re.search(r'\[(\d+)\]$', full_text)
            comment_count = int(comment_match.group(1)) if comment_match else 0
            # 댓글수 대괄호 제거한 순수 제목
            title = re.sub(r'\[\d+\]$', '', full_text).strip()
            
            # 일자 추출 (뽐뿌 리스트의 정보 영역)
            info_text = soup_item.find_next('span', class_='hi') # 클래스명은 실제 구조에 따라 변동 가능성 있음
            date_text = "일자미상"
            if info_text:
                date_match = re.search(r'\d{2}/\d{2}/\d{2}', info_text.get_text())
                if date_match: date_text = date_match.group(0)
            
            return {"title": title, "comments": comment_count, "date": date_text}
        except:
            return None

    @staticmethod
    def extract_core_keyword(full_title):
        """핵심 키워드 추출"""
        clean_name = re.sub(r'\[.*?\]|\(.*?\)|\!|\?|\★|\☆', '', full_title)
        clean_name = re.sub(r'[0-9,]{4,}원|[0-9]{1,2}\/[0-9]{1,2}', '', clean_name)
        words = clean_name.split()
        return " ".join(words[:6]) if len(words) > 6 else " ".join(words)

    @staticmethod
    def search_all(product_name):
        encoded_query = urllib.parse.quote(product_name)
        url = f"https://m.ppomppu.co.kr/new/search_result.php?search_type=sub_memo&keyword={encoded_query}&category=1"
        all_data = []
        try:
            res = requests.get(url, headers=AdvancedSearchEngine.get_mobile_headers(), timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 뽐뿌 모바일 검색 결과 타이틀 클래스 선택
            items = soup.select('.title')
            for item in items:
                parsed = AdvancedSearchEngine.parse_ppomppu_item(item)
                if parsed: all_data.append(parsed)
        except: pass
        return all_data

    @staticmethod
    def categorize_deals(items, search_query, user_excludes):
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
            if num < 10000: continue 

            t_low = text.lower()
            spec_tag = "기본"
            if any(k in t_low for k in ["10인용", "10인"]): spec_tag = "10인용"
            elif any(k in t_low for k in ["6인용", "6인"]): spec_tag = "6인용"
            if "256" in t_low: spec_tag += " 256G"
            elif "512" in t_low: spec_tag += " 512G"

            if spec_tag not in categorized: categorized[spec_tag] = []
            categorized[spec_tag].append({
                "price": num, 
                "title": text, 
                "comments": item['comments'], 
                "date": item['date']
            })
        
        # 가격 역전 방지 및 정제 로직 유지
        return {k: v for k, v in categorized.items() if v}

# ==========================================
# 2. UI 및 로직 통합
# ==========================================
def apply_style():
    st.set_page_config(page_title="지름신 판독기 PRO v3.5", layout="centered")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background-color: #000000 !important; }
        .stTextInput label p { color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important; }
        .unified-header { background-color: #FFFFFF !important; color: #000000 !important; text-align: center; font-size: 1.6rem; font-weight: 900; padding: 15px; border-radius: 12px; margin-bottom: 25px; border: 4px solid #00FF88; }
        .detail-card { border: 2px solid #00FF88 !important; padding: 20px; border-radius: 12px; margin-top: 15px; background-color: #1A1A1A !important; position: relative; }
        .price-highlight { color: #00FF88 !important; font-size: 2.2rem !important; font-weight: 900 !important; float: right; }
        .core-title { color: white; font-weight: 900; font-size: 1.2rem; display: block; width: 70%; line-height: 1.3; }
        .meta-info { color: #888888; font-size: 0.8rem; margin-top: 10px; display: flex; gap: 15px; }
        .badge { background: #333; padding: 2px 8px; border-radius: 4px; color: #00FF88; font-weight: bold; }
        .judgment-box { padding: 10px; border-radius: 8px; font-weight: 900; text-align: center; margin-top: 10px; font-size: 1.1rem; }
        .stButton>button { width: 100%; border: 2px solid #00FF88 !important; background-color: #000000 !important; color: #00FF88 !important; font-weight: bold !important; height: 3.5rem; }
        </style>
        """, unsafe_allow_html=True)

def main():
    apply_style()
    if 's_name' not in st.session_state: st.session_state.s_name = ""
    if 's_price' not in st.session_state: st.session_state.s_price = ""
    if 'history' not in st.session_state: st.session_state.history = []
    if 'current_data' not in st.session_state: st.session_state.current_data = None

    st.markdown('<div class="unified-header">⚖️ 지름신 판독기 PRO <span style="font-size:0.8rem; color:#444;">v3.5</span></div>', unsafe_allow_html=True)

    in_name = st.text_input("📦 제품명 입력", value=st.session_state.s_name)
    in_price = st.text_input("💰 나의 확인가 (숫자만)", value=st.session_state.s_price)
    in_exclude = st.text_input("🚫 제외 단어", value="직구, 해외, 렌탈, 당근, 중고")

    if st.button("🔍 시세 판독 실행"):
        if in_name:
            st.session_state.s_name, st.session_state.s_price = in_name, in_price
            with st.spinner('🏘️ 댓글 및 일자 분석 중...'):
                raw_data = AdvancedSearchEngine.search_all(in_name)
                res = AdvancedSearchEngine.categorize_deals(raw_data, in_name, in_exclude)
                data = {"name": in_name, "user_price": in_price, "results": res, "time": datetime.now().strftime('%H:%M')}
                st.session_state.current_data = data
                st.session_state.history.insert(0, data)
                st.rerun()

    if st.session_state.current_data:
        d = st.session_state.current_data
        for opt_key, items in sorted(d['results'].items(), reverse=True):
            items = sorted(items, key=lambda x: x['price']) # 가격순 정렬
            best = items[0]
            avg_comments = sum(i['comments'] for i in items) / len(items)
            
            # 신뢰도 계산 (표본 수 + 평균 댓글 수 반영)
            score = len(items) * 2 + avg_comments
            rel_col = "#00FF88" if score >= 10 else "#FFD700" if score >= 5 else "#FF5555"
            rel_txt = "높음" if score >= 10 else "보통" if score >= 5 else "낮음"

            st.markdown(f'''
            <div class="detail-card">
                <span style="color:{rel_col}; font-weight:bold; font-size:0.8rem;">분석 신뢰도: {rel_txt} (관심도 점수: {score:.1f})</span><br>
                <span class="price-highlight">{best['price']:,}원</span>
                <span class="core-title">{AdvancedSearchEngine.extract_core_keyword(best['title'])}</span>
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
        st.subheader("📜 최근 판독 이력 (10개)")
        for idx, h in enumerate(st.session_state.history[:10]):
            if st.button(f"[{h['time']}] {h['name']}", key=f"hi_{idx}"):
                st.session_state.current_data = h
                st.rerun()

if __name__ == "__main__": main()