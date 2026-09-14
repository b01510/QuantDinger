FROM ghcr.io/openbyteinc/quantdinger-backend:latest

USER root
COPY tw_stock.py /app/app/data_sources/tw_stock.py
COPY patch_backend.py /tmp/patch_backend.py
RUN python /tmp/patch_backend.py && rm -f /tmp/patch_backend.py

USER app
