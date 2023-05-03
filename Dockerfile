FROM python:3.10.6
WORKDIR /app
COPY requirements/development.txt ./
RUN pip install --upgrade pip
RUN pip install --no-deps --no-cache-dir -r development.txt
COPY . .
EXPOSE 8000
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]