FROM gcc:13

RUN useradd -m -u 1000 sandboxuser

WORKDIR /code

USER 1000:1000
