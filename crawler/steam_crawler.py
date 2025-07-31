import time
import re
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed

# 크롬 드라이버 셋업
def setup_selenium():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

# 상세 페이지에서 정보 크롤링
def get_game_detail(driver, url):
    try:
        driver.get(url)
        time.sleep(1.5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 가격: 본편만
        price_section = None
        for section in soup.select(".game_area_purchase_game"):
            if section.select_one(".btn_addtocart"):
                price_section = section
                break

        if price_section:
            price_tags = price_section.select(".discount_original_price, .discount_final_price, .game_purchase_price")
            prices = [p.text.strip() for p in price_tags if p.text.strip()]
        else:
            prices = []

        # 가격 판별
        if price_section and "Free To Play" in price_section.text:
            origin_price = sale_price = "Free"
        elif not prices:
            origin_price = sale_price = "정보 없음"
        elif len(prices) == 1:
            origin_price = sale_price = prices[0]
        else:
            origin_price, sale_price = prices[0], prices[-1]

        # 할인율 계산
        if "₩" in origin_price and "₩" in sale_price and origin_price != sale_price:
            try:
                op = int(origin_price.replace("₩", "").replace(",", ""))
                sp = int(sale_price.replace("₩", "").replace(",", ""))
                discount = f"{int((1 - sp / op) * 100)}%"
            except:
                discount = "정보 없음"
        elif origin_price == sale_price:
            discount = "0%"
        else:
            discount = "정보 없음"

        # 리뷰 수
        review_tag = soup.select_one(".user_reviews_summary_row .responsive_hidden")
        review_count = re.findall(r"[\d,]+", review_tag.text)[-1].replace(",", "") if review_tag else "정보 없음"

        # 연령 등급 (이미지 alt)
        age_img = soup.select_one(".shared_game_rating img")
        age = age_img["alt"].strip() if age_img and "alt" in age_img.attrs else "정보 없음"

        # 장르
        genre_tags = soup.select(".details_block a[href*='genre']")
        genre = ", ".join([g.text.strip() for g in genre_tags]) if genre_tags else "정보 없음"

        return origin_price, sale_price, discount, review_count, age, genre

    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        return ("정보 없음",) * 6

# 드라이버 단일 작업
def get_game_data(title, link, img_url):
    driver = setup_selenium()
    try:
        origin, sale, discount, review, age, genre = get_game_detail(driver, link)
        return {
            "게임 이름": title,
            "원가": origin,
            "할인가": sale,
            "사이트 URL": link,
            "할인율": discount,
            "유저리뷰수": review,
            "플랫폼 이름": "Steam",
            "이미지 URL": img_url,
            "장르": genre,
            "연령 등급": age
        }
    finally:
        driver.quit()

# 전체 페이지 수집
def crawl_all_pages(max_page=50):
    base_url = "https://store.steampowered.com/search/?filter=globaltopsellers&page={}"
    headers = {"User-Agent": "Mozilla/5.0"}
    game_links = []

    for page in range(1, max_page + 1):
        res = requests.get(base_url.format(page), headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        games = soup.select("a.search_result_row")

        for game in games:
            title = game.select_one(".title").text.strip()
            link = game["href"].split("?")[0]
            if "bundle" in link or "sub" in link or "soundtrack" in title.lower():
                continue
            img = game.select_one("img")["src"]
            game_links.append((title, link, img))

    print(f"[INFO] 총 {len(game_links)}개 게임 크롤링 시작...")

    all_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:  # 병렬성 조정
        futures = [executor.submit(get_game_data, t, l, i) for t, l, i in game_links]
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_data.append(result)

    return pd.DataFrame(all_data)

# 실행
if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    df = crawl_all_pages(max_page=70)  # 페이지 수 조절
    df.to_csv("data/steam_detailed_data.csv", index=False, encoding="utf-8-sig")
    print("[완료] CSV 저장 완료!")
