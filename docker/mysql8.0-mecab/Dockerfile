FROM --platform=linux/amd64 ubuntu:latest
RUN apt update && apt install -y \
    mysql-server                                \
    mecab                                       \
    libmecab-dev                                \
    mecab-ipadic-utf8                           \
    locales                                     \
&&  locale-gen ja_JP.UTF-8                      \
&&  echo "dicdir=/var/lib/mecab/dic/ipadic-utf8" > /etc/mecabrc
ENV LANG        ja_JP.UTF-8
ENV LC_CTYPE    ja_JP.UTF-8

