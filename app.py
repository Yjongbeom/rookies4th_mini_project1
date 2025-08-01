import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go

# --- HTML 태그 제거 함수 ---
def remove_html_tags(text):
    """문자열에서 HTML 태그를 제거합니다."""
    if isinstance(text, str):
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    return str(text)

def clean_game_name_final(name):
    """
    게임 이름 문자열을 최종 클리닝하는 함수:
    - 모두 소문자로 변환
    - '&'를 'and'로 변환
    - 띄어쓰기를 하이픈으로 변환
    - 영어 소문자, 숫자, 하이픈 외 모든 문자 제거
    - 연속된 하이픈 합치기 및 불필요한 하이픈 제거
    """
    # 0. 입력값이 NaN일 경우 빈 문자열로 처리
    if pd.isna(name):
        return ""
        
    # 문자열로 변환하고 모두 소문자로 변경
    cleaned_name = str(name).lower()

    # 1. '&' 기호를 'and'로 변환 (먼저 처리)
    cleaned_name = cleaned_name.replace('&', 'and')

    # 2. 띄어쓰기(' ')를 하이픈('-')으로 변환
    cleaned_name = cleaned_name.replace(' ', '-')

    # 3. 영어 소문자, 숫자, 하이픈('-')을 제외한 모든 문자 제거
    cleaned_name = re.sub(r'[^a-z0-9-]', '', cleaned_name)

    # 4. 연속으로 나타나는 하이픈을 하나로 줄이기 (예: 'metal--gear' -> 'metal-gear')
    cleaned_name = re.sub(r'-+', '-', cleaned_name)
    
    # 5. 문장 시작/끝에 불필요하게 붙는 하이픈 제거 (예: '-metal-gear-' -> 'metal-gear')
    cleaned_name = cleaned_name.strip('-')
    
    # 6. 마지막으로, 혹시 남아있을 수 있는 공백 제거 (trim)
    cleaned_name = cleaned_name.strip()

    return cleaned_name

def visualize(game_data):
    # '할인 시작일'를 datetime 형식으로 변환
    game_data = game_data.copy()
    game_data['할인 시작일'] = pd.to_datetime(game_data['할인 시작일'])

    # 각일별 최저가 및 해당 최저가에 해당하는 모든 데이터 찾기
    min_price_data = game_data.loc[game_data.groupby('할인 시작일')['할인가'].idxmin()]

    # Plotly를 사용하여 산점도 생성 (최저가 데이터만 사용)
    # 그래프 색상을 구매하기 버튼 색상인 #5B7C99으로 변경
    fig = px.scatter(min_price_data,
                     x='할인 시작일',
                     y='할인가',
                     hover_name='플랫폼 이름',
                     hover_data={
                         '할인가': ':,'},  # 할인가를 쉼표와 함께 전체 숫자로 표시
                     title='날짜별 최저 할인가 추이',
                     labels={'할인 시작일': '할인 시작일', '할인가': '할인가 (원)'},
                     color_discrete_sequence=['#5B7C99'])

    # 최저가를 나타내는 라인 트레이스 추가
    # 라인과 마커의 색상을 #5B7C99으로 변경
    fig.add_trace(
        go.Scatter(
            x=min_price_data['할인 시작일'],
            y=min_price_data['할인가'],
            mode='lines+markers',
            name='날짜별 최저 할인가',
            line=dict(color='#5B7C99', width=2),
            marker=dict(size=8, symbol='circle', color='#5B7C99'),
            hovertemplate='<b>날짜:</b> %{x|%Y-%m-%d}<br><b>최저 할인가:</b> %{y:,}원<br><b>플랫폼:</b> %{customdata[0]}<extra></extra>',
            customdata=min_price_data[['플랫폼 이름']]
        )
    )

    # 그래프 레이아웃 업데이트
    fig.update_layout(xaxis_title="할인 날짜",
                      yaxis_title="할인가",
                      xaxis_tickformat='%Y-%m-%d',
                      yaxis_tickformat=',', # y축 레이블을 쉼표를 포함한 전체 숫자로 표시
                      legend_title_text='범례')

    return fig

