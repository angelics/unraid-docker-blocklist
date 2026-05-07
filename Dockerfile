FROM python:3.12-alpine
WORKDIR /app
COPY fetch.py server.py entrypoint.sh config.json ./
RUN pip install --no-cache-dir requests && \
    mkdir -p /data /config && \
    chmod +x entrypoint.sh && \
    mv config.json config.json.sample
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "server.py"]
