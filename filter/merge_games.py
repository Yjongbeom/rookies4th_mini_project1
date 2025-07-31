import pandas as pd
import numpy as np

# 파일 경로 설정
steam_file = "data/steam_games_data.csv"
directg_file = "data/directg_games_data.csv"
output_file = "data/merged_games_data.csv"

# 1. CSV 파일 불러오기
steam_df = pd.read_csv(steam_file)
directg_df = pd.read_csv(directg_file)

# 2. DirectG 컬럼 정리
if "유저 리뷰" in directg_df.columns:
    directg_df["유저리뷰수"] = directg_df["유저 리뷰"].fillna(0)
elif "유저리뷰수" not in directg_df.columns:
    directg_df["유저리뷰수"] = 0

if "이미지" in directg_df.columns:
    directg_df.rename(columns={"이미지": "이미지 URL"}, inplace=True)

# 3. 가격 및 할인율 정리 함수
def clean_price(val):
    try:
        return int(float(str(val).replace("₩", "").replace("\\", "").replace(",", "").replace("\"", "").strip()))
    except:
        return np.nan

def clean_discount(val):
    try:
        return int(str(val).replace("%", "").replace("\"", "").strip())
    except:
        return np.nan

# 4. 장르 번역 딕셔너리
genre_translation = {
    '액션': 'Action',
    '어드벤쳐': 'Adventure',
    '시뮬레이션': 'Simulation',
    '레이싱/스포츠': 'Racing/Sports',
    '레이싱': 'Racing',
    '스포츠': 'Sports',
    'RPG': 'RPG',
    '인디': 'Indie',
    '캐주얼': 'Casual',
    '전략': 'Strategy',
    '퍼즐': 'Puzzle',
    '호러': 'Horror',
    '롤플레잉': 'RPG',          
    '슈팅': 'Shooter',          
    '전체 이용가': 'All Ages',
    '12세 이용가': '12+',
    '15세 이용가': '15+',
    '19세 이용가': '19+',
}


# 5. 장르 통일 함수
def translate_genre(genre_str):
    if pd.isna(genre_str):
        return genre_str
    genres = [g.strip() for g in str(genre_str).replace('/', ',').split(',')]
    translated = [genre_translation.get(g, g) for g in genres]
    return ", ".join(translated)

# 6. 전처리 적용
for df in [steam_df, directg_df]:
    df["원가"] = df["원가"].apply(clean_price).astype("Int64")
    df["할인가"] = df["할인가"].apply(clean_price).astype("Int64")
    df["할인율"] = df["할인율"].apply(clean_discount).astype("Int64")
    df["유저리뷰수"] = pd.to_numeric(df["유저리뷰수"], errors="coerce").fillna(0).astype("Int64")
    df["연령 등급"] = df["연령 등급"].replace("정보 없음", np.nan)
    df["장르"] = df["장르"].apply(translate_genre)

# 7. 공통 컬럼 기준 통일
common_columns = [
    "게임 이름", "원가", "할인가", "사이트 URL", "할인율",
    "유저리뷰수", "플랫폼 이름", "이미지 URL", "장르", "연령 등급"
]

for df in [steam_df, directg_df]:
    for col in common_columns:
        if col not in df.columns:
            df[col] = np.nan

steam_df = steam_df[common_columns]
directg_df = directg_df[common_columns]

# 8. 병합
merged_df = pd.concat([steam_df, directg_df], ignore_index=True)

# 9. 저장
merged_df.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"[완료] 병합된 데이터가 '{output_file}'에 저장되었습니다.")
