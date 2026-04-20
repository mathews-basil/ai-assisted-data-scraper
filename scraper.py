import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    return driver

def load_full_page(driver, url):
    driver.get(url)
    time.sleep(3)

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

def get_job_links(driver):
    links = []

    elements = driver.find_elements(By.TAG_NAME, "a")
    total = len(elements)

    print(f"Scanning {total} elements for links...")

    for i, el in enumerate(elements):
        href = el.get_attribute("href")

        if href and "job" in href.lower():
            links.append(href)

        if i % 20 == 0:
            print(f"Checked {i}/{total} elements...")

    return list(set(links))

def scrape_job(driver, link):
    driver.get(link)
    time.sleep(2)

    data = {
        "title": None,
        "company": None,
        "location": None,
        "description": None,
        "link": link
    }

    try:
        data["title"] = driver.find_element(By.TAG_NAME, "h1").text
    except:
        pass

    try:
        data["company"] = driver.find_element(By.CLASS_NAME, "company").text
    except:
        pass

    try:
        data["location"] = driver.find_element(By.CLASS_NAME, "location").text
    except:
        pass

    try:
        data["description"] = driver.find_element(By.TAG_NAME, "body").text[:500]
    except:
        pass

    return data


def clean_data(data_list):
    clean = []
    seen = set()

    for item in data_list:
        if item["link"] not in seen:
            seen.add(item["link"])

            if item["title"] is not None:
                clean.append(item)

    return clean


def save_data(data):
    df = pd.DataFrame(data)

    df.to_csv("data/jobs.csv", index=False)

    with open("data/jobs.json", "w") as f:
        json.dump(data, f, indent=4)


def main():
    url = input("Enter the URL to scrape: ").strip()

    try:
        limit = int(input("Enter number of pages/links to scrape (default 20): ") or 20)
    except ValueError:
        limit = 20

    driver = init_driver()

    print(f"\nLoading page: {url}")
    load_full_page(driver, url)

    print("Extracting links...")
    links = get_job_links(driver)
    print(f"Found {len(links)} links")

    all_data = []

    for i, link in enumerate(links[:limit]):
        print(f"Scraping {i+1}/{min(len(links), limit)}")

        try:
            job_data = scrape_job(driver, link)
            all_data.append(job_data)
        except Exception as e:
            print(f"Error scraping {link}: {e}")

    driver.quit()

    print("\nCleaning data...")
    clean = clean_data(all_data)

    print("Saving data...")
    save_data(clean)

    print(f"\nDone. Total clean records: {len(clean)}")

if __name__ == "__main__":
    main()