import pandas as pd
import numpy as np

# 파일 경로 설정
raw_input_file = "data/steam_detailed_data.csv"
steam_file = "data/steam_games_data.csv"
directg_file = "data/directg_games_data.csv"
output_file = "data/merged_games_data.csv"

### 1. Steam 데이터 전처리
# 원본 Steam CSV 파일 불러오기
raw_df = pd.read_csv(raw_input_file)

# '정보 없음' 또는 'Free'인 게임 제거
filtered_df = raw_df[~raw_df["원가"].isin(["정보 없음", "Free"])].copy()

# 저장
filtered_df.to_csv(steam_file, index=False, encoding="utf-8-sig")
print(f"[완료] 필터링된 {len(filtered_df)}개 게임 데이터를 저장했습니다 → {steam_file}")

# Steam 필터링된 데이터 불러오기
steam_df = pd.read_csv(steam_file)

### 2. DirectG 데이터 로딩 및 정리
directg_df = pd.read_csv(directg_file)

# 유저리뷰 처리
if "유저 리뷰" in directg_df.columns:
    directg_df["유저리뷰수"] = directg_df["유저 리뷰"].fillna(0)
elif "유저리뷰수" not in directg_df.columns:
    directg_df["유저리뷰수"] = 0

# 이미지 컬럼명 통일
if "이미지" in directg_df.columns:
    directg_df.rename(columns={"이미지": "이미지 URL"}, inplace=True)

### 3. 전처리 함수 정의
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

genre_translation = {
    '액션': 'Action', '어드벤쳐': 'Adventure', '시뮬레이션': 'Simulation',
    '레이싱/스포츠': 'Racing/Sports', '레이싱': 'Racing', '스포츠': 'Sports',
    'RPG': 'RPG', '인디': 'Indie', '캐주얼': 'Casual', '전략': 'Strategy',
    '퍼즐': 'Puzzle', '호러': 'Horror', '롤플레잉': 'RPG', '슈팅': 'Shooter',
    '전체 이용가': 'All Ages', '12세 이용가': '12+', '15세 이용가': '15+',
    '19세 이용가': '19+',
}

def translate_genre(genre_str):
    if pd.isna(genre_str):
        return genre_str
    genres = [g.strip() for g in str(genre_str).replace('/', ',').split(',')]
    translated = [genre_translation.get(g, g) for g in genres]
    return ", ".join(translated)

### 4. 전처리 적용
for df in [steam_df, directg_df]:
    df["원가"] = df["원가"].apply(clean_price).astype("Int64")
    df["할인가"] = df["할인가"].apply(clean_price).astype("Int64")
    df["할인율"] = df["할인율"].apply(clean_discount).astype("Int64")
    df["유저리뷰수"] = pd.to_numeric(df["유저리뷰수"], errors="coerce").fillna(0).astype("Int64")
    df["연령 등급"] = df["연령 등급"].replace("정보 없음", np.nan)
    df["장르"] = df["장르"].apply(translate_genre)

### 5. 컬럼 통일 및 병합
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

# 병합
merged_df = pd.concat([steam_df, directg_df], ignore_index=True)

# 저장
merged_df.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"[완료] 병합된 데이터가 '{output_file}'에 저장되었습니다.")
