FROM python:2.7-alpine3.7

# Copy in your requirements file
ADD requirements.txt /requirements.txt

# OR, if you’re using a directory for your requirements, copy everything (comment out the above and uncomment this if so):
# ADD requirements /requirements

# Install build deps, then run `pip install`, then remove unneeded build deps all in a single step. Correct the path to your production requirements file, if needed.
RUN set -ex \
    && apk add --no-cache \
            gcc \
            make \
            libc-dev \
            bash \
            musl-dev \
            jpeg-dev \
            zlib-dev \
            freetype-dev \
            lcms2-dev \
            openjpeg-dev \
            tiff-dev \
            tk-dev \
            tcl-dev \
            linux-headers \
            pcre-dev \
            git openssh


RUN pip install --upgrade pip
RUN pip install -r /requirements.txt

WORKDIR /usr/src/app
COPY web .
COPY proctor /usr/local/lib/python2.7/site-packages/proctor_lib
CMD ["./run.sh"]