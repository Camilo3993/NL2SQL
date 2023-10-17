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
    
    

    ejemplos = """
    Ejemplo 1:
        Pregunta: Necesito las ventas de los cliente para todo el año 2023 en las categorías Herramientas y Suspensión.
        Entidades: entidad:cliente, fecha: 2023, categorias: herramientas, suspensión
        Clasificacion:  Valido.

    Ejemplo 2:
        Pregunta: cuales son los 5 productos mas comprado por los clientes el año pasado.
        Entidades: entidad: cliente, fecha: año pasado, entidad: productos , condicion : mas comprados , valor : 5
        Clasificacion: Valido.

    Ejemplo 3:
        Pregunta: Cuántos productos diferentes se vendieron?.
        Entidades: entidad: producto, condición: diferentes
        Clasificacion: Valido.

    Ejemplo 4:
        Pregunta: Cuáles son los clientes que compraron el producto traje de baño.
        Entidades: producto: traje de baño, entidad: cliente
        Clasificacion: Valido.

    Ejemplo 5:
        Pregunta: necesito el promedio de ventas por dia durante marzo .
        Entidades: entidad: ventas, condicion: promedio, fecha: marzo
        Clasificacion: Valido
  
    Ejemplo 6:
        Pregunta: jdjdjdj cual es el vendedor que ha vendido mas en abril ssmssmmsmsms
        Entidades: entidad: vendedor, condicion: mas ventas, fecha: abril
        Clasificacion: Valido

    Ejemplo 7:
        Pregunta: las ballenas viven donde
        Entidades: entidad: ballenas, lugar: donde viven las ballenas
        Clasificacion: No Valido

    Ejemplo 8:
        Pregunta: cuanto es 2 + 2 . 
        Entidades: entidad: numero , condicion: sumar , valor: 2
        Clasificacion: No valido .

    Ejemplo 9:
        Pregunta: scncckmskcscn nvmcddnvn.
        Entidades: entidad: scncckmskcscn, entidad: nvmcddnvn
        Clasificacion: No valido.

    Ejemplo 10:
        Pregunta: donde viven los peces .
        Entidades: entidad: peces, lugar: donde viven los peces
        Clasificacion: No Valido

    Ejemplo 11:
        Pregunta: como puedo crear un torta
        Entidades: entidad:crear , entidad:torta
        Clasificacion: No Valido

    Ejemplo 12:
        Pregunta: como puedo llegar a la calle maria antonia
        Entidades: entidad: calle, nombre: maria antonia
        Clasificacion: No Valido

    Ejemplo 13:
        Pregunta: donde queda la calle camilo campos
        Entidades: entidad: calle, nombre: camilo campos
        Clasificacion: No Valido

    Ejemplo 14:
        Pregunta: quiero saber como construir un cohete para ir al espacio
        Entidades: entidad: cohete, valor: ir al espacio, entidad: construir, valor: cohete
        Clasificacion: No Valido

    Ejemplo 15:
        Pregunta: puedes hacer mi trabajo por mi
        Entidades:entidad: mi trabajo, valor: por mi
        Clasificacion: No Valido

    Ejemplo 16:
        Pregunta: Cuantos años tienes .
        Entidades: entidad: años, condicion: tienes
        Clasificacion: No valido.

    Ejemplo 17:
        Pregunta:cual es el valor de la mascara panda
        Entidades: producto, valor: mascara de panda
        Clasificacion: Valido

    Ejemplo 18:
        Pregunta:cuál es el vendedor que ha realizado la venta más costosa en una sola transacción
        Entidades: entidad: vendedor, condicion: venta más costosa , valor: una sola transacción
        Clasificacion: Valido

    Ejemplo 19:
        Pregunta:cuántos clientes tienen direccion del cliente vacio
        Entidades: entidad: cliente, condicion: vacio , valor : direccion del cliente
        Clasificacion: Valido

    Ejemplo 20:
        Pregunta:Cuál es la fecha y hora de la ultima transacción registrada
        Entidades:entidad: fecha y hora, valor: la ultima transacción registrada
        Clasificacion: Valido

    """


    def clasificacion(texto, entidades, ejemplos):
        promptTuning = "Clasifica la pregunta proporcionada como los valores 'Valido' o 'No valido' su naturaleza y los valores de sus entidades. Para clasificar las preguntas como Validas compara las entidades de la pregunta con los ejemplos si son similares es Valida y para las preguntas No validas haz lo mismo .Debes usar los ejemplos solo como guia para tu clasificacion pero no incluyas información de los ejemplos en la respuesta. Evita devolver la entrada original y solo entrega una clasificación. No repitas informacion ."

        prompt_text = f"Instrucciones que debes seguir: {promptTuning}\nEjemplos para guiar la clasificación:{ejemplos}\nPregunta a clasificar: {texto}\nEntidades de la pregunta:{entidades}\nClasificación: "
        #print(prompt_text)
        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)

        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)
        return resultado

    clasificacion_ = clasificacion(pregunta_formateada , entidades , ejemplos)
    
    
    
    ejemplos = """
    Ejemplo 1:
    Pregunta: Necesito las ventas de los cliente para todo el año 2023 en las categorías Herramientas y Suspensión.
    Clasificacion:  Valido

    Ejemplo 2:
    Pregunta: cuales son los 5 productos mas comprado por los clientes el año pasado
    Clasificacion: Valido
    
    Ejemplo 3:
    Pregunta: quiero saber cual vendedor a vendido mas el producto iphone 10
    Clasificacion: Valido

    Ejemplo 4:
    Pregunta: Cuantos años tienes 
    Clasificacion: No valido

    Ejemplo 5:
    Pregunta: Cuáles son los clientes que compraron el producto traje de baño
    Clasificacion: Valido

    Ejemplo 6:
    Pregunta: scncckmskcscn nvmcddnvn
    Clasificacion: No valido

    Ejemplo 7:
    Pregunta: Cuántos productos diferentes se vendieron?
    Clasificacion: Valido
    
    Ejemplo 8:
    Pregunta: cuanto es 2 + 2  
    Clasificacion: No valido 
    
    Ejemplo 9:
    Pregunta: necesito el promedio de ventas durante enero por el vendedor Camilo  
    Clasificacion: Valido
    
    Ejemplo 10:
    Pregunta: jdjdjdj cual es el vendedor que ha vendido mas en abril ssmssmmsmsms
    Clasificacion: Valido
    
    Ejemplo 11:
    Pregunta: necesito saber cual es el vendedor con mas ventas durante junio
    Clasificacion: Valido
    
    Ejemplo 12:
    Pregunta: cuál es el cliente que ha gastado más dinero en total
    Clasificacion: Valido
    
    Ejemplo 13:
    Pregunta:cual es el valor de la mascara panda
    Clasificacion: Valido
    
    Ejemplo 14:
    Pregunta:cuál es el cliente que ha realizado el mayor número de transacciones
    Clasificacion: Valido
    
    Ejemplo 15:
    Pregunta:cuál es el producto con el precio mas alto
    Clasificacion: Valido
    
    Ejemplo 16:
    Pregunta: cuántos productos se vendieron en cada una de las categorías de productos
    Clasificacion: Valido
    
    Ejemplo 17:
    Pregunta:cuál es el vendedor que ha realizado la venta más costosa en una sola transacción
    Clasificacion: Valido
    
    Ejemplo 18:
    Pregunta:cuál es el producto más vendido en la categoría repuestos ordenados por el nombre
    Clasificacion: Valido
    
    Ejemplo 19:
    Pregunta:cuál es el promedio de ventas de los productos por día
    Clasificacion: Valido
    
    Ejemplo 20:
    Pregunta:cuantos productos de la categoria electronica se han vendido
    Clasificacion: Valido
    
    Ejemplo 21:
    Pregunta:cuántos clientes tienen direccion del cliente vacio
    Clasificacion: Valido

    Ejemplo 22:
    Pregunta:Cuál es la fecha y hora de la ultima transacción registrad
    Clasificacion: Valido

    
    """

    def clasificacion(texto, ejemplos):
        promptTuning = "Debes analizar las palabras claves de la pregunta y Clasificar la pregunta proporcionada como Valido o No valido según su naturaleza .Solo devuelve una vez nomas la clasificacion. Las preguntas Válidas deben estar relacionadas con productos, vendedores, clientes, número de ventas, total de ventas, promedio de ventas, transacciones , entre otros, mientras que las preguntas No válidas deben estar relacionadas con temas como el clima, series, cocina, danza, música, preguntas sobre la edad, sobre sentimientos y preguntas insultantes. No incluyas información de los ejemplos en la respuesta. Evita devolver la entrada original y solo entrega una clasificación. No repitas información."

        prompt_text = f"Instrucciones que debes seguir: {promptTuning}\nEjemplos para guiar la clasificación:{ejemplos}\nPregunta a clasificar: {texto}\nClasificación: "

        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)

        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)

        # Ahora, simplemente devolvemos la respuesta generada como está
        return resultado.strip()

    clasificacion_2 = clasificacion(pregunta_formateada, ejemplos)
    #print(f"Clasificación para la pregunta '{pregunta_formateada}': {clasificacion_1}")

    # Calcular la longitud deseada
    longitud_deseada = len("Novalido ")

    # Crear una cadena que combine la pregunta formateada, la clasificación y la etiqueta
    cadena_completa = f"{clasificacion_2}"

    # Asegurarse de que la cadena no supere la longitud deseada
    if len(cadena_completa) > longitud_deseada:
        cadena_completa = cadena_completa[:longitud_deseada]

    

    examples = """
    Example 1:
        Question: I need the sales of customers for the entire year 2023 in the categories Tools and Suspension.
        Entities: entity: customer, date: 2023, categories: tools, suspension
        Classification: Valido.

    Example 2:
        Question: What are the top 5 products purchased by customers last year?
        Entities: entity: customer, date: last year, entity: products, condition: most purchased, value: 5
        Classification: Valido.

    Example 3:
        Question: How many different products were sold?
        Entities: entity: product, condition: different
        Classification: Valido.

    Example 4:
        Question: Who are the customers that bought the swimsuit product?
        Entities: product: swimsuit, entity: customer
        Classification: Valido.

    Example 5:
        Question: I need the average daily sales during March.
        Entities: entity: sales, condition: average, date: March
        Classification: Valido

    Example 6:
        Question: How many products were sold in each of the product categories ?
        Entities: entity: categories, condition: products, value: sold
        Classification: Valido

    Example 7:
        Question: where the fish live.
        Entities: entity: fish, location: where fish live
        Classification: No valido

    Example 8:
        Question: how many years you have
        Entities: entity: years, condition: you have
        Classification: No valido.

    Example 9:
        Question: What is 2 + 2.
        Entities: entity: number, condition: add, value: 2
        Classification: No valido.

    Example 10:
        Question: how can I create a cake
        Entities: entity:create, entity:cake
        Classification: No valido

    Example 11:
        Question: how can I get to Maria Antonia street
        Entities: entity: street, name: maria antonia
        Classification: No valido

    Example 12:
        Question: where is Camilo Campos street located
        Entities: entity: street, name: camilo campos
        Classification: No valido

    Example 13:
        Question: I want to know how to build a rocket to go to space
        Entities: entity: rocket, value: go to space, entity: build, value: rocket
        Classification: No valido

    Example 14:
        Question: Can you do my work for me
        Entities: entity: my work, value: for me
        Classification: No valido
    
    Example 15:
        Question: meet pablo neruda
        Entities: entity: pablo neruda
        Classification: No valido
    
    Example 16:
        Question: scncckmskcscn nvmcddnvn.
        Entities: entity: scncckmskcscn, entity: nvmcddnvn
        Classification: No valido.
    
    Example 17:
        Question:i need to know how i can cut my dog's hair
        Entities: entity: dog, condition: shave the dog
        Classification: No valido.
    
    Example 18:
        Question: i want to listen to a song anuel aa
        Entities: entity: song, name: anuel aa
        Classification: No valido
    
    Example 19:
        Question:where the lions live
        Entities: entity: leones, location: where do leones live
        Classification: No valido.
    
    Example 20:
        Question:Which seller has made the most expensive sale in a single transaction ?
        Entities:entity: seller , condition: expensive sale , value: one transaction
        Classification: Valido.
    
    Ejemplo 21:
        Pregunta:How many customers have a blank customer address ?
        entidad:entity: customer , condition: empty , value: customer direction 
        Clasificacion: Valido
    
    """

    def classification(text, entities, examples):
        promptTuning = "Classify the provided question as 'Valido' or 'No Valido' values by its nature and the values of its entities. To classify questions as Valido compare the entities of the question with the examples if they are similar it is Valido and for invalid questions do the same. You should use the examples only as a guide for your classification but do not include information from the examples in the answer. Avoid returning the original input and only provide a rating. Do not repeat information "
        
        prompt_text = f"Instructions to follow: {promptTuning}\nExamples to guide classification:{examples}\nQuestion to classify: {text}\nQuestion's entities:{entities}\nClassification: "
        
        # Create a Prompt object (make sure you have access_token and project_id defined previously)
        prompt = Prompt(access_token, project_id)
        
        # Call the generate method with the text string instead of the Prompt object
        result = prompt.generate(prompt_text, model_id_2, parameters)
        return result

    classification_ = classification(user_question, entities, examples)
    
    

    examples = """
    Example 1:
        Question: I need the sales of customers for the entire year 2023 in the categories Tools and Suspension.
        Classification: Valido.

    Example 2:
        Question: What are the top 5 products purchased by customers last year?
        Classification: Valido.

    Example 3:
        Question: How many different products were sold?
        Classification: Valido.

    Example 4:
        Question: Who are the customers that bought the swimsuit product?
        Classification: Valido.

    Example 5:
        Question: I need the average daily sales during March.
        Classification: Valido

    Example 6:
        Question: how many years you have
        Classification: No valido.

    Example 7:
        Question: What is 2 + 2.
        Classification: No valido.

    Example 8:
        Question: scncckmskcscn nvmcddnvn.
        Classification: No valido.
    
    Example 9:
        Question: meet pablo neruda
        Classification: No valido.
    
    Example 10:
        Question: i want to listen to a song anuel aa
        Classification: No valido
    
    Example 11:
        Question: where the fish live.
        Classification: No valido
    
    Example 12:
        Question:i need to know how i can cut my dog's hair
        Classification: No valido.
    
    Example 13:
        Question:how can i create a cake ?
        Classification: No valido.
    
    Example 14:
        Question:where the lions live
        Classification: No valido.
    
    Example 15:
        Question:where the lions live
        Classification: No valido.
    
    Example 16:
        Question: How many products were sold in each of the product categories ?
        Classification: Valido
    
    Example 17:
        Question: Which is the client that has spent the most money in total ?
        Classification: Valido
    
    Ejemplo 21:
        Pregunta:How many customers have a blank customer address ? 
        Clasificacion: Valido

    """

    def classification(text, examples):
        promptTuning = "Classify the provided question as 'Valido' or 'No valido' based on its nature. Valid questions should be related to products, sellers, customers, total amounts, or transactions only in that. Not valid questions should be related to weather , tvshow , cook , dance , series  ,  when asked about age, where live animals. Do not include information from the examples in your response. Avoid returning the original input, only the classification."
        
        prompt_text = f"instructions to follow: {promptTuning}\nExamples to guide classification:{examples}\nQuestion to classify: {text}\nClassification: "
        
        # Create an object of the Prompt class (make sure to have access_token and project_id defined previously)
        prompt = Prompt(access_token, project_id)
        
        # Call the generate method with the text string instead of the Prompt object
        result = prompt.generate(prompt_text, model_id_2, parameters)
        return result

    classification_2 = classification(user_question, examples)
    #print(f"Clasificación para la pregunta '{pregunta_formateada}': {classification_2}")

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
    variables_limpias = [variable.replace('\n\nP', '').replace('\nNo', '').replace('.', '').strip()  for variable in variables]


    #print(variables_limpias)

    # Cuenta cuántas veces aparece "Valido" y "No Valido".
    conteo_valido = variables_limpias.count("Valido")
    conteo_no_valido = variables.count("No Valido")

    clasificacion_final=""

    # Define una condición para tomar una decisión.
    if conteo_valido >= 3:
        # Si hay 3 o más "Valido", ejecuta este código.
        clasificacion_final="Valido"
        
        
    else:
        clasificacion_final="No Valido"
        


    response_data = {'Clasificacion': clasificacion_final}



    return response_data