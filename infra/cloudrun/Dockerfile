FROM python:3.13-slim
WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app
RUN pip install --no-cache-dir fastapi==0.116.1 pydantic-settings==2.10.1 uvicorn==0.35.0 firebase-admin==7.1.0 google-cloud-firestore==2.21.0 'google-cloud-storage>=2.18.0' 'google-cloud-tasks>=2.16.0' 'google-auth>=2.35.0' 'google-genai>=1.0.0' 'google-adk>=1.0.0' 'cryptography>=43.0.0'
RUN useradd --create-home --uid 10001 appuser
ENV PYTHONPATH=/app/backend
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
