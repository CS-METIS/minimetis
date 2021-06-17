FROM azul/zulu-openjdk:8

RUN apt update -y && apt upgrade -y && apt install -y curl fuse libfuse2
WORKDIR /opt


# Install alluxio
RUN curl -L https://downloads.alluxio.io/downloads/files/2.5.0/alluxio-2.5.0-bin.tar.gz | tar -xvz
RUN ln -s /opt/alluxio-2.5.0 /opt/alluxio
ENV ALLUXIO_HOME /opt/alluxio

# Install HADOOP
RUN curl -L https://apache.mediamirrors.org/hadoop/common/hadoop-2.10.1/hadoop-2.10.1.tar.gz | tar -xvz
RUN ln -s /opt/hadoop-2.10.1 /opt/hadoop
ENV HADOOP_HOME /opt/hadoop
ENV HADOOP_CLASSPATH /opt/alluxio/client/alluxio-2.5.0-client.jar:${HADOOP_CLASSPATH}

# Install hive
RUN curl -L https://apache.mediamirrors.org/hive/hive-3.1.2/apache-hive-3.1.2-bin.tar.gz | tar -xvz
RUN ln -s /opt/apache-hive-3.1.2-bin /opt/hive
ENV HIVE_HOME /opt/hive


RUN mkdir -p /var/lib/hive
RUN mkdir -p /var/lib/alluxio
