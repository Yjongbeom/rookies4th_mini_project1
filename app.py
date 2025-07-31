import streamlit as st
import pandas as pd
import re

# --- 1. 페이지 설정 ---
st.set_page_config(layout="wide")

# --- 2. 데이터 로딩 ---
@st.cache_data
def load_data(path):
    """CSV 파일을 불러와 데이터프레임으로 반환합니다."""
    df = pd.read_csv(path)
    if '장르' not in df.columns:
        df['장르'] = '기타'
    df['장르'] = df['장르'].fillna('기타').astype(str)
    # 사이트 URL 컬럼이 없을 경우를 대비
    if '사이트 URL' not in df.columns:
        df['사이트 URL'] = ''
    df['사이트 URL'] = df['사이트 URL'].fillna('')
    return df

# --- 헬퍼 함수 ---
def format_display_price(price_string):
    """가격 문자열을 보기 좋은 형식으로 변환합니다."""
    price_str = str(price_string)
    if "품절" in price_str: return "🚫 품절"
    if "무료" in price_str: return "🆓 무료"
    
    cleaned_price_str = price_str.replace('\\', '').replace(',', '').strip()
    
    try:
        price_num = float(cleaned_price_str)
        return f"₩{int(price_num):,}"
    except (ValueError, TypeError):
        return price_str

# --- 데이터 로드 ---
try:
    df = load_data("data/merged_games_data.csv")
except FileNotFoundError:
    st.error("오류: 'data/merged_games_data.csv' 파일을 찾을 수 없습니다.")
    st.info("app.py 파일과 같은 위치에 'data' 폴더를 만들고, 그 안에 CSV 파일을 넣어주세요.")
    st.stop()

# --- 데이터에서 모든 고유 장르 추출 ---
all_genres = sorted(list(df['장르'].str.split(',').explode().str.strip().unique()))

# --- 세션 상태 초기화 ---
if 'page' not in st.session_state:
    st.session_state.page = '대시보드'
if 'num_to_display' not in st.session_state:
    st.session_state.num_to_display = 20
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = df
if 'selected_game_id' not in st.session_state:
    st.session_state.selected_game_id = None

# --- 페이지 전환 함수 ---
def set_page():
    st.session_state.page = st.session_state.page_selector

def view_detail(game_id):
    st.session_state.selected_game_id = game_id
    st.session_state.page = '게임 상세'

# --- 3. 메인 UI ---
st.title("🔥 게임 할인 정보 대시보드")
st.caption("데이터는 웹 스크래핑을 기반으로 수집되었습니다.")

# --- 페이지 메뉴 생성 ---
st.radio(
    "메뉴 선택",
    ['대시보드', '전체 데이터 보기'],
    key='page_selector',
    horizontal=True,
    on_change=set_page
)

