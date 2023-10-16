from dotenv import load_dotenv
import os
import requests

load_dotenv()

watson_machine_learning_url = os.getenv("WML_URL")

class Prompt:
    def __init__(self, access_token, project_id):
        self.access_token = access_token
        self.project_id = project_id

    def generate(self, input, model_id, parameters):
        wml_url = watson_machine_learning_url
        Headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "model_id": model_id,
            "input": input,
            "parameters": parameters,
            "project_id": self.project_id
        }
        response = requests.post(wml_url, json=data, headers=Headers)
        if response.status_code == 200:
            return response.json()["results"][0]["generated_text"]
        else:
            return response.text