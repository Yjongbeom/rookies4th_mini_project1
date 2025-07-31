import pandas as pd
import numpy as np

# 파일 경로 설정
INPUT_FILE = "../data/steam_filtered_data.csv"  # 원본 파일 (수정 금지)
OUTPUT_FILE = "../data/steam_normalized_data.csv"  # 정규화된 결과 파일

# CSV 파일 불러오기
df = pd.read_csv(INPUT_FILE)

# 원본 보존을 위해 복사본 사용
normalized_df = df.copy()

# "정보 없음" → NaN 처리
normalized_df.replace("정보 없음", np.nan, inplace=True)

# 가격 정규화 함수
def parse_price(value):
    try:
        return int(float(value.replace("₩", "").replace(",", "").strip()))
    except:
        return np.nan

# 할인율 정규화 함수
def parse_discount(value):
    try:
        return int(value.replace("%", "").strip())
    except:
        return np.nan

# 정규화 적용
normalized_df["원가"] = normalized_df["원가"].apply(parse_price)
normalized_df["할인가"] = normalized_df["할인가"].apply(parse_price)
normalized_df["할인율"] = normalized_df["할인율"].apply(parse_discount)

# 정수형(Int64)으로 변환 (NaN 허용)
normalized_df["원가"] = normalized_df["원가"].astype("Int64")
normalized_df["할인가"] = normalized_df["할인가"].astype("Int64")
normalized_df["할인율"] = normalized_df["할인율"].astype("Int64")

# 결과 저장
normalized_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
print(f"[완료] 정규화된 데이터를 저장했습니다 → {OUTPUT_FILE}")
