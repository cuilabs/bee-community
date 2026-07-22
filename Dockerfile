FROM python:3.12-slim

ARG BEE_SDK_VERSION=0.6.3
RUN pip install --no-cache-dir "bee-sdk==${BEE_SDK_VERSION}"

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["bee-mcp"]
