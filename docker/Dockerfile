# Official WOSAC scoring — Python 3.10 + TF 2.13 (TF 2.12 image is py3.8; jaxlib 0.4.13 unavailable).
FROM python:3.10-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

# Pin deps matching waymo-open-dataset-tf-2-12-0==1.6.7 (install wheel with --no-deps).
RUN pip install --no-cache-dir \
    "tensorflow==2.13.0" \
    "numpy==1.23.5" \
    "pandas==1.5.3" \
    "pillow==9.2.0" \
    "matplotlib==3.6.1" \
    "absl-py==1.4.0" \
    "dask==2023.3.1" \
    "einsum==0.3.0" \
    "immutabledict==2.2.0" \
    "jax==0.4.13" \
    "jaxlib==0.4.13" \
    "plotly==5.13.1" \
    "pyarrow==16.0.0" \
    "scikit-image==0.20.0" \
    "scikit-learn==1.2.2" \
    "setuptools==67.6.0" \
    "tensorflow_probability==0.21.0" \
    "visu3d==1.5.1" \
    "dacite==1.8.1" \
    "google-auth==2.16.2" \
    "protobuf>=3.20,<5"

RUN pip install --no-cache-dir --no-deps "waymo-open-dataset-tf-2-12-0==1.6.7"

WORKDIR /app
COPY docker/score_one.py /app/score_one.py

ENV PYTHONPATH=/app
ENTRYPOINT ["python", "/app/score_one.py"]
