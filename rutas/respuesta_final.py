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
model_id = os.getenv("GRANITE")

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



def respuesta_humanizada(json_data):

    json_data = request.json
    

    if not json_data or 'pregunta' not in json_data:
        return jsonify({"error": "Invalid JSON format"}), 400    

    # Generación de sentencia SQL
    pregunta_usuario = json_data['pregunta']

    clasificacion_final= json_data['clasificacion']

    resultado_sql= json_data['resultado sql']

    ejemplos = json_data['ejemplos_1']

    ejemplos_2 = json_data['ejemplos_2']


    def generar_texto_combinado(ejemplos):
        texto_combinado = "Examples = \"\"\"\n"
        for i, ejemplo in enumerate(ejemplos, start=1):
            pregunta = ejemplo["pregunta_usuario"]
            texto_combinado += f"Example {i}:\n  User's question : {pregunta}\n  "
            if "entidades" in ejemplo:
                resultado_sql = ejemplo["resultado sql"]
                texto_combinado += f"  SQL query result : {resultado_sql} \n"
            respuesta = ejemplo["respuesta"]  
            texto_combinado += f"  Response : {respuesta} \n"
        texto_combinado += "\"\"\""
        return texto_combinado

    
    examples_1=generar_texto_combinado(ejemplos)
    examples_2=generar_texto_combinado(ejemplos_2)



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


    if clasificacion_final=="Valido" and resultado_sql:

        target_language = "english"

        from_language = "spanish"

        example_1 = """
        Example 1:
            User's question: Which customers bought the swimsuit product
            Response: Qué clientes compraron el bañador
        Example 2:
            User's question: tell me the products of the category suspension bought by customer camilo campos
            Response: tell me the products of the category suspension bought by customer camilo campos
            """

        def translate(text_to_translate, from_language, target_language, example):
            model_id_3="google/flan-t5-xxl"
            local_parameters = {
                "decoding_method": "greedy",
                "max_new_tokens": 200,
                "repetition_penalty": 1
            }
            try:
                instrucciones = f"translate from {from_language} to {target_language}: {text_to_translate} "
                prompt = Prompt(access_token, project_id)
                resultado = prompt.generate(instrucciones, model_id_3, local_parameters)
                return (resultado)
            except Exception as e:
                return (False, str(e))
        user_question = translate(pregunta_usuario, from_language, target_language, example_1)
        result_sql = translate(resultado_sql , from_language, target_language, example_1)

        
        def FINAL_RESPONSE(user_question, informacion_texto, examples):
            instruction_adjustment = f"You should analyze the user's question and the text information to provide a humanized response. If the query result is a number  or if it is empty then it returns as a response that there are no records in the database , respond accordingly. Provide the correct response to the user's question.only returns a single answer to the user's question"
            prompt_text = f"Instructions to follow: {instruction_adjustment}. \n examples that you should use as a guide for your answer and you should not include information from the examples in the answer:{examples}.\nUser's question: {user_question}.\nSQL query result: {informacion_texto}.\n Response:"

            # Create an object of the Prompt class (make sure you have access_token and project_id defined previously)
            prompt = Prompt(access_token, project_id)

            # Call the generate method with the text string instead of the Prompt object
            result = prompt.generate(prompt_text, model_id, parameters)

            response = ""
            for line in result.splitlines():
                if "." in line:
                    response = line
                    break
            return result

        humanized_response = FINAL_RESPONSE(user_question, result_sql, examples_1)
        

        target_language = "spanish"
        from_language = "english"

        example_3 = """
        Example 1:
            User's question: Which customers bought the swimsuit product
            Response: Qué clientes compraron el bañador

        Example 2:
            User's question: tell me the products of the category suspension bought by customer camilo campos
            Response: tell me the products of the category suspension bought by customer camilo campos"""

        def translate(text_to_translate, from_language, target_language, example):
            model_id_3="google/flan-t5-xxl"
            local_parameters = {
                "decoding_method": "greedy",
                "max_new_tokens": 200,
                "repetition_penalty": 1
            }
            try:
                instrucciones = f"translate from {from_language} to {target_language}: {text_to_translate} "
                prompt = Prompt(access_token, project_id)
                resultado = prompt.generate(instrucciones, model_id_3, local_parameters)

                return (resultado)
            except Exception as e:
                return (False, str(e))

        pregunta_usuario_ingles = translate(humanized_response, from_language, target_language, example_3)
        
        response_data = {'respuesta humanizada': pregunta_usuario_ingles }
        return response_data
        
    elif clasificacion_final=="No Valido":
        target_language = "english"
        from_language = "spanish"
        

        def translate(text_to_translate, from_language, target_language):
            model_id_3="google/flan-t5-xxl"
            local_parameters = {
                "decoding_method": "greedy",
                "max_new_tokens": 200,
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

        
        
        def FINAL_RESPONSE(user_question, examples):
            instruction_adjustment = f"You should analyze the user's question and the text information to provide a humanized response. If the query result is a number  or if it is empty then it returns as a response that there are no records in the database , respond accordingly. Provide the correct response to the user's question.only returns a single answer to the user's question"
            prompt_text = f"Instructions to follow: {instruction_adjustment}. \n examples that you should use as a guide for your answer and you should not include information from the examples in the answer:{examples}.\nUser's question: {user_question}.\n Response:"

            # Create an object of the Prompt class (make sure you have access_token and project_id defined previously)
            prompt = Prompt(access_token, project_id)

            # Call the generate method with the text string instead of the Prompt object
            result = prompt.generate(prompt_text, model_id, parameters)

            response = ""
            for line in result.splitlines():
                if "." in line:
                    response = line
                    break
            return result

        humanized_response = FINAL_RESPONSE(user_question, examples_2)
        
        target_language = "spanish"
        from_language = "english"
        
        
        def translate(text_to_translate, from_language, target_language):
            model_id_3="google/flan-t5-xxl"
            local_parameters = {
                "decoding_method": "greedy",
                "max_new_tokens": 200,
                "repetition_penalty": 1
            }
            try:
                instrucciones = f"translate from {from_language} to {target_language}: {text_to_translate} "
                prompt = Prompt(access_token, project_id)
                resultado = prompt.generate(instrucciones, model_id_3, local_parameters)
                return (resultado)
            except Exception as e:
                return (False, str(e))
        
        pregunta_usuario_ingles  = translate(humanized_response, from_language, target_language)

        response_data = {'respuesta humanizada': pregunta_usuario_ingles }

        return response_data

    