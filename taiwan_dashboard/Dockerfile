FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY patch_chart.py .
RUN python patch_chart.py && rm -f patch_chart.py
EXPOSE 8890
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8890"]
