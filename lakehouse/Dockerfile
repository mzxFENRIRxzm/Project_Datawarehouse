FROM apache/hive:4.0.0

USER root
ADD https://jdbc.postgresql.org/download/postgresql-42.7.4.jar /opt/hive/lib/postgresql.jar
ADD https://jdbc.postgresql.org/download/postgresql-42.7.4.jar /opt/hadoop/share/hadoop/common/lib/postgresql.jar
RUN chmod 644 /opt/hive/lib/postgresql.jar /opt/hadoop/share/hadoop/common/lib/postgresql.jar
USER hive
