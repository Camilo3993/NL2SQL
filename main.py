from flask import Flask, request, jsonify, Response
import json
from rutas.entidades import extraccion_entidades
from rutas.clasificacion import clasificacion_pregunta
from rutas.sql import sentencia_sql
from rutas.respuesta_final import respuesta_humanizada


app = Flask(__name__)  


@app.route('/entidades', methods=['POST'])
def ex_entidades():
    try:       

      json_data = request.json

      response_data = extraccion_entidades(json_data)      
      return  response_data
    
    except Exception as e:
        app.logger.error(f"Un error ha ocurrido: {str(e)}")
        return f"Un error ha ocurrido: {str(e)}", 500


@app.route('/clasificacion', methods=['POST'])
def final_clasificacion():
    try:       

      json_data = request.json

      response_data = clasificacion_pregunta(json_data)      
      return  response_data
    
    except Exception as e:
        app.logger.error(f"Un error ha ocurrido: {str(e)}")
        return f"Un error ha ocurrido: {str(e)}", 500

@app.route('/sql', methods=['POST'])
def sql_sentencia():
    try:       

      json_data = request.json

      response_data = sentencia_sql(json_data)      
      return  response_data
    
    except Exception as e:
        app.logger.error(f"Un error ha ocurrido: {str(e)}")
        return f"Un error ha ocurrido: {str(e)}", 500


@app.route('/respuesta', methods=['POST'])
def respuesta_final():
    try:       

      json_data = request.json

      response_data = respuesta_humanizada(json_data)      
      return  response_data
    
    except Exception as e:
        app.logger.error(f"Un error ha ocurrido: {str(e)}")
        return f"Un error ha ocurrido: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug = True)
