FROM python:3.12-bullseye

COPY ./app /app
COPY ./pyproject.toml pyproject.toml
COPY tools/wait-for-it.sh /wait-for-it.sh

RUN mkdir -p /app/uploads

RUN apt-get update && apt-get install -y default-mysql-client

RUN pip install --upgrade pip
RUN pip install -e .
RUN pip install gunicorn

RUN chmod +x /wait-for-it.sh

EXPOSE 8000

WORKDIR /app

ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=lumieres_project.settings

CMD ["/wait-for-it.sh", "db:3306", "gunicorn", "--bind", "0.0.0.0:8000", "lumieres_project.wsgi:application"]