# --- 페이지 렌더링 ---
if st.session_state.page == '대시보드':
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.metric(label="총 게임 수", value=f"{df.shape[0]} 개")
    with col2:
        with st.container(border=True):
            numeric_discounts = pd.to_numeric(df['할인율'].astype(str).str.replace('%', ''), errors='coerce')
            avg_discount = numeric_discounts[numeric_discounts > 0].mean()
            st.metric(label="평균 할인율", value=f"{avg_discount:.1f} %")
    with col3:
        with st.container(border=True):
            numeric_prices = pd.to_numeric(df['할인가'].astype(str).str.replace('₩', '').str.replace('\\', '').str.replace(',', ''), errors='coerce')
            free_games = df[(df['할인가'] == '무료') | (numeric_prices == 0)].shape[0]
            st.metric(label="무료 게임 수", value=f"{free_games} 개")
            
    st.markdown("---")

    left_col, right_col = st.columns([2, 1])
    with right_col:
        st.subheader("할인 중인 게임 TOP 10")
        
        numeric_discounts = pd.to_numeric(df['할인율'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
        discounted_games_df = df[numeric_discounts > 0].head(10)

        with st.container(border=True):
            if discounted_games_df.empty:
                st.info("현재 할인 중인 게임이 없습니다.")
            else:
                for index, row in discounted_games_df.iterrows():
                    img_col, info_col, price_col = st.columns([1, 3, 1.5])
                    with img_col: 
                        st.image(row['이미지 URL'], use_container_width=True)
                    with info_col:
                        st.markdown(f"**{row['게임 이름']}**")
                        st.caption(f"플랫폼: {row['플랫폼 이름']}")
                    with price_col:
                        discount_html, price_html = "", ""
                        discount_num = pd.to_numeric(str(row['할인율']).replace('%', ''), errors='coerce')
                        if pd.notna(discount_num) and discount_num > 0:
                            discount_html = f'<span style="background-color: #d43f3a; color: white; border-radius: 5px; padding: 3px 8px; font-weight: bold; font-size: 0.9em;">-{int(discount_num)}%</span>'
                        original_price_display = format_display_price(row['원가'])
                        sales_price_display = format_display_price(row['할인가'])
                        if original_price_display != sales_price_display and '품절' not in sales_price_display:
                            price_html = f'<div style="text-align: right;"><span style="font-size: 0.8em; color: grey;"><del>{original_price_display}</del></span><br><strong style="font-size: 1.2em;">{sales_price_display}</strong></div>'
                        else:
                            price_html = f'<div style="text-align: right; font-size: 1.2em; font-weight: bold;">{sales_price_display}</div>'
                        final_html = f'<div style="display: flex; justify-content: flex-end; align-items: center; gap: 15px; height: 100%;">{discount_html}{price_html}</div>'
                        st.markdown(final_html, unsafe_allow_html=True)

elif st.session_state.page == '전체 데이터 보기':
    filter_col, list_col = st.columns([1, 3])

    with filter_col:
        with st.form(key='filter_form'):
            st.subheader("🔍 검색 및 필터")
            
            search_query = st.text_input("게임 이름으로 검색", placeholder="예: 사이버펑크 2077")
            platforms = sorted(df['플랫폼 이름'].unique())
            selected_platforms = st.multiselect("플랫폼 선택", options=platforms)
            selected_genres = st.multiselect("장르 선택", options=all_genres)
            submit_button = st.form_submit_button(label='필터 적용')

    if submit_button:
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df['게임 이름'].str.contains(search_query, case=False, na=False)]
        if selected_platforms:
            filtered_df = filtered_df[filtered_df['플랫폼 이름'].isin(selected_platforms)]
        
        if selected_genres:
            for genre in selected_genres:
                filtered_df = filtered_df[filtered_df['장르'].str.contains(re.escape(genre), case=False, na=False)]
        
        st.session_state.filtered_df = filtered_df
        st.session_state.num_to_display = 20
        st.rerun()

    with list_col:
        current_results = st.session_state.filtered_df
        st.subheader(f"검색 결과 ({len(current_results)}개)")
        
        if current_results.empty:
            st.warning("선택한 조건에 맞는 게임이 없습니다.")
        else:
            results_to_show = current_results.head(st.session_state.num_to_display)
            for index, row in results_to_show.iterrows():
                with st.container(border=True):
                    img_col, info_col, price_col = st.columns([1, 3, 1.5])
                    
                    with img_col:
                        st.image(row['이미지 URL'], use_container_width=True)
                    with info_col:
                        st.markdown(f'<h5>{row["게임 이름"]}</h5>', unsafe_allow_html=True)
                        st.caption(f"플랫폼: {row['플랫폼 이름']} | 장르: {row['장르']}")
                        st.button("상세 보기", key=f"detail_{index}", on_click=view_detail, args=(index,))

                    with price_col:
                        discount_html, price_html = "", ""
                        discount_num = pd.to_numeric(str(row['할인율']).replace('%', ''), errors='coerce')
                        if pd.notna(discount_num) and discount_num > 0:
                            discount_html = f'<span style="background-color: #d43f3a; color: white; border-radius: 5px; padding: 3px 8px; font-weight: bold; font-size: 0.9em;">-{int(discount_num)}%</span>'
                        original_price_display = format_display_price(row['원가'])
                        sales_price_display = format_display_price(row['할인가'])
                        if original_price_display != sales_price_display and '품절' not in sales_price_display:
                            price_html = f'<div style="text-align: right;"><span style="font-size: 0.8em; color: grey;"><del>{original_price_display}</del></span><br><strong style="font-size: 1.2em;">{sales_price_display}</strong></div>'
                        else:
                            price_html = f'<div style="text-align: right; font-size: 1.2em; font-weight: bold;">{sales_price_display}</div>'
                        final_html = f'<div style="display: flex; justify-content: flex-end; align-items: center; gap: 15px; height: 100%;">{discount_html}{price_html}</div>'
                        st.markdown(final_html, unsafe_allow_html=True)
            
            if len(current_results) > st.session_state.num_to_display:
                if st.button("더 보기"):
                    st.session_state.num_to_display += 20
                    st.rerun()

elif st.session_state.page == '게임 상세':
    selected_id = st.session_state.get('selected_game_id')

    if st.button("← 목록으로 돌아가기"):
        st.session_state.page = '전체 데이터 보기'
        st.rerun()

    if selected_id is None:
        st.info("'전체 데이터 보기' 페이지에서 게임을 선택해주세요.")
    else:
        game_data = df.loc[selected_id]
        
        st.header(game_data['게임 이름'])
        st.caption(f"플랫폼: {game_data['플랫폼 이름']} | 장르: {game_data['장르']}")
        st.markdown("---")

        img_col, info_col = st.columns([2, 3])

        with img_col:
            st.image(game_data['이미지 URL'], use_container_width=True)

        with info_col:
            st.subheader("가격 정보")
            
            discount_html, price_html = "", ""
            discount_num = pd.to_numeric(str(game_data['할인율']).replace('%', ''), errors='coerce')
            if pd.notna(discount_num) and discount_num > 0:
                discount_html = f'<span style="background-color: #d43f3a; color: white; border-radius: 5px; padding: 3px 8px; font-weight: bold; font-size: 0.9em;">-{int(discount_num)}%</span>'
            
            original_price_display = format_display_price(game_data['원가'])
            sales_price_display = format_display_price(game_data['할인가'])
            
            if original_price_display != sales_price_display and '품절' not in sales_price_display:
                price_html = f'<div style="text-align: left;"><span style="font-size: 1.1em; color: grey;"><del>{original_price_display}</del></span><br><strong style="font-size: 1.8em; color: #d43f3a;">{sales_price_display}</strong></div>'
            else:
                price_html = f'<div style="text-align: left; font-size: 1.8em; font-weight: bold;">{sales_price_display}</div>'
            
            final_price_html = f'<div style="display: flex; justify-content: flex-start; align-items: center; gap: 15px; height: 100%;">{price_html}{discount_html}</div>'
            st.markdown(final_price_html, unsafe_allow_html=True)
            
            st.subheader(" ")
            st.info("게임 설명란 (추후 데이터 추가 시 표시됩니다.)")

        # --- 사이트별 가격 비교 ---
        st.markdown("---")
        st.subheader("🛍️ 사이트별 가격 비교")

        game_name = game_data['게임 이름']
        related_games = df[df['게임 이름'] == game_name]

        stores_data = {
            'steam': None, 'directg': None, 'epicgames': None, 'greenmangaming': None
        }
        for _, row in related_games.iterrows():
            url = str(row.get('사이트 URL', '')).lower()
            # [수정] Direct Games URL에 'steam'이 포함된 경우를 대비해, 더 명확한 도메인으로 스토어를 구분하여 버그를 해결합니다.
            if 'directg.net' in url:
                stores_data['directg'] = row
            elif 'store.steampowered.com' in url:
                stores_data['steam'] = row
            # elif 'epicgames.com' in url:
            #     stores_data['epicgames'] = row
            # elif 'greenmangaming.com' in url:
            #     stores_data['greenmangaming'] = row

        store_display_names = {
            'steam': 'Steam', 'directg': 'Direct Games', 
            'epicgames': 'Epic Games', 'greenmangaming': 'Green Man Gaming'
        }

        for store_key, store_name in store_display_names.items():
            store_data = stores_data.get(store_key)
            
            with st.container(border=True):
                if store_data is not None:
                    original = format_display_price(store_data['원가'])
                    sales = format_display_price(store_data['할인가'])
                    discount_num = pd.to_numeric(str(store_data['할인율']).replace('%', ''), errors='coerce')
                    url = store_data['사이트 URL']

                    price_html = ""
                    if original != sales and '품절' not in sales:
                        price_html = f"<div style='text-align: right;'><span style='font-size: 0.9em; color: grey; text-decoration: line-through;'>{original}</span><br><strong style='font-size: 1.2em;'>{sales}</strong></div>"
                    else:
                        price_html = f"<div style='text-align: right; font-size: 1.2em; font-weight: bold;'>{sales}</div>"

                    discount_badge = ""
                    if pd.notna(discount_num) and discount_num > 0:
                        discount_badge = f"<span style='background-color: #d43f3a; color: white; border-radius: 5px; padding: 2px 6px; font-size: 0.8em; font-weight: bold;'>-{int(discount_num)}%</span>"
                    
                    list_item_html = f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                        <div style="flex-grow: 1;"><strong style="font-size: 1.1em;">{store_name}</strong></div>
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            {discount_badge}
                            {price_html}
                            <a href="{url}" target="_blank" style="text-decoration: none; color: white;">
                                <button style="background-color: #5B7C99; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer;">
                                    구매하기
                                </button>
                            </a>
                        </div>
                    </div>
                    """
                    st.markdown(list_item_html, unsafe_allow_html=True)
                else:
                    list_item_html = f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; opacity: 0.5;">
                        <div style="flex-grow: 1;"><strong style="font-size: 1.1em;">{store_name}</strong></div>
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <span style="color: grey;">데이터 없음</span>
                            <button disabled style="background-color: grey; color: white; padding: 8px 16px; border: none; border-radius: 5px; cursor: not-allowed;">
                                구매하기
                            </button>
                        </div>
                    </div>
                    """
                    st.markdown(list_item_html, unsafe_allow_html=True)
