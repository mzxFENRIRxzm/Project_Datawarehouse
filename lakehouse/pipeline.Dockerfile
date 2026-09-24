FROM python:3.11-slim
WORKDIR /workspace
COPY lakehouse/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY scripts/northwind_lakehouse.py scripts/northwind_lakehouse.py
COPY tests/test_northwind_lakehouse.py tests/test_northwind_lakehouse.py
ENTRYPOINT ["python", "-u", "scripts/northwind_lakehouse.py"]
