FROM python:3.11
WORKDIR /rekcod
COPY ./requirements.txt /rekcod/requirements.txt
RUN pip install --no-cache-dir -r /rekcod/requirements.txt
COPY ./app /rekcod/app
ENV X_API_KEY 88829a93cdab6f6b44ff539f1ead287bcb93d663e31f0630fe5739c7d377d044
ENV X_API_KEY_ALGO HS256
CMD ["uvicorn", "app.oauth_passlib_advanced:app", "--host", "0.0.0.0", "--port", "80"]
