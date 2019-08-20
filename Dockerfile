FROM debian:sid-slim

RUN apt-get update && apt-get install -y \
    locales \
    locales-all \
    python3 \
    pipenv \
    texlive-full \
    poppler-utils

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

WORKDIR /app
COPY . /app
RUN pipenv install --system --deploy --ignore-pipfile

WORKDIR /app/latex-completion-data
CMD [ "python3", "main.py" ]
