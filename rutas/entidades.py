from flask import Flask, request, jsonify
import requests
from ibm_cloud_sdk_core import IAMTokenManager
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, BearerTokenAuthenticator
import pandas as pd
import ibm_db_dbi as dbi
import os
from prompt.prompt import Prompt


app = Flask(__name__)

# Selección del modelo
model_id = os.getenv("MPT")

# Selección del ID del proyecto
project_id = os.getenv("IBM_WATSON_STUDIO_PROJECT_ID")

# Selección de la api key
api_key = os.getenv("IBM_CLOUD_API_KEY")

# Selección url
url_cloud = os.getenv("IBM_CLOUD_URL")



# Autenticación        
access_token = IAMTokenManager(
  apikey = api_key,
  url = url_cloud).get_token()

# Parámetros
parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 700,
    "repetition_penalty": 1
}



def extraccion_entidades(json_data):

    json_data = request.json
    

    if not json_data or 'pregunta' not in json_data:
        return jsonify({"error": "Invalid JSON format"}), 400    

    # Generación de sentencia SQL
    pregunta_usuario = json_data['pregunta']#"¿Cuál es el cliente que ha realizado el mayor número de transacciones?"

    ejemplos = json_data['ejemplos']


    import re

    def formatear_pregunta(pregunta_usuario):
        # Eliminar espacios en blanco adicionales
        pregunta_formateada = ' '.join(pregunta_usuario.split())
    
        # Convertir a minúsculas
        pregunta_formateada = pregunta_formateada.lower()
    
        # Eliminar caracteres especiales y signos de puntuación
        pregunta_formateada = re.sub(r'[^\w\s]', '', pregunta_formateada)
    
        return pregunta_formateada

    pregunta_formateada = formatear_pregunta(pregunta_usuario)
    #print(f"Pregunta formateada: {pregunta_formateada}")

    # Inicializa una cadena vacía para almacenar el texto combinado
    texto_combinado = "ejemplos = \"\"\"\n"

    # Recorre la lista de ejemplos y agrega cada ejemplo al texto combinado
    for i, ejemplo in enumerate(ejemplos, start=1):
        pregunta = ejemplo["pregunta_usuario"]
        respuesta = ejemplo["respuesta"]
        
        # Agrega el número de ejemplo, la pregunta y la respuesta al texto
        texto_combinado += f"ejemplo {i}:\n    Pregunta usuario : {pregunta}\n    respuesta : {respuesta}\n"

    # Agrega el cierre de la cadena
    texto_combinado += "\"\"\""
    



    def extracccion(texto, ejemplos):
        promptTuning = "Actúa como un webmaster que debe extraer información estructurada de textos en español. Lee el siguiente texto y extrae y categoriza cada entidad. Utiliza los ejemplos proporcionados solo como guía para seguir la estructura de extracción, pero no incluyas la información de los ejemplos en la respuesta.La respuesta solo debe devolver la extracion de la entidades y no responder las preguntas. Evita devolver la entrada, solo devuelve una unica respuesta y no entregues información adicional."
        prompt_text = f"instrucciones que debes seguir:{promptTuning}, \n ejemplos que debes utilizar para guiar tu extraccion : {ejemplos} ,\n texto para la extraccion :{texto}, \n Respuesta: "
    
        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)
    
        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)
        return resultado

    entidades = extracccion(pregunta_formateada, texto_combinado)
    
    
    response_data = {'Entidades': entidades}



    return response_data








