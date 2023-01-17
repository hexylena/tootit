FROM alpine:3.11
# Copies your code file from your action repository to the filesystem path `/` of the container
COPY tootit.py /tootit.py
RUN chmod +x tootit.py

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/tootit.py"]
