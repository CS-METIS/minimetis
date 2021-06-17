FROM trinodb/trino:354

USER root
# Install alluxio
RUN curl -L https://downloads.alluxio.io/downloads/files/2.5.0/alluxio-2.5.0-bin.tar.gz | tar -xvz
RUN ln -s /opt/alluxio-2.5.0 /opt/alluxio
ENV ALLUXIO_HOME /opt/alluxio

# # Install HADOOP
# RUN curl -L https://apache.mediamirrors.org/hadoop/common/hadoop-2.10.1/hadoop-2.10.1.tar.gz | tar -xvz
# RUN ln -s /opt/hadoop-2.10.1 /opt/hadoop
# ENV HADOOP_HOME /opt/hadoop
# ENV HADOOP_CLASSPATH /opt/alluxio/client/alluxio-2.5.0-client.jar:${HADOOP_CLASSPATH}

RUN ln -s /opt/alluxio/client/alluxio-2.5.0-client.jar /usr/lib/trino/plugin/hive-hadoop2/alluxio-2.5.0-client.jar

USER trino:trino