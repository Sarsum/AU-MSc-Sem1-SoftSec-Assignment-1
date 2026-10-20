FROM python:3.12-slim

RUN pip install --upgrade pip \
	&& adduser --disabled-login --quiet worker

USER worker

WORKDIR /home/worker

COPY --chown=worker:worker application/export/ .
COPY --chown=worker:worker dependency/ dependency/
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir ./dependency
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]