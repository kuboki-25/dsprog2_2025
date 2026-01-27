import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re

# ===== 設定 =====
JOB_URLS = [
    "https://www.green-japan.com/company/10518/job/277257",
    "https://www.green-japan.com/company/5153/job/280318",
    "https://www.green-japan.com/company/5109/job/287074",
    "https://www.green-japan.com/company/2520/job/36116",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

DB_NAME = "jobs.db"

# ===== DB接続 =====
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# ===== テーブル初期化（毎回クリーン）=====
cursor.execute("DROP TABLE IF EXISTS jobs")

cursor.execute("""
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title TEXT,
    company TEXT,
    salary_text TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    remote INTEGER,
    location TEXT,
    url TEXT
)
""")

conn.commit()

# ===== スクレイピング =====
for url in JOB_URLS:
    print(f"取得中: {url}")

    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    page_text = soup.get_text(" ", strip=True)

    # --- 求人タイトル ---
    title_tag = soup.find("h1")
    job_title = title_tag.text.strip() if title_tag else None

    # --- 会社名（本文から推定） ---
    company = None
    m_company = re.search(r"株式会社[^\s]+", page_text)
    if m_company:
        company = m_company.group()

    # --- 年収 ---
    salary_text = None
    m_salary = re.search(r"\d+万円〜\d+万円", page_text)
    if m_salary:
        salary_text = m_salary.group()

    salary_min = None
    salary_max = None
    if salary_text:
        nums = re.findall(r"\d+", salary_text)
        if len(nums) == 2:
            salary_min = int(nums[0])
            salary_max = int(nums[1])

    # --- 勤務地 ---
    location = None
    m_location = re.search(r"(東京都|大阪府|フルリモート|全国)", page_text)
    if m_location:
        location = m_location.group()

    # --- リモート判定 ---
    remote = 1 if "リモート" in page_text else 0

    # --- DB保存 ---
    cursor.execute("""
        INSERT INTO jobs (
            job_title, company, salary_text,
            salary_min, salary_max,
            remote, location, url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_title,
        company,
        salary_text,
        salary_min,
        salary_max,
        remote,
        location,
        url
    ))

    conn.commit()
    time.sleep(2)

conn.close()
print("スクレイピング完了（DB初期化済み）")