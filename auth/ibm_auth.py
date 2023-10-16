from dotenv import load_dotenv
import os

load_dotenv()

ibm_api_key = os.getenv("IBM_CLOUD_API_KEY")
ibm_cloud_url = os.getenv("IBM_CLOUD_URL")

# Autenticación        
access_token = IAMTokenManager(
    apikey = ibm_api_key,
    url = ibm_cloud_url).get_token()