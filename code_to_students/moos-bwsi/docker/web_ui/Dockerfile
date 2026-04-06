# bwsi-web-ui — lightweight Flask dashboard
# Build from the docker/ directory:
#   docker build -f web_ui/Dockerfile -t bwsi-web-ui:latest web_ui/

FROM python:3.11-slim

RUN pip install flask pymoos --no-cache-dir

COPY app.py /app/app.py
COPY templates/ /app/templates/

WORKDIR /app
CMD ["python", "app.py"]
