FROM centos:centos7

RUN     yum clean all && \
        groupadd --gid 1000 elasticsearch && \
        adduser --uid 1000 --gid 1000 --home /usr/share/elasticsearch elasticsearch && \
        mkdir /var/lib/elasticsearch/ && \
        chown -R 1000:1000 /var/lib/elasticsearch/

USER 1000:1000

WORKDIR /usr/share/elasticsearch
COPY ./elasticsearch-8.8.1-linux-x86_64.tar.gz /usr/share/elasticsearch/

RUN     tar -xzf elasticsearch-8.8.1-linux-x86_64.tar.gz && \
        cp -rp elasticsearch-8.8.1/* ./ && \
        rm -fR elasticsearch-8.8.1*


COPY ./elasticsearch.yml /usr/share/elasticsearch/config/

EXPOSE 9200 9300

CMD ["bin/elasticsearch"]
