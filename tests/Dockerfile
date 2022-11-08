FROM python:3.10
WORKDIR /usr/src/app
RUN python -m pip install --upgrade pip
RUN python -m pip install tox poetry
COPY . .
CMD [ "tox" ]