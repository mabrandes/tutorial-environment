FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10
#use existing image and extend it

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./ /app