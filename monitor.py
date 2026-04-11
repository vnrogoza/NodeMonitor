import requests, time, sqlite3, datetime

# Создание таблицы, если не существует
conn = sqlite3.connect("monitor.db")
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
conn.close()


def RunTask():
    # URL to request
    url = "https://cbr.ru/s/newbik"    
    # Start timing
    start_time = time.time()

    try:
        # Make GET request
        response = requests.get(url)
        # End timing
        end_time = time.time()        
        response_time_ms = round(end_time - start_time, 3) 
        status_code = response.status_code
        error_message = None   
        #print("Status Code:", response.status_code, f"   Response Time: {response_time_ms:.2f} ms")
        print(str(datetime.datetime.now())[:19], "     Status:", status_code, f"   Response Time: {response_time_ms:.2f} ms")

    #except requests.exceptions.RequestException as e:
    except requests.RequestException as e:
        # Обработка всех ошибок запроса
        status_code = None
        #response_time_ms = None
        end_time = time.time()
        # Calculate response time in milliseconds
        response_time_ms = round(end_time - start_time, 3)
        status_code = 000        
        error_message = str(e)[:100]        
        print(str(datetime.datetime.now())[:19], f"     Ошибка при выполнении запроса: {error_message}")

    # Подключение к SQLite (или создание файла базы данных)
    conn = sqlite3.connect("monitor.db")
    cursor = conn.cursor()
    # Вставка данных
    local_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
    INSERT INTO requests_log (url, status_code, response_time_ms, error_message, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (url, status_code, response_time_ms, error_message, local_timestamp))
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

        
def CreateReport():
    import os, webbrowser
    conn = sqlite3.connect("monitor.db")
    cursor = conn.cursor()        
    cursor.execute('SELECT timestamp, response_time_ms, iif(status_code in (200, "200"), "blue", "red") FROM requests_log' )
    data = cursor.fetchall()                
    conn.close()    
    data = str([list(item) for item in data])[1:]
    data = '[["Дата Время", "Запрос, мс", { role: "style" }], '+data
    html = '''<head>
  <title>Мониторинг ЦБ РФ</title>
  <style>html, body, #container { width: 100%; height: 100%; margin: 20; padding: 20; }</style>
</head>
<body>
  <div id="chart_div" style="width: 1800px; height: 600px;"></div>   
  <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>  
  <script type="text/javascript">
  google.charts.load('current', {packages: ['corechart', 'bar']});
  google.charts.setOnLoadCallback(drawBasic);

  function drawBasic() {
       var data = google.visualization.arrayToDataTable( $data );	   
      var options = {
        title: 'Мониторинг доступности сайта ЦБ РФ',		
		chartArea: {width: '80%', height: '80%'},        
        hAxis: {title: 'Дата Время', format: 'h:mm', showTextEvery:12},
        vAxis: {title: 'Запрос, мс'},
		legend: {position:'none'}    
      };

      var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
      chart.draw(data, options);
  }
  </script> 
</body>
</html>
'''
    html = html.replace("$data", data)
    fileName = "report.html" 
    fileName = os.getcwd()+"\\"+fileName    
    with open(fileName, "w") as writer: 
        writer.write(html)
    #with open("O:\\IT\\Общее\\Rogoza\\CbrReport.html", "w") as writer2: 
    #    writer2.write(html)        
    #webbrowser.open('file://'+fileName)
    print(str(datetime.datetime.now())[:19], "     Report created")


import schedule
def RunSchedule():
    print('Scheduler started...')
    schedule.every(1).minutes.do(RunTask)
    schedule.every(2).minutes.do(CreateReport)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    #RunTask()
    RunSchedule()
    #CreateReport()
    
    
