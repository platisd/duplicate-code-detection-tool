FROM python:3.7-slim-buster

RUN apt-get update
RUN apt-get -y install git jq

COPY entrypoint.sh /action/entrypoint.sh
COPY run_action.py /action/run_action.py
COPY duplicate_code_detection.py /action/duplicate_code_detection.py
COPY requirements.txt /action/requirements.txt

RUN pip3 install -r /action/requirements.txt
RUN pip3 install requests
RUN python3 -c "import nltk; nltk.download('punkt')"
# nltk_data ends up in /root so python can't find it
RUN ln -s /root/nltk_data /usr/local/nltk_data

ENTRYPOINT ["/action/entrypoint.sh"]
