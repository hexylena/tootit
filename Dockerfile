FROM python:3.11
# Copies your code file from your action repository to the filesystem path `/` of the container
COPY tootit.py /tootit.py
COPY requirements.txt /requirements.txt
RUN chmod +x /tootit.py && pip install -r /requirements.txt

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/tootit.py"]
