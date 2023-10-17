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
    Pregunta usuario : Cuál es el nombre del vendedor con más experiencia \n respuesta : SELECT SELLER_NAME FROM SALES GROUP BY SELLER_NAME ORDER BY (DAYS(MAX(DATE_SELL)) - DAYS(MIN(DATE_SELL))) DESC FETCH FIRST 1 ROWS ONLY;
    Pregunta usuario : Cuántos productos únicos ha comprado cada cliente y cuál es el nombre del cliente que ha comprado la mayor cantidad de productos únicos.\nrespuesta : SELECT CUSTOMER_NAME, CUSTOMER_ID, COUNT(DISTINCT PRODUCT_NAME) AS PRODUCTOS_UNICOS_COMPRADOS FROM SALES GROUP BY CUSTOMER_NAME, CUSTOMER_ID ORDER BY PRODUCTOS_UNICOS_COMPRADOS DESC LIMIT 1;
    Pregunta usuario : Cuál es el vendedor que ha vendido productos en más categorías diferentes y cuántas categorías ha cubierto .\n  respuesta :SELECT SELLER_NAME, SELLER_ID, COUNT(DISTINCT PRODUCT_CATEGORY) AS CATEGORIAS_DIFERENTES FROM SALES GROUP BY SELLER_NAME, SELLER_ID ORDER BY CATEGORIAS_DIFERENTES DESC LIMIT 1;
    Pregunta usuario : Cuál es el producto más caro vendido por cada vendedor y en qué fecha se realizó esa venta. \n respuesta : SELECT SELLER_NAME, PRODUCT_NAME, MAX(PRODUCT_PRICE) AS PRECIO_MAXIMO, DATE_SELL FROM SALES GROUP BY SELLER_NAME, PRODUCT_NAME, DATE_SELL HAVING PRODUCT_PRICE = MAX(PRODUCT_PRICE);
    Pregunta usuario : Cuántos productos ha vendido cada vendedor en cada categoría, y quién es el vendedor con más ventas en una categoría específica \n respuesta :SELECT SELLER_NAME, PRODUCT_CATEGORY, COUNT(*) AS VENTAS FROM SALES GROUP BY SELLER_NAME, PRODUCT_CATEGORY HAVING VENTAS = ( SELECT MAX(VENTAS) FROM ( SELECT SELLER_NAME, PRODUCT_CATEGORY, COUNT(*) AS VENTAS FROM SALES GROUP BY SELLER_NAME, PRODUCT_CATEGORY ) AS VENTAS_POR_VENDEDOR_Y_CATEGORIA );
    Pregunta usuario : Cuántas categorías de vendedores existen \n respuesta :SELECT 'Cantidad Categorías', COUNT(DISTINCT(SELLER_CATEGORY)) FROM SALES;
    Pregunta usuario : Cuántos productos se vendieron en cada una de las categorías de productos \n respuesta :SELECT PRODUCT_CATEGORY, COUNT(*) AS COUNT_OF_PRODUCT_SOLD FROM SALES GROUP BY PRODUCT_CATEGORY
    Pregunta usuario : Cuál es la fecha y hora de la primera venta registrada \n respuesta : SELECT DATE_SELL, TIME_SELL FROM SALES order by ID_SALES  ASC LIMIT 1;
    Pregunta usuario : Cómo evolucionan las ventas mensuales del vendedor 104 a lo largo de todo el año 2023 \n respuesta : SELECT EXTRACT(MONTH FROM DATE_SELL) AS Mes, SUM(PRODUCT_PRICE) AS Ventas_Mensuales FROM  SALES WHERE  SELLER_ID = 104 AND EXTRACT(YEAR FROM DATE_SELL) = 2023 GROUP BY  EXTRACT(MONTH FROM DATE_SELL) ORDER BY  EXTRACT(MONTH FROM DATE_SELL);
    Pregunta usuario : Cuál es el porcentaje de ventas que representan los productos de la categoría Autos con respecto al total de ventas  \n respuesta : SELECT (SUM(CASE WHEN PRODUCT_CATEGORY = 'Autos' THEN PRODUCT_PRICE ELSE 0 END) / SUM(PRODUCT_PRICE)) * 100 AS Porcentaje_Ventas_Autos FROM SALES;
    Pregunta usuario : Cuál es el producto que ha tenido la mayor fluctuación en su precio a lo largo del año 2010 \n respuesta : SELECT PRODUCT_NAME, MAX(PRODUCT_PRICE) AS PRECIO_MAXIMO, MIN(PRODUCT_PRICE) AS PRECIO_MINIMO, (MAX(PRODUCT_PRICE) - MIN(PRODUCT_PRICE)) AS FLUCTUACION FROM SALES WHERE YEAR(DATE_SELL) = 2010 GROUP BY PRODUCT_NAME ORDER BY FLUCTUACION DESC LIMIT 1;
    Pregunta usuario : Cuántos clientes tienen 'CUSTOMER_PHONE_NUMBER'  vacio \n respuesta : SELECT COUNT(*) AS CUSTOMER_PHONE_NUMBER_Vacio FROM SALES WHERE CUSTOMER_PHONE_NUMBER IS NULL;
    Pregunta usuario : Cuántos vendedores llevan mas de 10 años trabajando \n respuesta :SELECT COUNT(*) AS VENDEDOR_CON_MAS_10_AÑOS FROM SALES WHERE SELLER_NAME LIKE '%>10%'
    Pregunta usuario : Cuál es el cliente que ha realizado compras en todas las categorías de productos disponibles \n respuesta :SELECT CUSTOMER_NAME FROM SALES GROUP BY CUSTOMER_NAME HAVING COUNT(DISTINCT PRODUCT_CATEGORY) = (SELECT COUNT(DISTINCT PRODUCT_CATEGORY) FROM SALES);
    Pregunta usuario : Cuál es el producto con el precio mas elevado \n respuesta : SELECT PRODUCT_NAME, PRODUCT_PRICE FROM SALES WHERE PRODUCT_PRICE = (SELECT MAX(PRODUCT_PRICE) FROM SALES)

    """

    def queryFactory2(texto_descriptivo, pregunta_usuario , ejemplos):
        promptTuning = "traduce texto a sql , debes analizar la pregunta del usuario entendiendo que te esta solicitando y cual es el proposito de la pregunta , para construir la sentencia sql debes tomar en consideracion la descripción de la unica tabla y sus campos y los ejemplos que se te entregan para guiarte, solo devolver la sentencia sql , no repetir informacion y no inventar informacion ademas crea alias para darle mas entendimiento a la sentencia sql"
        prompt_text = f"instrucciones que debes seguir:{promptTuning},\n ejemplos que debes utilizar para guiarte : {ejemplos} ,\n descripción de la unica tabla y sus columnas de la base de datos que debes usar para construir la sentencia sql : {texto_descriptivo} ,\n pregunta del usuario que debes responder :{pregunta_usuario} \n  respuesta: "
        
        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)
        
        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)
        return resultado

    query = queryFactory2(texto_descriptivo, pregunta_usuario , ejemplos)

    print(query)

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
    print(tabla_sales)
    datos=tabla_sales.to_json(orient ='index')

    import json
    from datetime import datetime

    # Parsear el JSON a un diccionario de Python
    data = json.loads(datos)

    # Inicializar una cadena de texto vacía para almacenar la información
    informacion_texto = ""

    # Recorrer el diccionario y agregar la información en formato de texto lineal
    for key, value in data.items():
        
        for subkey, subvalue in value.items():
            if subkey == "DATE_SELL":
                fecha_formateada = datetime.utcfromtimestamp(subvalue / 1000).strftime('%Y-%m-%d')
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