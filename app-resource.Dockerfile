FROM python:3.12-slim

RUN pip install --upgrade pip \
	&& adduser --disabled-login worker

USER worker

WORKDIR /home/worker

COPY --chown=worker:worker application/resource/ .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]