FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY experiments/results/ ./experiments/results/

CMD ["python", "scripts/validate_tab_rfr_counts.py"]
