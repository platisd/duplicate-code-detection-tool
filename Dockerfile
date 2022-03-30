FROM python:3.7-slim

RUN apt-get update
RUN apt-get -y install git jq

COPY duplicate_code_detection.py requirements.txt run_action.py entrypoint.sh /action/

RUN pip3 install -r /action/requirements.txt requests && \
    python3 -c "import nltk; nltk.download('punkt')" && \
    ln -s /root/nltk_data /usr/local/nltk_data 

ENTRYPOINT ["/action/entrypoint.sh"]
