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

def sentencia_sql(json_data):

    json_data = request.json
    

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

    # Define el diccionario de modelo de datos con la estructura esperada
    dataModel = {
        "tables": [
        {
            "tableName": "SALES",
            "columns": [
                {
                    "columnId": 1,
                    "columnName": "ID_SALES",
                    "columnType": "BIGINT",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 2,
                    "columnName": "PRODUCT_NAME",
                    "columnType": "VARCHAR",
                    "description": "this is name of the product sold"
                },
                {
                    "columnId": 3,
                    "columnName": "PRODUCT_CODE",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 4,
                    "columnName": "PRODUCT_CATEGORY",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 5,
                    "columnName": "CATEGORY_CODE",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 6,
                    "columnName": "PRODUCT_PRICE",
                    "columnType": "DECIMAL",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 7,
                    "columnName": "PRODUCTS_IN_STOCK",
                    "columnType": "INTEGER",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 8,
                    "columnName": "PRODUCT_DATE_ADDED",
                    "columnType": "TIMESTAMP",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 9,
                    "columnName": "PRODUCT_DATE_MODIFIED",
                    "columnType": "TIMESTAMP",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 10,
                    "columnName": "PRODUCT_MANUFACTURER",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 11,
                    "columnName": "PRODUCT_SUPPLIER",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales",
                    "useForTraining" : True
                },
                {
                    "columnId": 12,
                    "columnName": "DATE_SELL",
                    "columnType": "DATE",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 13,
                    "columnName": "TIME_SELL",
                    "columnType": "TIME",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 14,
                    "columnName": "SELLER_ID",
                    "columnType": "INTEGER",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 15,
                    "columnName": "SELLER_NAME",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 16,
                    "columnName": "SELLER_CATEGORY",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 17,
                    "columnName": "CUSTOMER_ID",
                    "columnType": "INTEGER",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 18,
                    "columnName": "CUSTOMER_NAME",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 19,
                    "columnName": "CUSTOMER_ADDRESS",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 20,
                    "columnName": "CUSTOMER_PHONE_NUMBER",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                },
                {
                    "columnId": 21,
                    "columnName": "CUSTOMER_CATEGORY",
                    "columnType": "VARCHAR",
                    "description": "this is ID of sales"
                }
            ]
        }
    ]
    }

    def extractDatabaseModelInfo(dataModel):
        database_info_text = ""

        for table_info in dataModel["tables"]:
            table_name = table_info["tableName"]
            columns_info = []

            for column_info in table_info["columns"]:
                column_name = column_info["columnName"]
                column_type = column_info["columnType"]
                column_info_text = f"{column_name} ({column_type})"
                columns_info.append(column_info_text)

            table_info_text = f"Tabla {table_name} con los siguientes campos:  {', '.join(columns_info)}"
            database_info_text += table_info_text + "\n"

        return database_info_text

    # Ejemplo de uso:
    texto_descriptivo = extractDatabaseModelInfo(dataModel)

    ejemplos = """
    ejemplo 1:
        Pregunta usuario : Cuál es el total de ventas hasta la fecha 
        respuesta : SELECT SUM(PRODUCT_PRICE) AS Total_Ventas FROM SALES;
    ejemplo 2:
        Pregunta usuario : Cuál es el producto con el precio mas alto 
        respuesta :SELECT PRODUCT_NAME, PRODUCT_PRICE FROM SALES WHERE PRODUCT_PRICE = (SELECT MAX(PRODUCT_PRICE) FROM SALES);
    ejemplo 3:
        Pregunta usuario : Cuál es el numero de ventas realizadas por cada vendedor 
        respuesta : SELECT SELLER_ID ,  COUNT(*) as VENTAS FROM SALES GROUP BY SELLER_ID;
    ejemplo 4:    
        Pregunta usuario : cuantos productos diferentes se vendieron 
        respuesta : SELECT COUNT(DISTINCT PRODUCT_NAME) as PRODUCTOS_DIFERENTES FROM SALES ;
    ejemplo 5:
        Pregunta usuario : Cuántos productos de la categoría Repuestos se vendieron 
        respuesta :SELECT COUNT(*) as Repuestos FROM SALES WHERE PRODUCT_CATEGORY = 'Repuestos';
    ejemplo 6:
        Pregunta usuario : Cuál es el precio promedio de los productos 
        respuesta : SELECT AVG(PRODUCT_PRICE) as PROMEDIO_PRODUCTOS FROM SALES;
    ejemplo 7:
        Pregunta usuario : Cuántos clientes tienen 'CUSTOMER_ADDRESS'  vacio 
        respuesta : SELECT COUNT(*) as CUSTOMER_ADDRESS_VACIO  FROM SALES WHERE CUSTOMER_ADDRESS IS NULL;
    ejemplo 8:
        Pregunta usuario : Cuál es el cliente que ha realizado el mayor número de transacciones  
        respuesta : SELECT CUSTOMER_ID, COUNT(*) AS NUM_TRANS FROM SALES GROUP BY CUSTOMER_ID ORDER BY COUNT(*) DESC ;
    ejemplo 9:
        Pregunta usuario : Cuál es el nombre del vendedor con más experiencia 
        respuesta : SELECT SELLER_NAME FROM SALES GROUP BY SELLER_NAME ORDER BY (DAYS(MAX(DATE_SELL)) - DAYS(MIN(DATE_SELL))) DESC FETCH FIRST 1 ROWS ONLY;
    ejemplo 10:
        Pregunta usuario : Cuántos productos se vendieron en cada una de las categorías de productos 
        respuesta : SELECT PRODUCT_CATEGORY, COUNT(*) AS CANTIDAD_VENDIDO FROM SALES GROUP BY PRODUCT_CATEGORY;
    ejemplo 11:
        Pregunta usuario : Cuál es el cliente que ha realizado la compra más costosa en una sola transacción 
        respuesta : SELECT CUSTOMER_NAME, SUM(PRODUCT_PRICE) AS compra_mas_costosa FROM SALES GROUP BY CUSTOMER_NAME ORDER BY compra_mas_costosa DESC ;
    ejemplo 12:
        Pregunta usuario :Cuál es el producto más vendido en la categoría 'Repuestos' ordenados por el nombre 
        respuesta : SELECT PRODUCT_NAME FROM SALES WHERE PRODUCT_CATEGORY = 'Repuestos' ORDER BY PRODUCT_NAME;
    ejemplo 13:
        Pregunta usuario : Cuál es el cliente que ha gastado más dinero en total  
        respuesta : SELECT CUSTOMER_ID, SUM(PRODUCT_PRICE * PRODUCTS_IN_STOCK) AS TOTAL_GASTADO FROM SALES GROUP BY CUSTOMER_ID ORDER BY TOTAL_GASTADO DESC;
    ejemplo 14:
        Pregunta usuario : Cuál es el promedio de ventas de los productos por día  
        respuesta : SELECT DATE_SELL, AVG(PRODUCT_PRICE) AS Promedio_Ventas FROM SALES GROUP BY DATE_SELL; 
    ejemplo 15:
        Pregunta usuario : Cuál es la fecha y hora de la última transacción registrada 
        respuesta : SELECT DATE_SELL, TIME_SELL FROM SALES order by ID_SALES  DESC LIMIT 1;;
    ejemplo 16:
        Pregunta usuario : necesito las ventas del cliente constructora hidalgo para todo el año 2023 en las categorias Herramientas y Suspension 
        respuesta : SELECT SUM(SALES.PRODUCT_PRICE * SALES.PRODUCTS_IN_STOCK) AS TOTAL_SALES FROM SALES WHERE CUSTOMER_NAME = 'constructora hidalgo' AND PRODUCT_CATEGORY IN ('Herramientas', 'Suspension') AND DATE_SELL BETWEEN '2023-01-01' AND '2023-12-31';
    ejemplo 17:
        Pregunta usuario : Cuál es el vendedor que ha realizado la venta más costosa en una sola transacción 
        respuesta : SELECT SELLER_NAME FROM SALES WHERE PRODUCT_PRICE = (SELECT MAX(PRODUCT_PRICE) FROM SALES);
    """

    def queryFactory2(texto_descriptivo, pregunta_usuario , ejemplos):
        promptTuning = "traduce texto a sql , debes analizar la pregunta del usuario entendiendo que te esta solicitando y cual es el proposito de la pregunta , para construir la sentencia sql debes tomar en consideracion la descripción de la unica tabla y sus campos y los ejemplos que se te entregan para guiarte, solo devolver la sentencia sql , no repetir informacion y no inventar informacion ademas crea alias para darle mas entendimiento a la sentencia sql"
        prompt_text = f"instrucciones que debes seguir:{promptTuning},\n ejemplos que debes utilizar para guiarte : {ejemplos} ,\n descripción de la unica tabla y sus columnas de la base de datos que debes usar para construir la sentencia sql : {texto_descriptivo} ,\n pregunta del usuario que debes responder :{pregunta_usuario} \n  respuesta: "
        
        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)
        
        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)
        return resultado

    query = queryFactory2(texto_descriptivo, pregunta_formateada , ejemplos)

    print(query)

    def clasificacion_sql(text, examples):
        promptTuning = "Classify the provided values as 'exactly the same' , 'similar' , 'different' or 'not valid' by their similarity between the sql statement that provided the model and the examples. To classify questions as exactly the same compare the sql statement in the answer with the examples if they are the same it is exactly the same , for sql statements similar compare the sql statement in the answer with the examples if the results are the same but the sql statement is not similar in similar , for sql statements different compare the sql statement in the answer with the examples if the results are different and the sql statement is also different it is different and for sql statements not valid it is when the model delivers anything but a sql statement . You should use the examples only as a guide for your classification but do not include information from the examples in the answer. Avoid returning the original entry and only provide a classification. Do not repeat information "
        prompt_text = f"Instructions to follow: {promptTuning}\nExamples to guide classification:{examples}\nQuestion to classify: {text}\nClassification: "
        
        # Create a Prompt object (make sure you have access_token and project_id defined previously)
        prompt = Prompt(access_token, project_id)
        
        # Call the generate method with the text string instead of the Prompt object
        result = prompt.generate(prompt_text, model_id_2, parameters)
        return result

    #sql_clasificacion= clasificacion_sql()

    import pandas as pd
    import os, ibm_db, ibm_db_dbi as dbi, pandas as pd


    DB2DWH_dsn = 'DATABASE={};HOSTNAME={};PORT={};PROTOCOL=TCPIP;UID={uid};PWD={pwd};SECURITY=SSL'.format(
        'bludb',
        '125f9f61-9715-46f9-9399-c8177b21803b.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud',
        30426,
        uid='zkd63801',
        pwd='Huemul.DB.2023+'
    )

    conn = dbi.connect(DB2DWH_dsn)
    cursor = conn.cursor()


    #cursor.execute(query1)
    tabla_sales = pd.read_sql(query, conn )


    conn.commit()
    cursor.close()
    conn.close()
    #print(tabla_sales)
    datos=tabla_sales.to_json(orient ='index')

    import json
    from datetime import datetime

    # Parsear el JSON a un diccionario de Python
    data = json.loads(datos)

    # Inicializar una cadena de texto vacía para almacenar la información
    informacion_texto = ""
    from datetime import datetime

    # Recorrer el diccionario y agregar la información en formato de texto lineal
    for key, value in data.items():
        for subkey, subvalue in value.items():
            if subkey in ["DATE_SELL", "PRODUCT_DATE_ADDED", "TIME_SELL", "PRODUCT_DATE_MODIFIED"]:
                subvalue = subvalue / 1000.0  # Convertir de milisegundos a segundos (utiliza 1000.0 para asegurarte de obtener un valor decimal)
                fecha_formateada = datetime.utcfromtimestamp(subvalue).strftime('%d/%m/%Y')
                informacion_texto += f" {subkey} : {fecha_formateada}, "
            else:
                informacion_texto += f" {subkey} : {subvalue}, "
        informacion_texto = informacion_texto.rstrip(', ') + "\n"

    # Imprimir o usar la cadena de texto según tus necesidades
    print(informacion_texto)
    response_data = {
                    'sentencia SQL': query,
                    'resultado SQL': informacion_texto
                    }



    return response_data