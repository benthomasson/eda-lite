FROM quay.io/bthomass/ansible-rulebook:ifthisthenthat

WORKDIR $HOME/eda-ifthisthenthat
COPY . $WORKDIR

USER $USER_ID
RUN pip install .
CMD ["uvicorn" , "ifthisthenthat_eda.app:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/etc/ssl/certs/ssl-cert.key", "--ssl-certfile", "/etc/ssl/certs/ssl-cert.crt"]
