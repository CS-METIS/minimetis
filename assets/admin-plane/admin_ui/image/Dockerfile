FROM httpd:2.4

RUN apt update -y && apt install python3 -y
ADD www /usr/local/apache2/htdocs

CMD [ "sh", "-c", "httpd-foreground" ]