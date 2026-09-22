FROM eclipse-temurin:17-jdk

RUN useradd -m -u 1000 sandboxuser

WORKDIR /code

USER 1000:1000