# --- 가격 형식 변환 함수 ---
def format_display_price(price_string):
    """가격 문자열을 보기 좋은 형식으로 변환합니다."""
    if pd.isna(price_string):
        return "가격 정보 없음"
    
    cleaned = remove_html_tags(str(price_string))
    
    if "품절" in cleaned.lower():
        return "🚫 품절"
    if "무료" in cleaned.lower():
        return "🆓 무료"
    
    cleaned = cleaned.replace('\\', '').replace(',', '').strip()
    price_match = re.search(r'(\d+\.?\d*)', cleaned)
    
    if price_match:
        try:
            price_num = float(price_match.group(0))
            return f"₩{int(price_num):,}"
        except (ValueError, TypeError):
            return cleaned
    return cleaned

# --- 페이지 설정 ---
st.set_page_config(layout="wide")

# --- 데이터 로딩 ---
@st.cache_data
def load_data(path):
    """CSV 파일을 불러와 데이터프레임으로 반환합니다."""
    df = pd.read_csv(path)
    
    for col in ['원가', '할인가', '할인율']:
        if col in df.columns:
            df[col] = df[col].apply(remove_html_tags)
    
    if '장르' not in df.columns:
        df['장르'] = '기타'
    df['장르'] = df['장르'].fillna('기타').astype(str)
    
    if '사이트 URL' not in df.columns:
        df['사이트 URL'] = ''
    df['사이트 URL'] = df['사이트 URL'].fillna('')
    
    return df

# --- 샘플 데이터 생성 (실제 파일이 없을 경우) ---
def create_sample_data():
    """샘플 데이터를 생성합니다."""
    sample_data = {
        '게임 이름': [
            'Cyberpunk 2077', 'The Witcher 3', 'Red Dead Redemption 2', 
            'Grand Theft Auto V', 'Assassin\'s Creed Valhalla', 'Call of Duty: Modern Warfare',
            'FIFA 23', 'Minecraft', 'Among Us', 'Fall Guys'
        ],
        '플랫폼 이름': ['Steam', 'Steam', 'Epic Games', 'Steam', 'Steam', 'Steam', 'Steam', 'Steam', 'Steam', 'Steam'],
        '원가': ['₩59,800', '₩39,800', '₩69,800', '₩29,800', '₩59,800', '₩49,800', '₩79,800', '₩26,900', '₩5,500', '₩20,500'],
        '할인가': ['₩29,900', '₩9,950', '₩34,900', '₩14,900', '₩29,900', '₩24,900', '₩39,900', '₩26,900', '무료', '₩10,250'],
        '할인율': ['50%', '75%', '50%', '50%', '50%', '50%', '50%', '0%', '100%', '50%'],
        '장르': ['RPG, 액션', 'RPG, 어드벤처', '액션, 어드벤처', '액션, 범죄', 'RPG, 액션', 'FPS, 액션', '스포츠', '샌드박스, 생존', '파티, 추리', '파티, 플랫포머'],
        '이미지 URL': [
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300',
            '/placeholder.svg?height=200&width=300'
        ],
        '사이트 URL': [
            'https://store.steampowered.com/app/1091500/Cyberpunk_2077/',
            'https://store.steampowered.com/app/292030/The_Witcher_3_Wild_Hunt/',
            'https://store.epicgames.com/en-US/p/red-dead-redemption-2',
            'https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/',
            'https://store.steampowered.com/app/1174180/Assassins_Creed_Valhalla/',
            'https://store.steampowered.com/app/1938090/Call_of_Duty_Modern_Warfare_II/',
            'https://store.steampowered.com/app/1811260/EA_SPORTS_FIFA_23/',
            'https://store.steampowered.com/app/1172470/Minecraft/',
            'https://store.steampowered.com/app/945360/Among_Us/',
            'https://store.steampowered.com/app/1097150/Fall_Guys/'
        ]
    }
    return pd.DataFrame(sample_data)

# --- 데이터 로드 ---
try:
    df = load_data("data/cleaned_merged_games_data.csv")
    df_sales = load_data("data/combined_sales_data.csv")
except FileNotFoundError:
    st.error("오류: 데이터 파일을 찾을 수 없습니다.")
    st.info("`merged_games_data.csv`와 `combined_sales_data.csv` 파일을 앱과 같은 위치에 넣어주세요.")
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
    st.rerun()

