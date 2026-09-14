FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY patch_chart.py .
COPY patch_v04_backend.py .
COPY patch_v04_frontend.py .
RUN python patch_chart.py \
    && python patch_v04_backend.py \
    && python patch_v04_frontend.py \
    && rm -f patch_chart.py patch_v04_backend.py patch_v04_frontend.py
EXPOSE 8890
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8890"]
