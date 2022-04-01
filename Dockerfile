FROM python:3.10

WORKDIR /usr/src/app

ENV FLASK_APP=lab_api

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=80"]