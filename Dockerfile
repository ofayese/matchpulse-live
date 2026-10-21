# syntax=docker/dockerfile:1.7

# Builder image must be supplied at build time by an approved immutable digest.
ARG PYTHON_BUILDER_IMAGE=python:3.12.15-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258

FROM ${PYTHON_BUILDER_IMAGE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install \
      --no-cache-dir \
      --no-compile \
      --target=/opt/matchpulse \
      .

FROM ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac AS runtime

# The OCI revision and source labels record the exact commit the published
# image was built from. The release workflow supplies them at build time, so
# the image carries its own source identity.
ARG OCI_REVISION
ARG OCI_SOURCE
LABEL org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.source="${OCI_SOURCE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/matchpulse

WORKDIR /app

COPY --from=builder --chown=10001:10001 \
    /opt/matchpulse/ /opt/matchpulse/

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3.12 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=3s --start-period=10s --retries=3 \
  CMD ["/usr/bin/python3.12", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/ready', timeout=2)"]

ENTRYPOINT ["/usr/bin/python3.12", "-m", "uvicorn"]
CMD ["matchpulse.service:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
