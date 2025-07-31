# app.py
import streamlit as st
import pandas as pd

# CSV 파일 로드 함수
@st.cache_data
def load_data():
    return pd.read_csv("data/steam_detailed_data.csv")

# 데이터 로드
df = load_data()

st.title("🔥 Steam 인기 게임 정보 대시보드")
st.caption("데이터는 실시간이 아닌 크롤링 기반입니다.")

# 테이블 형태로 데이터 보여주기
st.dataframe(df)

# 옵션: 게임명 기준 검색
search = st.text_input("게임명을 입력하세요")
if search:
    filtered = df[df["게임 이름"].str.contains(search, case=False, na=False)]
    st.dataframe(filtered)
