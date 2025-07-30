import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def get_game_detail(url):
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # 가격 정보
        price_div = soup.select(".game_purchase_price, .discount_original_price, .discount_final_price")
        prices = [p.text.strip() for p in price_div if "demo" not in p.text.lower()]
        prices = [p for p in prices if p]

        if not prices:
            origin_price = sale_price = "정보 없음"
        elif len(prices) == 1:
            origin_price = sale_price = prices[0]
        else:
            origin_price = prices[0]
            sale_price = prices[-1]

        if "무료" in origin_price or "Free" in origin_price:
            origin_price = sale_price = "Free"

        # 할인율 계산
        if "₩" in origin_price and "₩" in sale_price and origin_price != sale_price:
            try:
                origin_num = int(origin_price.replace("₩", "").replace(",", "").strip())
                sale_num = int(sale_price.replace("₩", "").replace(",", "").strip())
                discount = int((1 - sale_num / origin_num) * 100)
                discount_str = f"{discount}%"
            except:
                discount_str = "정보 없음"
        elif origin_price == sale_price:
            discount_str = "0%"
        else:
            discount_str = "정보 없음"

        # 유저 리뷰 수
        review_count_tag = soup.select_one(".user_reviews_summary_row .responsive_hidden")
        if review_count_tag:
            review_count = review_count_tag.text.strip().replace(",", "")
            review_count = re.findall(r"[\d,]+", review_count)[-1]
        else:
            review_count = "정보 없음"

        # 유저 댓글 5개
        comment_divs = soup.select(".review_box .content")[:5]
        comments = [c.get_text(strip=True) for c in comment_divs if c.get_text(strip=True)]
        comments_text = "||".join(comments) if comments else "정보 없음"

        # 연령 등급
        age_info = soup.select_one(".age_rating_banner")
        age = age_info.text.strip() if age_info else "정보 없음"

        # 장르
        genre_tags = soup.select(".details_block a[href*='genre']")
        genre_list = [g.text.strip() for g in genre_tags if g.text.strip()]
        genre = ", ".join(genre_list) if genre_list else "정보 없음"

        return origin_price, sale_price, discount_str, review_count, comments_text, age, genre

    except Exception as e:
        print("상세페이지 파싱 실패:", url, e)
        return "정보 없음", "정보 없음", "정보 없음", "정보 없음", "정보 없음", "정보 없음", "정보 없음"

def crawl_all_pages(max_page=1):
    base_url = "https://store.steampowered.com/search/?filter=globaltopsellers&page={}"
    results = []

    for page in range(1, max_page + 1):
        print(f"[INFO] 페이지 {page} 수집 중...")
        url = base_url.format(page)
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        games = soup.select("a.search_result_row")

        for game in games:
            title = game.select_one(".title").text.strip()
            link = game["href"].split("?")[0]
            if "bundle" in link or "sub" in link or "soundtrack" in title.lower():
                continue

            img_url = game.select_one("img")["src"]
            platform = "Steam"

            origin_price, sale_price, discount, review_count, comments, age, genre = get_game_detail(link)

            results.append({
                "게임 이름": title,
                "원가": origin_price,
                "할인가": sale_price,
                "사이트 URL": link,
                "할인율": discount,
                "유저리뷰수": review_count,
                "유저댓글": comments,
                "플랫폼 이름": platform,
                "이미지 URL": img_url,
                "장르": genre,
                "연령 등급": age
            })

            time.sleep(1.5)

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = crawl_all_pages(max_page=3)
    df.to_csv("data/steam_detailed_data.csv", index=False, encoding="utf-8-sig")
    print("[완료] CSV 저장 완료!")
