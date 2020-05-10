FROM tiangolo/meinheld-gunicorn:python3.7

COPY $FOLDER/. /telemenu_dist

RUN set -x \
    && chmod +x /entrypoint.sh \
    && mkdir -p /config/ \
    && ln -s /telemenu_dist/requirements.txt /config/requirements.txt \
    && rm -rf /app \
    && ln -s /telemenu_dist/example/code /app \
    && cd /app/ \
    && pip install --no-cache-dir -r /config/requirements.txt \
    && pip install --no-cache-dir -e /telemenu_dist

