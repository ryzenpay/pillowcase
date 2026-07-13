FROM python:3.12-slim


COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY pillowcase/ /app/pillowcase/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN useradd --create-home --uid 10001 pillow \
    && mkdir -p /input /output /config \
    && chown -R pillow /input /output /config

ENTRYPOINT ["/entrypoint.sh"]
