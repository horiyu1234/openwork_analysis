import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

# ChromeDriverのパス
driver_path = '/Users/yhorii/Downloads/chromedriver-mac-arm64/chromedriver'

# ヘッダー情報の設定（User-Agentなど）
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

# ChromeDriverのサービスオブジェクトを作成
service = Service(executable_path=driver_path)

# ChromeDriverのインスタンスを作成
driver = webdriver.Chrome(service=service, options=chrome_options)

# データを保存するリスト
data = []

# 投稿者の属性情報を分類する関数
def categorize_attributes(attributes):
    categorized = {'how_long': '', 'working': '', 'new_grad': '', 'gender': '', 'whosheis': ''}
    
    # "在籍" の部分
    how_long_match = re.search(r'在籍\d+～\d+年', attributes)
    if how_long_match:
        categorized['how_long'] = how_long_match.group()

    # "退社済み" または "現職" を部分一致で対応
    working_match = re.search(r'(退社済み|現職)', attributes)
    if working_match:
        categorized['working'] = working_match.group()
    else:
        # "現職（回答時）" のような表現を部分一致で処理
        working_match_partial = re.search(r'現職.*', attributes)
        if working_match_partial:
            categorized['working'] = working_match_partial.group()

    # "中途入社" または "新卒入社"
    new_grad_match = re.search(r'(中途入社|新卒入社)', attributes)
    if new_grad_match:
        categorized['new_grad'] = new_grad_match.group()

    # "男性" または "女性"
    gender_match = re.search(r'(男性|女性)', attributes)
    if gender_match:
        categorized['gender'] = gender_match.group()

    # 他のすべての属性を "whosheis" に格納
    # 他のカテゴリに該当しない部分を抽出
    other_attributes = re.sub(r'在籍\d+～\d+年|退社済み|現職.*|中途入社|新卒入社|男性|女性', '', attributes)
    categorized['whosheis'] = other_attributes.strip()

    return categorized

try:
    # OpenWorkのログインページにアクセス
    driver.get('https://www.openwork.jp/login.php')

    # メールアドレスとパスワードの入力
    email_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "_username"))
    )
    email_input.send_keys('input your mail address')  # メールアドレスを入力

    password_input = driver.find_element(By.ID, '_password')
    password_input.send_keys('input your password')  # パスワードを入力

    # ログインボタンをクリック
    login_button = driver.find_element(By.ID, 'log_in')
    login_button.click()

    # ページ番号
    page_number = 1

    while True:
        # 1ページ目は next_page パラメータを含まない
        if page_number == 1:
            page_url = 'https://www.openwork.jp/company_answer.php?m_id=a0910000000GVaN&q_no=6'
        else:
            # 2ページ目以降は next_page パラメータを付与
            page_url = f"https://www.openwork.jp/company_answer.php?m_id=a0910000000GVaN&q_no=6&next_page={page_number}"

        print(f"Scraping page: {page_number} - {page_url}")

        # 該当ページにアクセス
        driver.get(page_url)
        time.sleep(5)  # ページの読み込みを待機

        # 口コミの本文を取得 (実際のHTMLクラス名はページ構造に合わせて調整)
        review_elements = driver.find_elements(By.CLASS_NAME, 'article_answer')  # クラス名を適宜調整

        # 投稿者の属性を取得
        attribute_elements = driver.find_elements(By.CLASS_NAME, 'mr-5.v-m')

        if not review_elements or not attribute_elements:
            print("No more reviews found.")
            break

        # 口コミと投稿者属性をペアで処理
        for review, attributes in zip(review_elements, attribute_elements):
            review_text = review.text.strip()  # 口コミ本文
            attribute_text = attributes.text.strip()  # 投稿者の属性

            # 属性を分類
            categorized_attributes = categorize_attributes(attribute_text)

            # データをリストに保存
            data.append({
                'reputation': review_text,
                'how_long': categorized_attributes['how_long'],
                'working': categorized_attributes['working'],
                'new_grad': categorized_attributes['new_grad'],
                'gender': categorized_attributes['gender'],
                'whosheis': categorized_attributes['whosheis']
            })

        # "次へ"ボタンを探して次ページへ進む
        try:
            next_button = driver.find_element(By.CLASS_NAME, 'paging_link-more')
        except Exception as e:
            print("No more pages found.")
            break

        # 次ページへ進む
        page_number += 1

finally:
    # ブラウザを閉じる
    driver.quit()

    # DataFrameに変換
    df = pd.DataFrame(data)

    # CSVファイルに出力
    df.to_csv('openwork_reviews_with_attributes.csv', index=False, encoding='utf-8')
    print("Data saved to openwork_reviews_with_attributes.csv")
