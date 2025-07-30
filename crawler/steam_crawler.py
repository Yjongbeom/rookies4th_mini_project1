# crawler/steam_crawler.py
# 스팀 웹크롤링 코드입니다

# crawler/steam_crawler.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os

headers = {
    "User-Agent": "Mozilla/5.0"
}

def calculate_discount(원가, 할인가):
    try:
        if "Free" in 원가 or "무료" in 원가:
            return "0%"
        o = int(re.sub(r"[₩,\s]", "", 원가))
        f = int(re.sub(r"[₩,\s]", "", 할인가))
        if o > f:
            return f"{round((1 - f / o) * 100)}%"
    except:
        pass
    return "0%"

def parse_detail_page(url):
    """상세 페이지에서 평점, 리뷰, 장르, 연령, 가격 정보 추출"""
    time.sleep(0.5)
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # 유저 평점
        review_summary = soup.select_one(".user_reviews_summary_row .game_review_summary")
        review_summary = review_summary.text.strip() if review_summary else "정보 없음"

        # 유저 리뷰 수
        review_count = soup.select_one(".user_reviews_summary_row .responsive_hidden")
        if review_count:
            count = re.findall(r'(\d[\d,]*)', review_count.text)
            review_count = count[0] if count else "정보 없음"
        else:
            review_count = "정보 없음"

        # 장르
        genre_tag = soup.select("div.details_block a[href*='genre']")
        genre = ", ".join([g.text for g in genre_tag]) if genre_tag else "정보 없음"

        # 연령 등급
        age_block = soup.select_one(".details_block")
        age_text = age_block.text if age_block else ""
        age_match = re.search(r"Rating:\s*(.*)", age_text)
        age = age_match.group(1).strip() if age_match else "정보 없음"

        # 가격 정보 (첫 번째 구매 항목 기준)
        purchase_block = soup.select_one(".game_area_purchase_game")
        if purchase_block:
            original = purchase_block.select_one(".discount_original_price")
            final = purchase_block.select_one(".discount_final_price")
            if final:  # 할인 중
                원가 = original.text.strip() if original else final.text.strip()
                할인가 = final.text.strip()
            else:  # 정가만 존재하거나 무료
                price_text = purchase_block.select_one(".game_purchase_price")
                원가 = 할인가 = price_text.text.strip() if price_text else "정보 없음"
        else:
            원가 = 할인가 = "정보 없음"

        # 무료 처리
        for price in [원가, 할인가]:
            if "Free" in price or "무료" in price or price.strip() in ["₩ 0", "₩0"]:
                원가 = 할인가 = "Free"
                break

        할인율 = calculate_discount(원가, 할인가)

        return review_summary, review_count, genre, age, 원가, 할인가, 할인율

    except Exception as e:
        print(f"[상세페이지 오류] {url} : {e}")
        return "정보 없음", "정보 없음", "정보 없음", "정보 없음", "정보 없음", "정보 없음", "0%"

def crawl_all_pages(max_page=5):
    base_url = "https://store.steampowered.com/search/?filter=globaltopsellers&page="
    game_list = []

    for page in range(1, max_page + 1):
        url = base_url + str(page)
        print(f"[INFO] 페이지 {page} 수집 중: {url}")
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        games = soup.select("a.search_result_row")

        for g in games:
            try:
                title = g.select_one("span.title").text.strip()
                game_url = g["href"]
                image_url = g.select_one("img")["src"]

                # 상세 페이지 접근
                유저평점, 유저리뷰, 장르, 연령등급, 원가, 할인가, 할인율 = parse_detail_page(game_url)

                game_list.append({
                    "게임 이름": title,
                    "원가": 원가,
                    "할인가": 할인가,
                    "사이트 URL": game_url,
                    "할인율": 할인율,
                    "유저평점": 유저평점,
                    "유저리뷰": 유저리뷰,
                    "플랫폼 이름": "Steam",
                    "이미지 URL": image_url,
                    "장르": 장르,
                    "연령 등급": 연령등급
                })

            except Exception as e:
                print(f"[게임 목록 파싱 오류] {e}")
                continue

        time.sleep(1)

    return pd.DataFrame(game_list)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df = crawl_all_pages(max_page=3)
    df.to_csv("data/steam_detailed_data.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ 총 {len(df)}개 게임 정보 저장 완료: data/steam_detailed_data.csv")
