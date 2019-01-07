FROM python:3.7.2

MAINTAINER LSST SQuaRE <sqre-admin@lists.lsst.org>
LABEL description="SQuare Bot Jr is the second-generation, Kafka-oriented, Slack bot for LSST." \
      name="lsstsqre/sqrbot-jr"

ENV APPDIR /app
RUN mkdir $APPDIR
WORKDIR $APPDIR

# Supply on CL as --build-arg VERSION=<version> (or run `make image`).
ARG VERSION
LABEL version="$VERSION"

# Must run python setup.py sdist first before building the Docker image.

COPY dist/sqrbotjr-$VERSION.tar.gz .
RUN pip install sqrbotjr-$VERSION.tar.gz && \
    rm sqrbotjr-$VERSION.tar.gz && \
    groupadd -r app_grp && useradd -r -g app_grp app && \
    chown -R app:app_grp $APPDIR

USER app

EXPOSE 8080

CMD ["sqrbot", "run", "--port", "8080"]
