#Deriving the latest base image
FROM python:latest


#Labels as key value pair
LABEL Maintainer="Camilo Campos"


# Any working directory can be chosen as per choice like '/' or '/home' etc
# i have chosen /usr/app/src
WORKDIR /usr/app/src

#to COPY the remote file at working directory in container
COPY text_to_query.py ./
COPY requirements.txt ./
# Now the structure looks like this '/usr/app/src/test.py'
RUN pip install -r "requirements.txt"

# Expose to a port
EXPOSE 8080

#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

CMD [ "python", "./text_to_query.py"]
