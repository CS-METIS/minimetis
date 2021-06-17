FROM httpd:2.4

RUN apt update -y && apt install python3 -y
ADD www /usr/local/apache2/htdocs
ADD replace.py replace.py

CMD [ "sh", "-c", "python3 replace.py && httpd-foreground" ]