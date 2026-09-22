# CNFgen, Massimo Lauria et al.: generators of formulas from proof complexity
# (pigeonhole, Tseitin, parity, ordering, clique, ...).  Pinned to release
# 0.9.6 and to one Python minor version, since Python's random module does not
# promise the same draws across versions.
FROM python:3.12.7-slim-bookworm
ARG CNFGEN_VERSION=0.9.6
RUN pip install --no-cache-dir "cnfgen==${CNFGEN_VERSION}" \
    && pip freeze > /usr/local/share/cnfgen-freeze.txt
ENV PYTHONHASHSEED=0
WORKDIR /data
ENTRYPOINT ["cnfgen"]
