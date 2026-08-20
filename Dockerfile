# syntax=docker/dockerfile:1
FROM python:3.11.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=1 \
    CUDA_VISIBLE_DEVICES=-1 \
    PYTHONPATH=/app:/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        g++ \
        gcc \
        gfortran \
        git \
        git-lfs \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip wheel \
    && python -m pip install -r requirements.txt

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/src/RESULTS /app/src/CACHE /home/appuser/data_grid2op \
    && chown -R appuser:appuser /home/appuser/data_grid2op

COPY --chown=appuser:appuser . .

RUN <<'EOF'
cat > /usr/local/bin/project-entrypoint <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

cd /app/src

required_files=(
  "/app/HBGB_14.pkl"
  "/app/curriculum_14/model/saved_model.pb"
  "/app/curriculum_14/actions/actions.npy"
)

for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "Required artifact is missing or empty: $file" >&2
    echo "If this repository was cloned with Git LFS, run 'git lfs pull' before building the image." >&2
    exit 66
  fi
done

if head -c 128 /app/HBGB_14.pkl | grep -q "version https://git-lfs.github.com/spec"; then
  echo "HBGB_14.pkl appears to be a Git LFS pointer, not the real model file." >&2
  echo "Run 'git lfs pull' on the host, then rebuild the image." >&2
  exit 66
fi

mkdir -p /app/src/RESULTS /app/src/CACHE

exec "$@"
SCRIPT
EOF

RUN sed -i 's/\r$//' /usr/local/bin/project-entrypoint \
    && chown -R appuser:appuser /app/src/RESULTS /app/src/CACHE \
    && chmod +x /usr/local/bin/project-entrypoint

USER appuser
WORKDIR /app/src

ENTRYPOINT ["project-entrypoint"]
CMD ["python", "main.py", "--config", "smoke"]
