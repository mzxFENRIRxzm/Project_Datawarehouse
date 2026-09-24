FROM apache/superset:5.0.0

# Install the published wheel to supply application code and static assets.
USER 0:0
RUN . /app/.venv/bin/activate && uv pip install --no-cache --no-deps --reinstall apache-superset==5.0.0 && uv pip install --no-cache psycopg2-binary==2.9.10 trino[sqlalchemy]==0.336.0
USER 1000:1000
WORKDIR /app/pythonpath
ENV PYTHONPATH=/app/.venv/lib/python3.10/site-packages:/app/pythonpath
