FROM python:3.11.4
WORKDIR /FASTAPIEXERCISE

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "myproject.app.myapi:app", "--host", "0.0.0.0", "--port", "8000"]