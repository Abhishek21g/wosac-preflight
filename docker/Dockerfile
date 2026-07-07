# WOSAC scoring image — minimal deps, waymo wheel with --no-deps (jax not needed for metrics).
FROM python:3.10-bookworm

RUN pip install --no-cache-dir \
    "tensorflow==2.13.0" \
    "tensorflow_probability==0.21.0" \
    "numpy==1.23.5" \
    "pandas==1.5.3" \
    "scikit-learn==1.2.2" \
    "absl-py==1.4.0" \
    "immutabledict==2.2.0" \
    "protobuf>=3.20,<5"

RUN pip install --no-cache-dir --no-deps "waymo-open-dataset-tf-2-12-0==1.6.7"

WORKDIR /app
COPY docker/score_one.py /app/score_one.py

ENV PYTHONPATH=/app
ENTRYPOINT ["python", "/app/score_one.py"]