# --- 메인 UI ---
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
            numeric_discounts = pd.to_numeric(df['할인율'].str.replace('%', ''), errors='coerce')
            avg_discount = numeric_discounts[numeric_discounts > 0].mean()
            st.metric(label="평균 할인율", value=f"{avg_discount:.1f} %")
    
    with col3:
        with st.container(border=True):
            numeric_prices = pd.to_numeric(df['할인가'].str.replace('₩', '').str.replace(',', ''), errors='coerce')
            free_games = df[(df['할인가'] == '무료') | (numeric_prices == 0)].shape[0]
            st.metric(label="무료 게임 수", value=f"{free_games} 개")
    
    st.markdown("---")
    
    left_col, right_col = st.columns([2, 1])

    with left_col:
        # 1. 플랫폼별 게임 수 및 평균 할인율 (이중 축 막대 그래프)
        st.subheader("📊 플랫폼별 게임 수 및 평균 할인율")
        
        platform_summary = df.groupby('플랫폼 이름').agg(
            game_count=('게임 이름', 'count'),
            avg_discount=('할인율', lambda x: pd.to_numeric(x.astype(str).str.replace('%', ''), errors='coerce').mean())
        ).reset_index()

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=platform_summary['플랫폼 이름'],
            y=platform_summary['game_count'],
            name='게임 수',
            marker_color='#5B7C99',
            yaxis='y1'
        ))
        fig1.add_trace(go.Scatter(
            x=platform_summary['플랫폼 이름'],
            y=platform_summary['avg_discount'],
            name='평균 할인율',
            marker_color='#d43f3a',
            mode='lines+markers',
            yaxis='y2'
        ))

        fig1.update_layout(
            title_text='플랫폼별 게임 수 및 평균 할인율',
            yaxis=dict(title='게임 수', side='left'),
            yaxis2=dict(title='평균 할인율 (%)', overlaying='y', side='right'),
            legend_title_text='범례'
        )
        st.plotly_chart(fig1, use_container_width=True)

        # 2. 가격대별 게임 분포 (막대 그래프)
        st.subheader("💰 가격대별 게임 분포")
        # '할인가' 컬럼을 숫자로 변환
        df['numeric_sales_price'] = pd.to_numeric(
            df['할인가'].astype(str).str.replace('₩', '').str.replace(',', ''), errors='coerce'
        ).fillna(0)
        
        bins = [0, 20000, 40000, 60000, 80000, 100000, float('inf')]
        labels = ['0-2만원', '2-4만원', '4-6만원', '6-8만원', '8-10만원', '10만원 이상']
        df['price_range'] = pd.cut(df['numeric_sales_price'], bins=bins, labels=labels, right=False)
        
        price_distribution = df['price_range'].value_counts().sort_index()
        price_distribution_df = price_distribution.reset_index()
        price_distribution_df.columns = ['price_range', 'count']

        fig2 = px.bar(price_distribution_df, x='price_range', y='count',
                     title='가격대별 게임 분포',
                     labels={'price_range': '가격대', 'count': '게임 수'},
                     color='price_range',
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        # 3. 할인율 구간별 게임 분포 (파이 그래프)
        st.subheader("📉 할인율 구간별 게임 분포")
        # '할인율' 컬럼을 숫자로 변환
        df['numeric_discount'] = pd.to_numeric(
            df['할인율'].astype(str).str.replace('%', ''), errors='coerce'
        ).fillna(0)

        # 0% 할인은 제외
        df_discounted = df[df['numeric_discount'] > 0].copy()
        
        discount_bins = [0, 20, 40, 60, 80, 101]
        discount_labels = ['1-20%', '21-40%', '41-60%', '61-80%', '81-100%']
        df_discounted['discount_range'] = pd.cut(df_discounted['numeric_discount'], bins=discount_bins, labels=discount_labels, right=True)
        
        discount_distribution = df_discounted['discount_range'].value_counts().reset_index()
        discount_distribution.columns = ['discount_range', 'count']

        fig3 = px.pie(discount_distribution, values='count', names='discount_range',
                      title='할인율 구간별 게임 분포 (0% 제외)',
                      hole=0.3,
                      color_discrete_sequence=px.colors.qualitative.Plotly)
        st.plotly_chart(fig3, use_container_width=True)

        # 4. 장르별 게임 수 (막대 그래프)
        st.subheader("🕹️ 장르별 게임 수")
        # '장르' 컬럼의 쉼표로 구분된 문자열을 개별 행으로 분리
        df_exploded_genres = df.assign(장르=df['장르'].str.split(',')).explode('장르')
        df_exploded_genres['장르'] = df_exploded_genres['장르'].str.strip()
        genre_count = df_exploded_genres['장르'].value_counts().head(10).reset_index()
        genre_count.columns = ['장르', '게임 수']
        
        # 색상 스케일을 파란색 계열로 가시성 좋게 변경
        fig4 = px.bar(genre_count, x='게임 수', y='장르', orientation='h',
                     title='장르별 게임 수 (TOP 10)',
                     labels={'게임 수': '게임 수', '장르': '장르'},
                     color='게임 수',
                     color_continuous_scale='Cividis_r') #색깔 선택 가능Blues,Greens,Reds,Purples,Oranges,PuBu,YlGnBu,Viridis,Plasma,Inferno,Magma,Cividis
        fig4.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig4, use_container_width=True)
    
    with right_col:
        st.subheader("할인 중인 게임 TOP 10")
        
        numeric_discounts = pd.to_numeric(df['할인율'].str.replace('%', ''), errors='coerce').fillna(0)
        discounted_games_df = df[numeric_discounts > 0].head(10)
        
        with st.container(border=True):
            if discounted_games_df.empty:
                st.info("현재 할인 중인 게임이 없습니다.")
            else:
                for index, row in discounted_games_df.iterrows():
                    img_col, info_col, price_col, btn_col = st.columns([2, 3, 2, 1.8])
                    
                    with img_col:
                        st.image(row['이미지 URL'], use_container_width=True)
                    
                    with info_col:
                        st.markdown(f"**{row['게임 이름']}**")
                        st.caption(f"플랫폼: {row['플랫폼 이름']}")
                    
                    with price_col:
                        discount_html, price_html = "", ""
                        discount_str = str(row['할인율'])
                        discount_num = pd.to_numeric(discount_str.replace('%', ''), errors='coerce')
                        
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
                    
                    with btn_col:
                        # 상세보기 버튼을 파란색으로 변경
                        st.markdown("""
                        <style>
                        .stButton > button {
                            background-color: #007bff;
                            color: white;
                            border: none;
                        }
                        .stButton > button:hover {
                            background-color: #0056b3;
                            color: white;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        if st.button("상세", key=f"detail_{index}", use_container_width=True):
                            view_detail(index)

elif st.session_state.page == '전체 데이터 보기':
    # 상단 필터 섹션
    filter_col, _ = st.columns([1, 3])
    
    with filter_col:
        with st.container():
            st.subheader("🔍 필터 설정")
            with st.expander("검색 및 필터 옵션", expanded=True):
                with st.form(key='filter_form'):
                    search_query = st.text_input("게임 이름 검색", placeholder="예: 사이버펑크 2077")
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
    
    # 게임 목록
    current_results = st.session_state.filtered_df
    st.subheader(f"검색 결과: {len(current_results)}개의 게임")
    
    if current_results.empty:
        st.warning("선택한 조건에 맞는 게임이 없습니다.")
    else:
        # CSS 스타일링
        st.markdown("""
        <style>
            .game-card {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                transition: all 0.3s ease;
                display: flex;
                flex-direction: column;
                height: 420px;
                position: relative;
            }
            .game-card:hover {
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                transform: translateY(-2px);
                background-color: #f8f9fa;
                border-color: #5B7C99;
            }
            .game-card img {
                width: 100%;
                height: 150px;
                object-fit: cover;
                border-radius: 8px;
            }
            .game-title {
                font-weight: bold;
                font-size: 16px;
                margin-top: 10px;
                height: 40px;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }
            .game-genre {
                color: #666;
                font-size: 14px;
                margin-bottom: 8px;
                height: 20px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .price-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: auto;
                padding-top: 10px;
                height: 60px;
            }
            .price-info {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .original-price {
                color: #999;
                text-decoration: line-through;
                font-size: 14px;
            }
            .sale-price {
                font-weight: bold;
                font-size: 18px;
                color: #d32f2f;
            }
            .discount-badge {
                background-color: #d43f3a;
                color: white;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 12px;
                font-weight: bold;
            }
            /* 상세보기 버튼 스타일 */
            .stButton > button {
                background-color: #007bff !important;
                color: white !important;
                border: none !important;
            }
            .stButton > button:hover {
                background-color: #0056b3 !important;
                color: white !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        results_to_show = current_results.head(st.session_state.num_to_display)
        
        # 4열 그리드 생성
        cols = st.columns(4)
        col_index = 0
        
        for index, row in results_to_show.iterrows():
            with cols[col_index]:
                # 할인율 처리
                discount_str = str(row['할인율'])
                discount_num = pd.to_numeric(discount_str.replace('%', ''), errors='coerce')
                original_price_display = format_display_price(row['원가'])
                sales_price_display = format_display_price(row['할인가'])
                
                # 할인 배지 설정
                discount_badge = ""
                if pd.notna(discount_num) and discount_num > 0:
                    discount_badge = f'<span class="discount-badge">-{int(discount_num)}%</span>'
                
                # 가격 정보 HTML
                price_info_html = f'<div class="price-info">'
                if pd.notna(discount_num) and discount_num > 0 and original_price_display != sales_price_display:
                    price_info_html += f'<div><div class="original-price">{original_price_display}</div><div class="sale-price">{sales_price_display}</div></div>'
                else:
                    price_info_html += f'<div class="sale-price">{sales_price_display}</div>'
                price_info_html += f'{discount_badge}</div>'
                
                # 게임 카드 HTML
                card_html = (
                    f'<div class="game-card">'
                    f'<img src="{row["이미지 URL"]}" alt="{row["게임 이름"]}">'
                    f'<div class="game-title">{row["게임 이름"]}</div>'
                    f'<div class="game-genre">장르: {row["장르"][:30]}{"..." if len(row["장르"]) > 30 else ""}</div>'
                    f'<div class="price-container">'
                    f'{price_info_html}'
                    f'</div>'
                    f'</div>'
                )
                
                st.markdown(card_html, unsafe_allow_html=True)
                
                # 상세보기 버튼 추가
                if st.button("상세보기", key=f"view_detail_{index}", use_container_width=True):
                    view_detail(index)
                
                col_index = (col_index + 1) % 4
        
        # 더 보기 버튼
        if len(current_results) > st.session_state.num_to_display:
            if st.button("더 보기", use_container_width=True):
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
        # 인덱스 존재 여부 확인
        if selected_id not in df.index:
            st.error(f"오류: 선택된 게임 ID({selected_id})가 데이터에 존재하지 않습니다.")
            if st.button("목록으로 돌아가기"):
                st.session_state.page = '전체 데이터 보기'
                st.rerun()
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
                discount_str = str(game_data['할인율'])
                discount_num = pd.to_numeric(discount_str.replace('%', ''), errors='coerce')
                
                if pd.notna(discount_num) and discount_num > 0:
                    discount_html = f'<span style="background-color: #d43f3a; color: white; border-radius: 5px; padding: 3px 8px; font-weight: bold; font-size: 0.9em;">-{int(discount_num)}%</span>'
                
                original_price_display = format_display_price(game_data['원가'])
                sales_price_display = format_display_price(game_data['할인가'])
                
                if original_price_display != sales_price_display and '품절' not in sales_price_display:
                    price_html = f'<div style="text-align: left;"><span style="font-size: 1.1em; color: grey;"><del>{original_price_display}</del></span><br><strong style="font-size: 1.8em; color: #d32f2f;">{sales_price_display}</strong></div>'
                else:
                    price_html = f'<div style="text-align: left; font-size: 1.8em; font-weight: bold;">{sales_price_display}</div>'
                
                final_price_html = f'<div style="display: flex; justify-content: flex-start; align-items: center; gap: 15px; height: 100%;">{price_html}{discount_html}</div>'
                st.markdown(final_price_html, unsafe_allow_html=True)
                
                st.subheader(" ")
                st.info("게임 설명란 (추후 데이터 추가 시 표시됩니다.)")
                
                # 구매 링크 버튼
                if game_data['사이트 URL']:
                    st.link_button("🛒 구매하러 가기", game_data['사이트 URL'])
            
            # 사이트별 가격 비교 - 간단한 방식으로 수정
            st.markdown("---")
            st.subheader("🛍️ 사이트별 가격 비교")

            store_logos = {
                'steam': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/1024px-Steam_icon_logo.svg.png',
                'directg': 'https://avatars.fastly.steamstatic.com/9e83477d3d1484489b83970cfd7a1051f886f688_full.jpg',
                'epicgames': 'https://upload.wikimedia.org/wikipedia/commons/3/31/Epic_Games_logo.svg',
                'greenmangaming': 'https://mcvuk.com/wp-content/uploads/green-man-gaming-logo_rgb_light-bg_copypng.png'
            }

            
            game_name = game_data['게임 이름']
            related_games = df[df['게임 이름'] == game_name]
            
            stores_data = {
                'steam': None, 'directg': None, 'epicgames': None, 'greenmangaming': None
            }
            
            for _, row in related_games.iterrows():
                url = str(row.get('사이트 URL', '')).lower()
                if 'directg.net' in url:
                    stores_data['directg'] = row
                elif 'store.steampowered.com' in url:
                    stores_data['steam'] = row
                elif 'epicgames.com' in url:
                    stores_data['epicgames'] = row
                elif 'greenmangaming.com' in url:
                    stores_data['greenmangaming'] = row
            
            store_display_names = {
                'steam': 'Steam', 
                'directg': 'Direct Games', 
                'epicgames': 'Epic Games', 
                'greenmangaming': 'Green Man Gaming'
            }
            
            # 간단한 컨테이너 방식으로 변경
            for store_key, store_name in store_display_names.items():
                store_data = stores_data.get(store_key)

                with st.container(border=True):
                    # 순서: 로고 | 스토어명 | 가격 | 구매버튼
                    col_logo, col_name, col_price, col_button = st.columns([0.3, 1.5, 0.4, 0.4])

                    with col_logo:
                        st.image(store_logos[store_key], width=100)

                    with col_name:
                        st.markdown(f"**{store_name}**")

                    with col_price:
                        if store_data is not None:
                            original = format_display_price(store_data['원가'])
                            sales = format_display_price(store_data['할인가'])
                            discount_str = str(store_data['할인율'])
                            discount_num = pd.to_numeric(discount_str.replace('%', ''), errors='coerce')

                            if pd.notna(discount_num) and discount_num > 0 and original != sales:
                                st.markdown(f"""
                                    <span style='background-color: #dc3545; color: white; border-radius: 4px; padding: 2px 6px; font-size: 12px; font-weight: bold;'>-{int(discount_num)}%</span>
                                    <span style='color: #888; text-decoration: line-through; font-size: 13px; margin-left: 6px;'>{original}</span>
                                    <span style='font-size: 15px; font-weight: bold; color: #d32f2f; margin-left: 10px;'>{sales}</span>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='font-size: 15px; font-weight: bold;'>{sales}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color: #999;'>정보 없음</span>", unsafe_allow_html=True)

                    with col_button:
                        if store_data is not None and store_data['사이트 URL']:
                            st.markdown("""
                                <style>
                                .custom-link-button {
                                    display: inline-block;
                                    background-color: #007bff;
                                    color: white !important;
                                    padding: 6px 10px;
                                    border-radius: 6px;
                                    text-decoration: none !important;
                                    font-size: 13px;
                                    font-weight: bold;
                                    text-align: center;
                                    transition: background-color 0.2s;
                                    width: 100%;
                                }
                                .custom-link-button:hover {
                                    background-color: #0056b3;
                                }
                                </style>
                            """, unsafe_allow_html=True)
                            st.markdown(
                                f'<a href="{store_data["사이트 URL"]}" target="_blank" class="custom-link-button">구매하기</a>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown("<span style='color: #999;'>-</span>", unsafe_allow_html=True)
                
            st.markdown("---")
            st.subheader("📈 가격 추이")
            
            # '게임 이름' 클리닝
            cleaned_game_name = clean_game_name_final(game_data['게임 이름'])

            # combined_sales_data.csv에서 해당 게임의 데이터 필터링
            game_sales_data = df_sales[df_sales['게임 이름'] == cleaned_game_name]

            if not game_sales_data.empty:
                # visualize 함수를 호출하여 그래프 생성
                fig = visualize(game_sales_data)
                # Streamlit에 그래프 표시
                st.plotly_chart(fig, use_container_width=True, key=f"price_chart_{cleaned_game_name}")
            else:
                st.info("해당 게임의 가격 추이 데이터가 없습니다.")