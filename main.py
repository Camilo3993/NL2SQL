from flask import Flask, request, jsonify, Response
import json
from entidades import extraccion_entidades

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug = True)
