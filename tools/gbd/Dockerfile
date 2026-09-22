# GBD identifiers (Markus Iser, benchmark-database.de): gbdhash is the MD5 of
# the normalised CNF, isohash an isomorphism-invariant variant.
FROM python:3.12.7-slim-bookworm
RUN pip install --no-cache-dir gbdc==0.4.2
COPY gbdhash.py /usr/local/bin/gbdhash.py
WORKDIR /data
ENTRYPOINT ["python3", "/usr/local/bin/gbdhash.py"]
