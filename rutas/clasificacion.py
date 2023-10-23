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

# Selección del modelo
model_id_2 = os.getenv("GRANITE")

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

def clasificacion_pregunta(json_data):

    json_data = request.json
    

    if not json_data or 'pregunta' not in json_data:
        return jsonify({"error": "Invalid JSON format"}), 400    

    # guardamos la pregunta del usuario
    pregunta_usuario = json_data['pregunta']

    # guardamos las entidades de la pregunta
    entidades = json_data['entidades']

    ejemplos_1 = json_data['ejemplos_1']

    ejemplos_2 = json_data['ejemplos_2']

    examples_1 = json_data['examples_1']

    examples_2 = json_data['examples_2']

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


    def generar_texto_combinado(ejemplos):
        texto_combinado = "ejemplos = \"\"\"\n"
        for i, ejemplo in enumerate(ejemplos, start=1):
            pregunta = ejemplo["pregunta_usuario"]
            texto_combinado += f"ejemplo {i}:\n  Pregunta usuario : {pregunta}\n"
            if "entidades" in ejemplo:
                entidades = ejemplo["entidades"]
                texto_combinado += f"\n     Entidades : {entidades}\n"
            clasificacion = ejemplo["clasificacion"]
            texto_combinado += f"\n     Clasificacion : {clasificacion}\n"
        texto_combinado += "\"\"\""
        return texto_combinado

    def generar_texto_combinado_2(ejemplos):
        texto_combinado = "Examples = \"\"\"\n"
        for i, ejemplo in enumerate(ejemplos, start=1):
            pregunta = ejemplo["pregunta_usuario"]
            texto_combinado += f"Example {i}:\n  Question : {pregunta}\n"
            if "entidades" in ejemplo:
                entidades = ejemplo["entidades"]
                texto_combinado += f"  Entities : {entidades}\n"
            clasificacion = ejemplo["clasificacion"]
            texto_combinado += f"  Classification : {clasificacion}\n"
        texto_combinado += "\"\"\""
        return texto_combinado

    # Generar el texto combinado para cada conjunto de ejemplos
    texto_combinado_1 = generar_texto_combinado(ejemplos_1)
    texto_combinado_2 = generar_texto_combinado(ejemplos_2)
    texto_combinado_3 = generar_texto_combinado_2(examples_1)
    texto_combinado_4 = generar_texto_combinado_2(examples_2)


    target_language = "english"
    from_language = "spanish"


    def translate(text_to_translate, from_language, target_language):
        model_id_3="google/flan-t5-xxl"
        local_parameters = {
            "decoding_method": "greedy",
            "max_new_tokens": 500,
            "repetition_penalty": 1
        }
        try:
            instrucciones = f"translate from {from_language} to {target_language}: {text_to_translate} "
            prompt = Prompt(access_token, project_id)
            resultado = prompt.generate(instrucciones, model_id_3, local_parameters)
            return (resultado)
        except Exception as e:
            return (False, str(e))

    user_question = translate(pregunta_usuario, from_language, target_language)
    entities =  translate(entidades, from_language, target_language)


    def clasificacion(texto, entidades, ejemplos):
        promptTuning = "Clasifica la pregunta proporcionada como los valores 'Valido' o 'No Valido' su naturaleza y los valores de sus entidades. Para clasificar las preguntas como Validas compara las entidades de la pregunta con los ejemplos si son similares es Valida y para las preguntas No Validas haz lo mismo .Debes usar los ejemplos solo como guia para tu clasificacion pero no incluyas información de los ejemplos en la respuesta. Evita devolver la entrada original y solo entrega una clasificación. No repitas informacion ."

        prompt_text = f"Instrucciones que debes seguir: {promptTuning}\nEjemplos para guiar la clasificación:{ejemplos}\nPregunta a clasificar: {texto}\nEntidades de la pregunta:{entidades}\nSolo devuelve la Clasificación: "
        #print(prompt_text)
        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)

        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)
        return resultado

    clasificacion_ = clasificacion(pregunta_formateada , entidades , texto_combinado_1)
    # Para acortar la variable y tomar solo los primeros 10 caracteres, puedes hacer lo siguiente:
    
    
    

    def clasificacion2(texto, ejemplos):
        promptTuning = "Debes analizar las palabras claves de la pregunta y Clasificar la pregunta proporcionada como Valido o No Valido según su naturaleza .Solo devuelve una vez nomas la clasificacion. Las preguntas Válidas deben estar relacionadas con productos, vendedores, clientes, número de ventas, total de ventas, promedio de ventas, transacciones , entre otros, mientras que las preguntas No Válidas deben estar relacionadas con temas como el clima, series, cocina, danza, música, preguntas sobre la edad, sobre sentimientos y preguntas insultantes. No incluyas información de los ejemplos en la respuesta. Evita devolver la entrada original y solo entrega una clasificación. No repitas información."

        prompt_text = f"Instrucciones que debes seguir: {promptTuning}\nEjemplos para guiar la clasificación:{ejemplos}\nPregunta a clasificar: {texto}\nSolo devuelve la Clasificación: "

        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)

        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)

        # Ahora, simplemente devolvemos la respuesta generada como está
        return resultado.strip()

    clasificacion_2 = clasificacion2(pregunta_formateada, texto_combinado_2)

    # Calcular la longitud deseada
    longitud_deseada = len("Novalido ")

    # Crear una cadena que combine la pregunta formateada, la clasificación y la etiqueta
    cadena_completa = f"{clasificacion_2}"

    # Asegurarse de que la cadena no supere la longitud deseada
    if len(cadena_completa) > longitud_deseada:
        cadena_completa = cadena_completa[:longitud_deseada]

    


    def classification(text, entities, examples):
        promptTuning = "Classify the provided question as 'Valido' or 'No Valido' values by its nature and the values of its entities. To classify questions as Valido compare the entities of the question with the examples if they are similar it is Valido and for invalid questions do the same. You should use the examples only as a guide for your classification but do not include information from the examples in the answer. Avoid returning the original input and only provide a rating. Do not repeat information "
        
        prompt_text = f"Instructions to follow: {promptTuning}\nExamples to guide classification:{examples}\nQuestion to classify: {text}\nQuestion's entities:{entities}\nClassification: "
        
        # Create a Prompt object (make sure you have access_token and project_id defined previously)
        prompt = Prompt(access_token, project_id)
        
        # Call the generate method with the text string instead of the Prompt object
        result = prompt.generate(prompt_text, model_id_2, parameters)
        return result

    classification_ = classification(user_question, entities, texto_combinado_3)
    
    

    def classification2(text, examples):
        promptTuning = "You must analyze the key words of the question and Classify the provided question as Valido or No Valido according to its nature, returning only once the classification. Valido questions should be related to products, vendors, customers, number of sales, total sales, average sales, transactions, among others, while No Valido questions should be related to topics such as weather, series, cooking, dance, music, questions about age, about feelings and insulting questions. Do not include information from the examples in the answer. Avoid returning the original entry and only provide a rating. Do not repeat information."
        
        prompt_text = f"instructions to follow: {promptTuning}\nExamples to guide classification:{examples}\nQuestion to classify: {text}\n only returns the classification: "
        
        # Create an object of the Prompt class (make sure to have access_token and project_id defined previously)
        prompt = Prompt(access_token, project_id)
        
        # Call the generate method with the text string instead of the Prompt object
        result = prompt.generate(prompt_text, model_id_2, parameters)
        return result

    classification_2 = classification2(user_question, texto_combinado_4)


    # Calcular la longitud deseada
    longitud_deseada = len(pregunta_formateada) + len("No valido") + len("Clasificación para la pregunta:       ")

    # Crear una cadena que combine la pregunta formateada, la clasificación y la etiqueta
    cadena_completa_2 = f"Clasificación para la pregunta '{pregunta_formateada}' : {classification_2}"

    # Asegurarse de que la cadena no supere la longitud deseada
    if len(cadena_completa) > longitud_deseada:
        cadena_completa = cadena_completa[:longitud_deseada]

    # Crea una lista con tus variables para facilitar la comprobación.
    variables = [clasificacion_, cadena_completa, classification_, classification_2]
    
    

    # Utiliza una lista de comprensión para reemplazar '\n\nP' con una cadena vacía en la segunda cadena
    variables_limpias = [variable.replace('\n\nP', '').replace('\n', '').replace('.', '').strip()  for variable in variables]

    print(variables_limpias)
    # Cuenta cuántas veces aparece "Valido" y "No Valido".
    conteo_valido = variables_limpias.count("Valido")
    conteo_no_valido = variables.count("No Valido")

    total=conteo_valido - conteo_no_valido
    

    clasificacion_final=""

    # Define una condición para tomar una decisión.
    if total >= 3:
        # Si hay 3 o más "Valido", ejecuta este código.
        clasificacion_final="Valido"
    else:
        clasificacion_final="No Valido"
        


    response_data = {'Clasificacion': clasificacion_final}



    return response_data