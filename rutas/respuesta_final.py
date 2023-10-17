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
    pregunta_usuario = json_data['pregunta']#"¿Cuál es el cliente que ha realizado el mayor número de transacciones?"

    clasificacion_final= json_data['clasificacion']

    resultado_sql= json_data['resultado sql']





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
        user_question = translate(pregunta_usuario, from_language, target_language, example_1)

        
        examples_2 = """
        Example 1:
            User's question: I need the sales of the customers throughout the year 2023 in the categories Tools and Suspension.
            SQL query result: CUSTOMER_NAME: Customer A, CUSTOMER_ID: 201, PRODUCT_NAME: Product 4, PRODUCT_CODE: P004, PRODUCT_CATEGORY: Tools, PRODUCT_PRICE: 89.99, PRODUCTS_IN_STOCK: 75, PRODUCT_DATE_ADDED: 1691107200000, PRODUCT_DATE_MODIFIED: 1691107200000, PRODUCT_MANUFACTURER: Manufacturer C, PRODUCT_SUPPLIER: Supplier Z, DATE_SELL: 1691884800000, TIME_SELL: 16:15:00
            Response: Customers C and A are the only ones who have purchased products from the tools and suspension categories.
        Example 2:
            User's question: What are the top 5 products most purchased by the clients last year?
            SQL query result: PRODUCT_NAME: Product 1, PRODUCTS_PURCHASED: 6, PRODUCT_NAME: Product 4, PRODUCTS_PURCHASED: 6, PRODUCT_NAME: Product 2, PRODUCTS_PURCHASED: 4, PRODUCT_NAME: Product 5, PRODUCTS_PURCHASED: 4
            Response: The top 5 most purchased products are Product 1 with 6 PRODUCTS_PURCHASED, Product 4 with 6 PRODUCTS_PURCHASED, Product 2 with 4 PRODUCTS_PURCHASED, and Product 5 with 4 PRODUCTS_PURCHASED.

        Example 3:
            User's question: Which customers have made a transaction greater than 400?
            SQL query result: CUSTOMER_NAME: Customer C, CUSTOMER_ID: 203, CUSTOMER_NAME: Customer A, CUSTOMER_ID: 201
            Response: Customers C and A have made a transaction greater than 400.

        Example 4:
            User's question: Which customers bought the swimsuit product?
            SQL query result:0
            Response: No customer has a record in the database of any purchase of the swimsuit product.
            
        Example 5:
            User's question: How many sales of lion mask product are there?
            SQL query result:none
            Response: this product does not exist in our catalog.
            """
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

        humanized_response = FINAL_RESPONSE(user_question, resultado_sql, examples_2)
        

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
        print("estamos aqui")

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

        print(user_question)
        
        print("estamos aqui 2")
        examples_2 = """
        Example 1:
            User's question: how many years you have
            Response: I am a chatbot so I am not old. 
        Example 2:
            User's question: how can I get to Maria Antonia street
            Response: I am not qualified to provide this information

        Example 3:
            User's question: I want to know how to build a rocket to go to space
            Response: I don't have that knowledge to help you

        Example 4:
            User's question: i want to listen to a song anuel aa
            Response:  I can't access the internet and look for the song you are asking for.
            
        Example 5:
            User's question: how can i create a cake ?
            Response:  I do not have the information and knowledge to help you with the task you are asking for. 
            
        Example 5:
            User's question: can you do my work for me
            Response: I can't do your job that's your responsibility not mine.
        
            
            
        """
        
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
        print(humanized_response)
        target_language = "spanish"
        from_language = "english"
        print("estamos aqui 3")
        
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
        print("estamos aqui 4")
        return response_data

    