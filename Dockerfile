# REF: https://github.com/nazliander/scrape-nr-of-deaths-istanbul/blob/master/Dockerfile
ARG PYTHON_IMAGE_VERSION="3.9"

FROM python:${PYTHON_IMAGE_VERSION}

#------------------------------
# DESC: Informations to make the
# download of the Chrome and Chrome Driver

ARG CHROME_VERSION="114.0.5735.90-1"
ARG CHROME_DRIVER_VERSION="114"
#------------------------------

#------------------------------
# DESC: Informations to make the
# download of the scientific journals

ARG JOURNAL_NUMBER='2'
ENV JOURNAL_NUMBER=${JOURNAL_NUMBER}

ARG JOURNAL_YEAR='2024'
ENV JOURNAL_YEAR=${JOURNAL_YEAR}
#------------------------------

#------------------------------
# DESC: connect and persist information on ChromaDB
#---------------DEVELOPMENT INFOS---------------
ARG CHROMA_HOST='0.0.0.0'
ENV CHROMA_HOST=${CHROMA_HOST}

ARG CHROMA_PORT='8000'
ENV CHROMA_PORT=${CHROMA_PORT}

ARG CHROMA_SERVER_AUTHN_PROVIDER='chromadb.auth.token_authn.TokenAuthClientProvider'
ENV CHROMA_SERVER_AUTHN_PROVIDER=${CHROMA_SERVER_AUTHN_PROVIDER}

ARG CHROMA_SERVER_AUTHN_CREDENTIALS='chr0ma-t0k3n'
ENV CHROMA_SERVER_AUTHN_CREDENTIALS=${CHROMA_SERVER_AUTHN_CREDENTIALS}

ARG CHROMA_AUTH_TOKEN_TRANSPORT_HEADER='Authorization'
ENV CHROMA_AUTH_TOKEN_TRANSPORT_HEADER=${CHROMA_AUTH_TOKEN_TRANSPORT_HEADER}

ARG CHROMA_COLLECTION='scientific_collection'
ENV CHROMA_COLLECTION=${CHROMA_COLLECTION}

ARG EMBEDDING_MODEL_NAME='all-MiniLM-L6-v2'
ENV EMBEDDING_MODEL_NAME=${EMBEDDING_MODEL_NAME}

ARG LOGFIRE_PROJECT_TOKEN=''
ENV LOGFIRE_PROJECT_TOKEN=${LOGFIRE_PROJECT_TOKEN}

#------------------------------

# DESC: Install Google Chrome specific version
# Aparentemente este link está quebrado: https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/. Logo,
# Achei uma alternativa neste link: https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/, a partir deste
# comentário do stackoverflow: https://stackoverflow.com/a/78001106
RUN wget --no-verbose -O /tmp/chrome.deb https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb \
  && apt-get update \
  && apt install -y /tmp/chrome.deb \
  && rm /tmp/chrome.deb

# DESC: Chorme driver
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_DRIVER_VERSION}`/chromedriver_linux64.zip \
    && apt-get install -yqq unzip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

WORKDIR /scientific-assistant-crawler

RUN chmod -R 775 ./

ENV PYTHONPATH="/scientific-assistant-crawler"

COPY pyproject.toml poetry.lock ./

# DESC: Install the poetry, set the env var in the project directory,
# and install the dependencies

RUN python -m pip install -q poetry==1.8.3 \
    && python -m poetry config virtualenvs.in-project true \
    && python -m poetry install --only main

COPY /scripts ./scripts

# DESC: Importante definir esta env para solucionar o bug na hora
# da obtenção do modelo de embeddings
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# DESC: Get the embedding model
RUN python -m poetry run python ./scripts/caching_embedding_model.py

COPY /src ./src

#-------------------------
# DESC: only for debugging on the development process
# RUN python -m poetry run python /scientific-assistant-crawler/scripts/get_articles.py
# ENTRYPOINT ["tail", "-f", "/dev/null"]
#-------------------------

CMD ["python", "-m", "poetry", "run", "python", "/scientific-assistant-crawler/scripts/get_articles.py"]

#----------INSTRUCTIONS----------

# buildar a imagem
#docker build -t scientific_crawler .

# executar o container com os containers visualizando a rede da maquina
#docker run -d --name scientific_crawler_service --network host scientific_crawler

# acessar o container
#docker exec -i -t scientific_crawler_service bash

# finalizar a execucao do container
#docker kill scientific_crawler_service

# excluir os containers finalizados
#docker rm $(docker ps -a -q)
