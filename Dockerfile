FROM texastribune/supervisor
MAINTAINER tech@texastribune.org

RUN apt-get update && apt-get -yq install nginx
# There's a known harmless warning generated here:
# See https://github.com/benoitc/gunicorn/issues/788

RUN pip install gunicorn==19.1.1
RUN pip install flask



# 1.every service should add the dependency to the requirements.txt


WORKDIR /app
# TOOD: move this to ancestor image?
RUN mkdir /app/run
RUN mkdir /app/flask_app
#add the project to the /app/
ADD flask_app/ /app/flask_app
RUN pip install -r /app/flask_app/requirements.txt
ADD gunicorn_conf.py /app/
ADD gunicorn.supervisor.conf /etc/supervisor/conf.d/

ADD nginx.conf /app/
ADD nginx.supervisor.conf /etc/supervisor/conf.d/



VOLUME ["/app/logs"]
EXPOSE 9010
