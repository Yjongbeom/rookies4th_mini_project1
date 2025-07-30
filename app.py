import streamlit as st
import pandas as pd
import os

# 페이지 기본 설정
st.set_page_config(page_title="Steam 인기 게임 정보", layout="wide")

# 제목
st.title("🎮 Steam 인기 게임 데이터 뷰어")
st.markdown("최신 인기 게임 정보를 테이블로 확인하고, 유저 댓글도 함께 볼 수 있습니다.")

# CSV 파일 경로
csv_path = "data/steam_detailed_data.csv"

# CSV 로딩 함수
@st.cache_data
def load_data():
    return pd.read_csv(csv_path)

# 파일 존재 여부 확인
if os.path.exists(csv_path):
    df = load_data()

    # 테이블 표시
    st.subheader("📊 전체 게임 목록")
    st.dataframe(df.drop(columns=["유저댓글"]), use_container_width=True)

    # 유저 댓글 미리보기
    st.subheader("💬 유저 댓글 (상위 5개 게임)")
    for idx, row in df.head(5).iterrows():
        st.markdown(f"#### 🎮 {row['게임 이름']}")
        comments = str(row.get("유저댓글", "")).split("\n\n")
        if comments and comments[0]:
            for i, comment in enumerate(comments):
                st.markdown(f"- {comment}")
        else:
            st.markdown("- 유저 댓글 없음")
        st.markdown("---")

else:
    st.error(f"`{csv_path}` 파일을 찾을 수 없습니다. `data` 폴더에 CSV 파일이 존재하는지 확인하세요.")
