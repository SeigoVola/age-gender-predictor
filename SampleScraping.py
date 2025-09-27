from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from time import sleep 


options = webdriver.ChromeOptions()
#以下の1行でヘッドレスモード利用を決めている
# options.add_argument('--headless')
driver = webdriver.Chrome(options = options)


target_url = "https://zozo.jp/shop/adrer/goods/89127273/?did=155805078"
# target_url = "https://zozo.jp/"
driver.get(target_url)

# 検索ボタンが表示されるまで最大10秒待機
wait = WebDriverWait(driver, 10)
search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[not(contains(@class, 'mobile-toggle')) and contains(@class, 'toggle toggle-search') ]")))
search_button.click()

# search_word = "フィンテック"

# # 検索入力ボックスが表示されるまで待機x
# search_text = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='search']")))
# search_text.send_keys(search_word)

# # 検索送信ボタンをクリック
# submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
# submit_button.click()

# # 検索結果が表示されるまで少し待機
# MAX_PAGES = 4
# i = 0

# try:
#     while True:
#         sleep(2)
#         # 記事のタイトルとリンクを取得
#         for elem in driver.find_elements(By.XPATH, "//h3/a"):
#             print(elem.text)
#             print(elem.get_attribute("href"))

#         next_link = driver.find_element(By.XPATH,"//a[contains(@class,'next')]")
#         driver.get(next_link.get_attribute("href"))
#         i += 1
#         if i >= MAX_PAGES:
#             break
# except Exception:
#     print("データが存在しません。")
# finally:
#     driver.quit()