FROM library/python:3.9
WORKDIR /opt
COPY requirements.txt /opt/
COPY keep_ica_workspace_running.py /opt/
RUN pip3 install -r requirements.txt 
RUN apt-get update -y && \
    playwright install
RUN playwright install-deps
ENV PATH $PATH:/opt/