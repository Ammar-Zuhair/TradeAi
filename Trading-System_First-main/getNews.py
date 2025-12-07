import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import csv
import requests

TELEGRAM_TOKEN = "7877894204:AAG2Bk3yckZL6QQBlX-WlBsTyBQ1lWgY77E"
TELEGRAM_CHAT_ID = "-1003037892441"


def send_telegram_message(message, retries=3):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print("📲 تم إرسال الخبر إلى Telegram.")
                return True
            else:
                print(f"⚠️ محاولة {attempt + 1} فشلت: {response.text}")
        except Exception as e:
            print(f"⚠️ محاولة {attempt + 1} فشلت: {e}")
        time.sleep(2)
    print("❌ فشل إرسال الرسالة بعد عدة محاولات.")
    return False


recommendations_log = []

options = uc.ChromeOptions()
options.headless = False
options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
options.add_argument("user-agent=Mozilla/5.0")

driver = uc.Chrome(options=options)
driver.get("https://www.forexfactory.com/calendar")
print("📂 تم فتح صفحة ForexFactory.")
time.sleep(7)

try:
    today_button = driver.find_element(By.LINK_TEXT, "Today")
    today_button.click()
    print("✅ تم الضغط على زر Today.")
except Exception as e:
    print("⚠️ فشل الضغط على زر Today:", e)

try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "tr.calendar__row"))
    )
    print("✅ الأخبار ظهرت.")
except Exception as e:
    print("⚠️ لم تظهر الأخبار:", e)

rows = driver.find_elements(By.CSS_SELECTOR, "tr.calendar__row")
print(f"📌 عدد الأخبار المستخرجة: {len(rows)}")

last_time = "غير محدد"
event_date = datetime.now().strftime("%Y-%m-%d")

for row in rows:
    try:
        time_cell = row.find_elements(By.CSS_SELECTOR, ".calendar__time")
        if time_cell and time_cell[0].text.strip():
            last_time = time_cell[0].text.strip()
        time_ = last_time

        currency = row.find_element(By.CSS_SELECTOR, ".calendar__currency").text if row.find_elements(By.CSS_SELECTOR,
                                                                                                      ".calendar__currency") else "غير محددة"
        event = row.find_element(By.CSS_SELECTOR, ".calendar__event").text if row.find_elements(By.CSS_SELECTOR,
                                                                                                ".calendar__event") else "حدث غير معروف"

        impact_cell = row.find_elements(By.CSS_SELECTOR, ".calendar__impact span")
        impact = impact_cell[0].get_attribute("title") if impact_cell else "غير معروف"
        if "High" not in impact:
            continue

        print(f"\n📅 التاريخ: {event_date}")
        print(f"📌 الحدث: {event}")
        print(f"💱 العملة: {currency}")
        print(f"🕒 الوقت: {time_}")
        print(f"🔴 التأثير: عالي")

        recommendations_log.append([
            event_date, time_, currency, event, "🔴 عالي"
        ])

        msg = f"""📅 *تاريخ الحدث:* {event_date}
📌 *الحدث:* {event}
💱 *العملة:* {currency}
🕒 *وقت الخبر:* {time_}
🔴 *التأثير:* عالي"""
        send_telegram_message(msg)

    except Exception as e:
        print("⚠️ خطأ في قراءة صف:", e)

driver.quit()

if recommendations_log:
    with open("recommendations.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "تاريخ الحدث", "الوقت", "العملة", "الحدث", "التأثير"
        ])
        writer.writerows(recommendations_log)
    print("\n📁 تم حفظ الأخبار عالية التأثير في ملف recommendations.csv بنجاح.")
else:
    print("\n📁 لا توجد أخبار عالية التأثير لحفظها.")
