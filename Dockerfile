FROM python:3.7-slim-buster

RUN apt-get update
RUN apt-get -y install git

RUN pip3 install -r requirements.txt
RUN python3 -m textblob.download_corpora
# nltk_data ends up in /root so python can't find it
RUN ln -s /root/nltk_data /usr/local/nltk_data

COPY entrypoint.sh /action/entrypoint.sh
COPY run.py /action/run.py
COPY duplicate_code_detection.py /action/duplicate_code_detection.py

ENTRYPOINT ["./action/entrypoint.sh"]
