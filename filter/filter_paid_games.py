import pandas as pd

# CSV 파일 경로 설정
INPUT_FILE = "../data/steam_detailed_data.csv"
OUTPUT_FILE = "../data/steam_games_data.csv"

# CSV 파일 불러오기
df = pd.read_csv(INPUT_FILE)

# '원가'가 '정보 없음' 또는 'Free'인 게임 제외
filtered_df = df[~df["원가"].isin(["정보 없음", "Free"])].copy()

# 필터링된 결과 저장
filtered_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"[완료] 필터링된 {len(filtered_df)}개 게임 데이터를 저장했습니다 → {OUTPUT_FILE}")
