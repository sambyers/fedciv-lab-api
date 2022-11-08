FROM python:3.10
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . .
# Remove mock to use the lab network devices
CMD [ "./start.sh" ]