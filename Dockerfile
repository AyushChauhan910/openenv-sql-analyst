FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user server/ ./server/

USER root
RUN pip install --no-cache-dir fastapi uvicorn pydantic
USER user

ENV PYTHONPATH=/app

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
