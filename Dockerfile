FROM ubuntu

RUN apt-get update 

RUN apt-get -y install \
	build-essential \
	python3-dev \
	python-setuptools \
	python-pip

#Install scikit-learn dependancies

RUN set -xe \
    && apt-get update -y \
    && apt-get install -y python3-pip
RUN mkdir /app
ADD . /app



	
WORKDIR /app

RUN pip install -r requirements.txt
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
