# Official WOSAC scoring environment (Linux amd64).
# waymo-open-dataset wheels are not published for macOS.
FROM tensorflow/tensorflow:2.12.0

RUN pip install --no-cache-dir waymo-open-dataset-tf-2-12-0==1.6.7

WORKDIR /app
COPY wosac_preflight/constants.py /app/wosac_preflight/constants.py
COPY wosac_preflight/__init__.py /app/wosac_preflight/__init__.py
COPY docker/score_one.py /app/score_one.py
COPY vendor/testdata /app/vendor/testdata

ENV PYTHONPATH=/app
ENTRYPOINT ["python", "/app/score_one.py"]
