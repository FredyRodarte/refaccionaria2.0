from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv('connect.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Conexion a Mongo
mongo_uri = f"mongodb://{os.getenv('DB_HOST')}:{os.getenv('DB_PUERTO')}/" # direccion del servidor de mongo.
mongo_client = MongoClient(
    mongo_uri,
    serverSelectionTimeoutMS=int(os.getenv('DB_TIEMPO_FUERA'))
)
db = mongo_client[os.getenv('DB_NAME')] #Nombre de la base de datos.

# Verificar conexion a mongo
try:
    mongo_client.server_info()  # Forzar una llamada al servidor
    print("✅ Conexión a MongoDB establecida correctamente")
except Exception as e:
    print(f"❌ Error al conectar a MongoDB: {e}")

#Rutas de la app --- 
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)