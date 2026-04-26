FROM python:3.11-slim

# System dependencies for psycopg2, opencv, GDAL/rasterio
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev libgdal-dev libgeos-dev \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all requirement files
COPY backend/requirements.txt /tmp/requirements-backend.txt
COPY data_pipeline/requirements.txt /tmp/requirements-pipeline.txt
COPY ml_classifier/requirements.txt /tmp/requirements-ml.txt

# Install each set of dependencies separately to handle naming conflicts
# (data_pipeline has 'sentinelhub-py' which is wrong; backend has the correct 'sentinelhub')
RUN pip install --no-cache-dir -r /tmp/requirements-backend.txt && \
    pip install --no-cache-dir -r /tmp/requirements-ml.txt && \
    pip install --no-cache-dir rasterio numpy shapely geopandas requests

# Copy source code
COPY backend/ /app/backend/
COPY data_pipeline/ /app/data_pipeline/
COPY ml_classifier/ /app/ml_classifier/

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
