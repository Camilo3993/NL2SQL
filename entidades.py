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
    print("aqui estamos")

    if not json_data or 'pregunta' not in json_data:
        return jsonify({"error": "Invalid JSON format"}), 400    

    # Generación de sentencia SQL
    pregunta_usuario = json_data['pregunta']#"¿Cuál es el cliente que ha realizado el mayor número de transacciones?"


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
    print("aqui estamos 2 ")


    ejemplos = """
    Ejemplo 1:
      Texto: Necesito las ventas de los cliente para todo el año 2023 en las categorías Herramientas y Suspensión.
      Respuesta:  entidad: cliente ,fecha: 2023, categorias: herramientas, suspensión 

    Ejemplo 2:
      Texto: cuales son los 5 productos de todas las categoria A mas comprado por los clientes el año pasado
      Respuesta: entidad: cliente, fecha: año pasado, entidad: productos , condicion : mas comprados , valor : 5 , condicion:todas las categorias

    Ejemplo 3:
      Texto: Cuál es el total de ventas realizadas por el vendedor que ha trabajado menos.
      Respuesta: entidad: vendedor, objetivo: trabajado menos, valor: total de ventas

    Ejemplo 4:
      Texto: Cuáles son los clientes que compraron el producto traje de baño
      Respuesta: producto: traje de baño, entidad: cliente

    Ejemplo 5:
      Texto: Cuáles fueron los gastos totales para el mes de junio de 2023?
      Respuesta: fecha: 2023, mes: junio, valor: gastos totales

    Ejemplo 6:
      Texto: Cuántos productos diferentes se vendieron?
      Respuesta: entidad: producto, condición: diferentes
  
    Ejemplo 7:
      Texto: cual es el cliente que hecho mas compras en la tienda 
      Respuesta: entidad: cliente, condición: mas compras 
  
    Ejemplo 8:
      Texto: necesito las ventas del cliente Constructora Campos durante todo el año 2021 
      Respuesta: entidad: cliente,nombre :Constructora Campos, entidad: ventas , fecha : 2021 , valor :todo
  
    Ejemplo 9:
      Texto: Cuál es el cliente que ha realizado mas de 10 transacciones en el mes de mayo 
      Respuesta: entidad: cliente, entidad:transacciones  , condicion : mas de 10 transacciones , fecha: mayo , fecha: mes
  
    Ejemplo 10:
      Texto: quien es el vendedor que aumentado sus ventas durante el año 2023
      Respuesta: entidad: vendedor, condicion : aumentado ventas , fecha: 2023
  
    Ejemplo 11:
      Texto:  Cuál es el nombre del gerente con más experiencia
      Respuesta: entidad: gerente, condicion : mas experiencia 
  
    Ejemplo 12:
      Texto: Cuántos vendedores llevan mas de 2 años trabajando
      Respuesta: entidad: vendedor, condicion : mas de 2 años
  
    Ejemplo 13:
      Texto: porque el pasto es verde
      Respuesta: entidad: pasto , valor :verde

    Ejemplo 14:
      Texto: necesito saber cual es el vendedor con mas ventas durante junio
      Respuesta: entidad: vendedor , condicion : mas ventas , fecha : junio
  
    Ejemplo 15:
      Texto: cuanto es 2 + 2 
      Respuesta: entidad: numero , condicion: sumar , valor: 2 
  
    Ejemplo 16:
      Texto: cuál es el numero de ventas realizadas por cada vendedor
      Respuesta: entidad: vendedor , condicion: por cada vendedor , valor: numero de ventas
  
    Ejemplo 17:
      Texto: cuántos clientes tienen direccion del cliente vacio
      Respuesta: entidad: cliente, condicion: vacio , valor : direccion del cliente
      """


    def extracccion(texto, ejemplos):
        promptTuning = "Actúa como un webmaster que debe extraer información estructurada de textos en español. Lee el siguiente texto y extrae y categoriza cada entidad. Utiliza los ejemplos proporcionados solo como guía para seguir la estructura de extracción, pero no incluyas la información de los ejemplos en la respuesta.La respuesta solo debe devolver la extracion de la entidades y no responder las preguntas. Evita devolver la entrada, solo devuelve una unica respuesta y no entregues información adicional."
        prompt_text = f"instrucciones que debes seguir:{promptTuning}, \n ejemplos que debes utilizar para guiar tu extraccion : {ejemplos} ,\n texto para la extraccion :{texto}, \n Respuesta: "
    
        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)
    
        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)
        return resultado

    entidades = extracccion(pregunta_formateada, ejemplos)
    print("aqui estamos 3")
    response_data = {'Entidades': entidades}



    return response_data








