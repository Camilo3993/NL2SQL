from flask import Flask, request, jsonify
import requests
from ibm_cloud_sdk_core import IAMTokenManager
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, BearerTokenAuthenticator
import os
from ibm_watson_machine_learning.foundation_models.utils.enums import ModelTypes
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from ibm_watson_machine_learning.foundation_models.utils.enums import DecodingMethods
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

app = Flask(__name__)

# Selección del modelo
model_id = os.getenv("MPT")

# Selección del ID del proyecto
project_id = os.getenv("IBM_WATSON_STUDIO_PROJECT_ID")

# Selección de la api key
api_key = os.getenv("IBM_CLOUD_API_KEY")

# Selección url
url_cloud = os.getenv("IBM_CLOUD_URL")

mi_apikey = os.getenv("mi_apikey")

url = os.getenv("url")

model_id_3 = ModelTypes.MPT_7B_INSTRUCT2

# Autenticación        
access_token = IAMTokenManager(
  apikey = api_key,
  url = url_cloud).get_token()

import getpass

credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "SJKz5Uoz1AlZhL6IKRSkPCRHVt5yvVICvH3GWNTfzoG7"
}

# Parámetros
parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 700,
    "repetition_penalty": 1
}

parametros = {
    GenParams.DECODING_METHOD: DecodingMethods.SAMPLE,
    GenParams.MAX_NEW_TOKENS: 100,
    GenParams.MIN_NEW_TOKENS: 1,
    GenParams.TEMPERATURE: 0.5,
    GenParams.TOP_K: 50,
    GenParams.TOP_P: 1
}

MPT_7B_INSTRUCT2 = Model(
    model_id=model_id_3, 
    params=parametros, 
    credentials=credentials,
    project_id=project_id)

MPT_7B_INSTRUCT2_llm = WatsonxLLM(model=MPT_7B_INSTRUCT2)

def categorizar(json_data):

    json_data = request.json
    

    if not json_data or 'nombre_columna' not in json_data:
        return jsonify({"error": "Invalid JSON format"}), 400    

    # Generación de sentencia SQL
    nombre_columna = json_data['nombre_columna']#"¿Cuál es el cliente que ha realizado el mayor número de transacciones?"

    datos = json_data['datos']


    clasificar_template = """
    Respira profundamente y enfoquémonos. Tu rol es el de un experto en administración de datos, encargado de identificar la categoría a la cual pertenecen los datos. Utiliza el nombre de la columna como un indicador inicial,Algunos de los nombres de las columna pueden ser abreviaciones de palabras del estilo VEN=VENDEDOR , CLI=CLIENTE,SEG=SEGUIMIENTO,FEC=FECHA. y los datos de esa columna para confirmar esa decisión ademas en que tu respuesta sea como se te indica y de seguir el ejemplo.
    El conjunto de datos podría corresponder a alguna de estas categorías: cliente, vendedor, indicador, ventas, fecha o identificador. Analiza el nombre de la columna como punto de partida para seleccionar una de las categorías.
    Cliente: Información asociada a los clientes, como nombres, apellidos, direcciones, detalles de contacto como correos o números de teléfono.
    Vendedor: Datos relacionados con personas o entidades que ofrecen productos o servicios, incluyendo nombres, detalles de contacto, entre otros.
    Indicador:Medir el rendimiento de un proceso o actividad.
    Ventas: Información sobre transacciones comerciales, tales como montos de compra, precio neto o bruto o cualquier tipo de precio de un producto o servicio, métodos o tipos de pago,canales, informacion econocimica como  deuda , descuento,promedio, origen venta, total, etc.
    Productos: informacion sobre los servicios , categorias o productos que se ofrecen en la tienda como el nombre del producto , el stock del producto , la descripcion del producto.
    Fecha: Datos exclusivos sobre fechas, como fechas de transacciones, de registro, de nacimiento, etc.
    Identificador: Código o clave única para identificar elementos de otras categorías. Los identificadores son únicos y se utilizan para identificar elementos de otras categorías, como clientes, productos, ventas, etc. Algunos ejemplos de identificadores son números de identificación fiscal, números de serie, claves de acceso, etc.
    Utiliza el ejemplo solo para guiar tu respuesta, ademas evitar devolver informacion que es diferente a alguna de las categorias anteriormente mencionadas.
    ejemplo 1:
        Texto para clasificar:
            -Nombre de la columna: Cliente RUT_Documento. 
            -Datos de la columna: 12347022-4
        Respuesta:
            Identificador
    ejemplo 2:
        Texto para clasificar:
            -Nombre de la columna: SALESID. 
            -Datos de la columna: DKMLO0120.
        Respuesta:
            Identificador    
    respira y enfocate en que la respuesta que necesitamos es solo la categoría a la que pertenecen los datos, sin detalles adicionales.
    Texto para clasificar: 
        Nombre de la columna: {nombre_columna}. 
        Datos de la columna: {datos}.
    Respuesta:
    """

    prompt_2 = PromptTemplate(
        input_variables=["nombre_columna","datos"],
        template=clasificar_template,
    )


    chain_2 = LLMChain(llm=MPT_7B_INSTRUCT2_llm, prompt=prompt_2)
    

    clasificar=chain_2.run({'nombre_columna': nombre_columna,'datos':datos})
    
    descripcion_template = """
    Respira profundamente y enfoquémonos. Tu rol es el de un experto en administración de datos, encargado de crear una breve descripcion de los datos.Evita devolver que no sabes , solo crea un descripcion del conjunto de datos entregado. 
    Utiliza el nombre de la columna ,la categoria y los datos de la columna para crear la descripcion del conjunto de datos.Algunos de los nombres de las columna pueden ser abreviaciones de palabras del estilo VEN=VENDEDOR , CLI=CLIENTE,SEG=SEGUIMIENTO,FEC=FECHA,PREV=PREVIAMENTE,FUGA=ABANDONO.
    Utiliza el ejemplo solo para guiar tu respuesta.
    ejemplo 1:
        Conjuntos de datos:
            Nombre de la columna: Cliente RUT_Documento.
            Categoria: Identificador.
            Datos de la columna: 12347022-4.
        Respuesta:
            El conjunto de datos indica el rut del cliente y sirve para identificar al cliente.
    respira y enfocate en que la respuesta que necesitamos es solo la descripcion del conjunto de datos, sin detalles adicionales.
    Conjunto de datos:
    Nombre de la columna: {nombre_columna}. 
    Categoria : {categoria}
    Datos de la columna: {datos}.
    Respuesta:
    """

    prompt_3 = PromptTemplate(
        input_variables=["nombre_columna","datos","categoria"],
        template=descripcion_template,
    )

    chain_3 = LLMChain(llm=MPT_7B_INSTRUCT2_llm, prompt=prompt_3)


    descripcion=chain_3.run({'nombre_columna': nombre_columna,'datos':datos,'categoria':clasificar})
    
    
    response_data = {'Categoria':clasificar,
                      'Descripcion':descripcion,
                     }



    return response_data