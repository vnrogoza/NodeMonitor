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
    REPORT_INTERVAL_MINUTES,
    LOG_LEVEL,
    REPORT_HEADER,
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Создание таблицы, если не существует
try:
    conn = sqlite3.connect(DB_PATH)
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
finally:
    conn.close()


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
    import os, webbrowser
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

    data = str([list(item) for item in data])[1:]
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
    RunSchedule()
    
    
