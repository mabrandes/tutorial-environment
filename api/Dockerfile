FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10
#use existing image and extend it

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

ENV APP_MODULE="main_with_Auth:app"

COPY ./ /app

# second option to run python file
# CMD ["uvicorn", "main_with_Auth:app", "--host", "0.0.0.0", "--port", "80"]