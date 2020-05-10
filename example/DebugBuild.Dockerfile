FROM tiangolo/meinheld-gunicorn:python3.7
ARG TELESTATE_DIST
ARG FOLDER

COPY $TELESTATE_DIST/. /telestate_dist
COPY $FOLDER/requirements.txt /config/requirements.txt


RUN set -x \
    && echo /telestate_dist \
    && ls /telestate_dist \
    && chmod +x /entrypoint.sh \
    && mkdir -p /config/ \
    && rm -rf /app \
    && mkdir -p /app \
    && cd /app \
    && pip install --no-cache-dir -r /config/requirements.txt \
    && pip install --no-cache-dir -e /telestate_dist \
    && echo 'done'

COPY $FOLDER/. /telemenu_dist
RUN set -x \
    && echo /telemenu_dist \
    && ls /telemenu_dist \
    && mv /app/* /telemenu_dist/example/code/  \
    && rm -rf /app \
    && ln -s /telemenu_dist/example/code /app \
    && cd /app \
    && pip install --no-cache-dir -e /telemenu_dist



