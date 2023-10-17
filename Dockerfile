#Deriving the latest base image
FROM python:3.9.18-slim-bullseye

#Crear entorno virtual
RUN python -m venv /opt/env

#Activar el entorno virtual
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /usr/app/src

COPY requirements.txt .

#to COPY the remote file at working directory in container
COPY main.py .
COPY .env .
COPY rutas/ ./rutas
COPY auth/ ./auth
COPY prompt/ ./prompt 

# Now the structure looks like this '/usr/app/src/test.py'
RUN pip install --no-cache -r "requirements.txt"

#Labels as key value pair
LABEL Maintainer="Camilo Campos"

#CMD instruction should be used to run the software
#contained by your image, along with any arguments.

CMD [ "python", "./main.py"]
