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

    # recibe la informacion de la base de datos
    dataModel = json_data['dataModel']

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

            table_info_text = f"Tabla {table_name} con los siguientes campos: {', '.join(columns_info)}"
            database_info_text += table_info_text + "\n"

        return database_info_text

    # Ejemplo de uso:
    texto_descriptivo = extractDatabaseModelInfo(dataModel)

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

    # Imprime el texto combinado
    #print(texto_combinado)

    
    

    def queryFactory2(texto_descriptivo, pregunta_usuario , ejemplos):
        promptTuning = "traduce texto a sql , debes analizar la pregunta del usuario entendiendo que te esta solicitando y cual es el proposito de la pregunta , para construir la sentencia sql debes tomar en consideracion la descripción de la unica tabla y sus campos y los ejemplos que se te entregan para guiarte, solo devolver la sentencia sql , no repetir informacion y no inventar informacion ademas crea alias para darle mas entendimiento a la sentencia sql"
        prompt_text = f"instrucciones que debes seguir:{promptTuning},\n ejemplos que debes utilizar para guiarte : {ejemplos} ,\n descripción de la unica tabla y sus columnas de la base de datos que debes usar para construir la sentencia sql : {texto_descriptivo} ,\n pregunta del usuario que debes responder :{pregunta_usuario} \n  respuesta: "
        
        # Crear un objeto de la clase Prompt (asegúrate de tener access_token y project_id definidos previamente)
        prompt = Prompt(access_token, project_id)
        
        # Llamar al método generate con la cadena de texto en lugar del objeto Prompt
        resultado = prompt.generate(prompt_text, model_id, parameters)
        return resultado

    query = queryFactory2(texto_descriptivo, pregunta_formateada , texto_combinado)

    print(query)

    import re

    def formatear_pregunta(pregunta_usuario):
        # Eliminar espacios en blanco adicionales
        pregunta_formateada = ' '.join(pregunta_usuario.split())
    
        # Reemplazar saltos de línea por espacios en blanco
        pregunta_formateada = pregunta_formateada.replace('\n', ' ')
    
        return pregunta_formateada

    sql_formateado = formatear_pregunta(query)



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
            if subkey in ["DATE_SELL"]:
                subvalue = subvalue / 1000.0  # Convertir de milisegundos a segundos (utiliza 1000.0 para asegurarte de obtener un valor decimal)
                fecha_formateada = datetime.utcfromtimestamp(subvalue).strftime('%d/%m/%Y')
                informacion_texto += f" {subkey} : {fecha_formateada}, "
            else:
                informacion_texto += f" {subkey} : {subvalue}, "
        informacion_texto = informacion_texto.rstrip(', ') + "\n"

    # Imprimir o usar la cadena de texto según tus necesidades
    #print(informacion_texto)
    response_data = {
                    'sentencia SQL': sql_formateado,
                    'resultado SQL': informacion_texto,
                    }



    return response_data