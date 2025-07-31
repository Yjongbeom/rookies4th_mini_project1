import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time

# --- 가격 형식을 통일하는 함수 추가 --- #
def format_price(price_text):
    """가격 문자열에서 불필요한 기호(₩, \, 원)와 공백을 제거하고, 맨 앞에 ₩를 붙여 반환합니다."""
    if isinstance(price_text, str):
        cleaned_price = price_text.replace('₩', '').replace('\\', '').replace('원', '').strip()
        # 숫자 형태인 경우에만 ₩ 기호를 붙여서 반환
        if cleaned_price.isdigit():
            return f"₩ {cleaned_price}"
    # 문자열이 아니거나 숫자가 아닌 경우(예: '품절')는 그대로 반환
    return price_text

def scrape_all_directg_games():
    """
    다이렉트 게임즈의 모든 페이지를 순회하며,
    DLC를 제외하고 상세 페이지의 정보를 포함한 최종 데이터를 스크래핑하는 함수 (최종본)
    """
    base_url = "https://directg.net/game/game.html"
    game_data_list = []

    # --- 1. 최종 페이지 번호 찾기 ---
    try:
        print("최종 페이지 번호를 확인합니다...")
        response = requests.get(base_url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        last_page = 1 # 기본값
        pagination = soup.find('ul', class_='pagination')
        if pagination:
            page_links = pagination.find_all('a')
            for link in page_links:
                if link.get_text(strip=True) == 'Last »':
                    last_page_href = link['href']
                    last_page = int(last_page_href.split('page=')[-1])
                    break
        
        print(f"최종 페이지: {last_page} 페이지")
    except Exception as e:
        print(f"최종 페이지 번호를 찾는 중 오류 발생: {e}. 1페이지만 진행합니다.")
        last_page = 1 
    
    # --- 2. 1페이지부터 마지막 페이지까지 순회 ---
    for page_num in range(1, last_page + 1):
        page_url = f"https://directg.net/game/game.html?page={page_num}"
        print(f"\n--- {page_num} 페이지 스크래핑 시작 ---")

        try:
            response = requests.get(page_url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            game_items = soup.select('div.product.vm-col.vm-col-3')
            if not game_items:
                print(f"{page_num} 페이지에 게임이 없어 중단합니다.")
                break

            for item in game_items:
                # 1단계: 목록 페이지에서 기본 정보 및 URL 추출
                temp_title_tag = item.find('h2', itemprop='name')
                temp_title = temp_title_tag['content'] if temp_title_tag else '제목 없음'
                
                site_url = 'URL 없음'
                site_url_tag = item.find('a', itemprop='url')
                if site_url_tag and 'href' in site_url_tag.attrs:
                    site_url = urljoin(base_url, site_url_tag['href'])

                # 2단계: 상세 페이지 접속하여 최종 데이터 추출
                game_title, genre, age_rating = temp_title, '정보 없음', '정보 없음'
                
                if site_url != 'URL 없음':
                    try:
                        detail_response = requests.get(site_url)
                        detail_response.encoding = 'utf-8'
                        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                        
                        # --- DLC 게임인지 확인하는 최종 로직 ---
                        short_desc_div = detail_soup.find('div', class_='product-short-description')
                        if short_desc_div and "기본 게임이 필요합니다" in short_desc_div.get_text():
                            print(f"  - DLC 게임으로 판단되어 건너뜁니다: {temp_title}")
                            continue 
                        # --- DLC 확인 로직 끝 ---
                        
                        # 영문 제목, 장르, 연령 등급 추출
                        title_span_tag = detail_soup.select_one('h1 span[style="text-transform:none"]')
                        if title_span_tag:
                            game_title = title_span_tag.get_text(strip=True)
                        
                        info_section = detail_soup.find('div', class_='product-info')
                        if info_section:
                            genre_desc_tag = info_section.find('span', class_='vm-desc', string='장르 ')
                            if genre_desc_tag:
                                genre_value_tag = genre_desc_tag.find_next_sibling('span', class_='vm-value')
                                if genre_value_tag: genre = genre_value_tag.get_text(strip=True)

                            age_img_tag = info_section.select_one('div#etc > img')
                            if age_img_tag and 'src' in age_img_tag.attrs:
                                img_src = age_img_tag['src']
                                if 'age_10' in img_src: age_rating = '전체 이용가'
                                elif 'age_12' in img_src: age_rating = '12세 이용가'
                                elif 'age_15' in img_src: age_rating = '15세 이용가'
                                elif 'age_19' in img_src: age_rating = '19세 이용가'

                    except requests.exceptions.RequestException as detail_e:
                        print(f"'{temp_title}' 상세 페이지 접속 실패: {detail_e}")
                        continue

                # 3단계: 목록 페이지에서 나머지 정보 추출
                platform_name = '플랫폼 정보 없음'
                platform_img = item.select_one('div[style*="display:block"] img')
                if platform_img and 'src' in platform_img.attrs:
                    src = platform_img['src']
                    if 'steam' in src: platform_name = 'Steam'
                    elif 'rockstar' in src: platform_name = 'Rockstar'
                    elif 'epic' in src: platform_name = 'Epic Games'
                
                image_tag = item.find('img', class_='browseProductImage')
                image_url = image_tag['src'] if image_tag else '이미지 없음'
                
                sales_price_tag = item.find('span', class_='PricesalesPrice', itemprop='price')
                sales_price = sales_price_tag.get_text(strip=True) if sales_price_tag else '품절'

                base_price_tag = item.find('span', class_='PricebasePrice')
                if base_price_tag and base_price_tag.get_text(strip=True):
                    original_price = base_price_tag.get_text(strip=True)
                    discount_rate_tag = item.find('span', class_='label-danger')
                    discount_rate = discount_rate_tag.get_text(strip=True) if discount_rate_tag else '0%'
                else:
                    original_price = sales_price
                    discount_rate = '0%'

                original_price = format_price(original_price)
                sales_price = format_price(sales_price)
                
                print(f"  - 처리 완료: {game_title}")
                game_data_list.append({
                    "게임 이름": game_title,
                    "원가": original_price,
                    "할인가": sales_price,
                    "사이트 URL": site_url,
                    "할인율": discount_rate,
                    "유저 평점": None, 
                    "유저 리뷰": None,
                    "플랫폼 이름": platform_name,
                    "이미지": image_url,
                    "장르": genre,
                    "연령 등급": age_rating,
                })
        
        except Exception as e:
            print(f"{page_num} 페이지 처리 중 오류 발생: {e}")
            continue 

        time.sleep(1)

    return game_data_list

if __name__ == "__main__":
    print("다이렉트 게임즈 전체 페이지 스크래핑을 시작합니다...")
    scraped_data = scrape_all_directg_games()

    if scraped_data:
        df = pd.DataFrame(scraped_data)
        print(f"\n총 {len(df)}개의 게임 데이터를 수집했습니다.")
        print("최종 스크래핑 결과 (상위 5개):")
        print(df.head())
        df.to_csv("data/directg_games_data.csv", index=False, encoding='utf-8-sig')
        print("\n'data/directg_games_data.csv' 파일로 저장이 완료되었습니다.")
    else:
        print("스크래핑된 데이터가 없습니다.")