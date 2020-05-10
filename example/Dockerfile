FROM tiangolo/meinheld-gunicorn:python3.7

COPY $FOLDER/requirements.txt   /config/requirements.txt
RUN chmod +x /entrypoint.sh &&  pip install --no-cache-dir -r /config/requirements.txt

COPY $FOLDER/code /app
