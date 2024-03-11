FROM python:3.9

# Установка зависимостей
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода в контейнер
COPY . /app

# Запуск кода
CMD ["python", "main.py"]
