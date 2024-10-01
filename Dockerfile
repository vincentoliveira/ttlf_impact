FROM python:3.10

WORKDIR /app

# Copy application dependency manifests to the container image.
# Copying this separately prevents re-running pip install on every code change.
COPY requirements.txt ./

# Install production dependencies.
RUN set -ex; \
    pip install -r requirements.txt; \
    pip install gunicorn

COPY . /app

RUN mkdir -p /app/databases

CMD exec gunicorn --log-file=- --bind :8080 --workers 1 --threads 8 app:app
