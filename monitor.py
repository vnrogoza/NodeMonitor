import datetime
import logging
import sqlite3
import time

import requests
import schedule

from config import (
    CHECK_INTERVAL_MINUTES,
    DB_PATH,
    MONITOR_URL,
    REPORT_OUTPUT_PATH,
    REPORT_TEMPLATE_PATH,
    REPORT_HEADER,
    REPORT_INTERVAL_MINUTES,
    LOG_LEVEL,
    WEBHOOK_TIMEOUT_SECONDS,
    WEBHOOK_URL,
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def initialize_database():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
CREATE TABLE IF NOT EXISTS requests_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    status_code INTEGER,
    response_time_ms REAL,
    error_message TEXT,
    timestamp DATETIME
)
""")
            conn.commit()
    except sqlite3.Error as db_error:
        logging.error("Ошибка инициализации БД: %s", str(db_error)[:100])


def build_webhook_payload(url, status_code, response_time_ms, error_message):
    return {
        "event": "monitor_failure" if status_code != 200 or error_message else "monitor_success",
        "url": url,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "error_message": error_message,
        "timestamp": datetime.datetime.now().isoformat(),
    }


def send_webhook_notification(webhook_url, payload):
    if not webhook_url:
        logging.debug("Webhook URL is not configured, skipping notification.")
        return False

    try:
        response = requests.post(webhook_url, json=payload, timeout=WEBHOOK_TIMEOUT_SECONDS)
        response.raise_for_status()
        logging.info("Webhook notification sent to %s", webhook_url)
        return True
    except requests.RequestException as e:
        logging.error("Webhook notification failed: %s", str(e))
        return False


def format_report_data(rows):
    return str([list(item) for item in rows])[1:]


def RunTask():
    url = MONITOR_URL
    start_time = time.time()

    try:
        # Make GET request
        response = requests.get(url)
        # End timing
        end_time = time.time()        
        response_time_ms = round(end_time - start_time, 3) 
        status_code = response.status_code
        error_message = None   
        logging.info("Status: %s   Response Time: %.2f ms", status_code, response_time_ms)

    #except requests.exceptions.RequestException as e:
    except requests.RequestException as e:
        status_code = 0
        end_time = time.time()
        response_time_ms = round(end_time - start_time, 3)
        error_message = str(e)[:100]
        logging.warning("Ошибка при выполнении запроса: %s", error_message)

    if status_code != 200 or error_message:
        payload = build_webhook_payload(url, status_code, response_time_ms, error_message)
        send_webhook_notification(WEBHOOK_URL, payload)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        local_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("""
        INSERT INTO requests_log (url, status_code, response_time_ms, error_message, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """, (url, status_code, response_time_ms, error_message, local_timestamp))
        conn.commit()
    except sqlite3.Error as db_error:
        logging.error("Ошибка БД: %s", str(db_error)[:100])
    finally:
        if conn:
            conn.close()

        
def CreateReport():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp, response_time_ms, iif(status_code in (200, "200"), "blue", "red") FROM requests_log')
        data = cursor.fetchall()
    except sqlite3.Error as db_error:
        logging.error("Ошибка БД при создании отчёта: %s", str(db_error)[:100])
        return
    finally:
        if conn:
            conn.close()

    data = format_report_data(data)
    data = '[["Дата Время", "Запрос, мс", { role: "style" }], ' + data

    try:
        with open(REPORT_TEMPLATE_PATH, "r", encoding="utf-8") as template_file:
            html = template_file.read()
    except OSError as template_error:
        logging.error("Не удалось открыть шаблон отчёта: %s", str(template_error)[:100])
        return

    html = html.replace("$data", data)
    html = html.replace("$header", REPORT_HEADER)
    output_path = REPORT_OUTPUT_PATH

    try:
        with open(output_path, "w", encoding="utf-8") as writer:
            writer.write(html)
        logging.info("Отчёт создан: %s", output_path)
    except OSError as write_error:
        logging.error("Не удалось записать отчёт: %s", str(write_error)[:100])

def RunSchedule():
    logging.info("Scheduler started")
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(RunTask)
    schedule.every(REPORT_INTERVAL_MINUTES).minutes.do(CreateReport)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user")
        logging.info("Goodbye!")


if __name__ == "__main__":
    initialize_database()
    RunSchedule()
    
    
