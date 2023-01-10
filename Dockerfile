FROM debian:sid-slim

RUN apt-get update && apt-get install -y \
    locales \
    curl \
    locales-all \
    python3 \
    pipenv \
    poppler-utils

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

RUN mkdir /install-tl-unx && ls / && \
        curl -sSL  https://ftp.mpi-inf.mpg.de/pub/tex/mirror/ftp.dante.de/pub/tex/systems/texlive/tlnet/install-tl-unx.tar.gz | tar -xzC /install-tl-unx --strip-components=1 &&\
        echo 'selected_scheme scheme-full' >> /install-tl-unx/texlive.profile &&\
        /install-tl-unx/install-tl \
                -profile /install-tl-unx/texlive.profile \
             -repository https://ftp.mpi-inf.mpg.de/pub/tex/mirror/ftp.dante.de/pub/tex/systems/texlive/tlnet/

ENV PATH="$PATH:/usr/local/texlive/2022/bin/x86_64-linux"


WORKDIR /app
COPY . /app
RUN pipenv install --system --deploy --ignore-pipfile



WORKDIR /app/latex-completion-data
CMD [ "python3", "main.py" ]
