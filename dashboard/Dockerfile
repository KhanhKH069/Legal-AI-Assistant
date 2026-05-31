FROM python:3.12-slim

WORKDIR /app

# Cài đặt uv
RUN pip install uv==0.5.15

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
