# NodeMonitor

Лёгкий мониторинг доступности и времени отклика сайта ЦБ РФ с графическим отчетом и webhook-уведомлениями.

## Быстрый старт

1. Клонируйте репозиторий
2. Создайте и активируйте виртуальное окружение

```powershell
python -m venv .venv
.venv\Scripts\activate.ps1
```

3. Установите зависимости

```powershell
pip install -r requirements.txt
```

4. Создайте `.env` из `.env.example`

```powershell
copy .env.example .env
```

5. Настройте параметры в `.env`

## Конфигурация

Основные переменные:

- `MONITOR_URL` — URL для проверки
- `CHECK_INTERVAL_MINUTES` — интервал проверки
- `REPORT_INTERVAL_MINUTES` — интервал генерации отчёта
- `DB_PATH` — путь к SQLite базе данных
- `REPORT_TEMPLATE_PATH` — путь к HTML-шаблону
- `REPORT_OUTPUT_PATH` — путь к выходному HTML
- `REPORT_HEADER` — заголовок графика
- `WEBHOOK_URL` — URL для webhook уведомлений
- `WEBHOOK_TIMEOUT_SECONDS` — таймаут при отправке webhook
- `LOG_LEVEL` — уровень логирования

## Запуск

```powershell
python monitor.py
```

## Webhook уведомления

Если в `.env` задан `WEBHOOK_URL`, при ошибочном запросе или коде ответа, отличном от `200`, будет отправлено JSON-уведомление.

Пример полезной нагрузки:

```json
{
  "event": "monitor_failure",
  "url": "https://cbr.ru/s/newbik",
  "status_code": 0,
  "response_time_ms": 3.12,
  "error_message": "...",
  "timestamp": "2026-04-12T12:00:00"
}
```

## Тесты

```powershell
pytest
```
