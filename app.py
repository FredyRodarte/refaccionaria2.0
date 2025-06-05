from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv('connect.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Conexion a Mongo
mongo_uri = f"mongodb://{os.getenv('DB_HOST')}:{os.getenv('DB_PUERTO')}/" # direccion del servidor de 
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


#=================================== Eduardo Picazo ==========================================================
# AQUI COMIEZA EL CRUD DE PRODUCTOS


"""Desde esta sección se encuentran las rutas para el manejo de los productos
aun esta en desarrollo el registro, modificación y eliminación de productos 23/05/2024
"""
# Modulo para el registro de productos
@app.route('/registrar_producto', methods=['POST'])
def registrar_producto():
    datos = request.form
    producto = {
        "nombre": datos['nombre'],
        "descripcion": datos['descripcion'],
        "cantidad": int(datos['cantidad']),
        "categoria_id": ObjectId(datos['categoria_id']),
        "proveedor_id": ObjectId(datos['proveedor_id']),
        "ubicacion": datos['ubicacion']
    }
    db.productos.insert_one(producto)
    return redirect(url_for('index'))


# Modulo para redirigir al formulario de registro de productos
@app.route('/registrar_producto', methods=['GET'])
def mostrar_formulario_producto():
    categorias = list(db.categorias.find())
    proveedores = list(db.proveedores.find())
    return render_template('productos/registrar_producto.html', categorias=categorias, proveedores=proveedores)



# Modulo para mostrar los productos registrados, se utiliza una agregación para unir las colecciones 
# de productos, categorías y proveedores.
@app.route('/productos')
def productos():
    productos = db.productos.aggregate([
        {
            '$lookup': {
                'from': 'categorias',
                'localField': 'categoria_id',
                'foreignField': '_id',
                'as': 'categoria'
            }
        },
        {
            '$lookup': {
                'from': 'proveedores',
                'localField': 'proveedor_id',
                'foreignField': '_id',
                'as': 'proveedor'
            }
        },
        { '$unwind': '$categoria' },
        { '$unwind': '$proveedor' }
    ])
    
    lista_productos = list(productos)
    return render_template('productos/productos.html', productos=lista_productos)


from bson.objectid import ObjectId


#Modulo para modifcar un producto por ID
@app.route('/modificar_producto/<id>', methods=['GET', 'POST'])
def modificar_producto(id):
    if request.method == 'POST':
        datos = request.form
        db.productos.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                "nombre": datos['nombre'],
                "descripcion": datos['descripcion'],
                "cantidad": int(datos['cantidad']),
                "categoria_id": ObjectId(datos['categoria_id']),
                "proveedor_id": ObjectId(datos['proveedor_id']),
                "ubicacion": datos['ubicacion']
            }}
        )
        return redirect(url_for('productos'))

    producto = db.productos.find_one({'_id': ObjectId(id)})
    categorias = list(db.categorias.find())
    proveedores = list(db.proveedores.find())

    return render_template('productos/modificar_producto.html',
                           producto=producto,
                           categorias=categorias,
                           proveedores=proveedores)



#modulo para redirigir al formulario de modificación de productos
@app.route('/modificar_producto/<id>', methods=['GET'])
def mostrar_formulario_modificar(id):
    producto = db.productos.find_one({'_id': ObjectId(id)})
    print(producto)
    categorias = list(db.categorias.find())
    proveedores = list(db.proveedores.find())

    return render_template('productos/modificar_producto.html',
                           producto=producto,
                           categorias=categorias,
                           proveedores=proveedores)


# Modulo para eliminar un producto por ID
@app.route('/eliminar_producto/<id>', methods=['POST'])
def eliminar_producto(id):
    db.productos.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('productos'))




"""
Desde esta sección se encuentran las rutas para el manejo de los proveedores
ya esta funcionando el registro, modificación y eliminación de proveedores 23/05/2024"""
@app.route('/registrar_proveedor', methods=['POST'])
def registrar_proveedor():
    datos = request.form
    proveedor = {
        "nombre": datos['nombre'],
        "contacto": datos['contacto'],
        "telefono": datos['telefono'],
        "correo": datos['correo'],
        "direccion": {
            "calle": datos['calle'],
            "ciudad": datos['ciudad'],
            "codigo_postal": datos['codigo_postal']
        }
    }
    db.proveedores.insert_one(proveedor)
    return redirect(url_for('proveedores'))

@app.route('/registrar_proveedor', methods=['GET'])
def mostrar_formulario_proveedor():
    return render_template('proveedores/registro_proveedor.html')


# Mostrar los proveedores registrados
@app.route('/proveedores')
def proveedores():
    lista_proveedores = db.proveedores.find()
    return render_template('proveedores/proveedores.html', proveedores=lista_proveedores)



# Modificar proveedor por ID
@app.route('/modificar_proveedor/<id>', methods=['GET', 'POST'])
def modificar_proveedor(id):
    if request.method == 'POST':
        datos = request.form
        db.proveedores.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                "nombre": datos['nombre'],
                "contacto": datos['contacto'],
                "telefono": datos['telefono'],
                "correo": datos['correo'],
                "direccion": {
                    "calle": datos['calle'],
                    "ciudad": datos['ciudad'],
                    "codigo_postal": datos['codigo_postal']
                }
            }}
        )
        
        return redirect(url_for('proveedores'))

    proveedor = db.proveedores.find_one({'_id': ObjectId(id)})
    return render_template('proveedores/modificar_proveedor.html', proveedor=proveedor)



# Eliminar proveedor por ID
@app.route('/eliminar_proveedor/<id>', methods=['POST'])
def eliminar_proveedor(id):
    db.proveedores.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('proveedores'))








if __name__ == '__main__':
    app.run(debug=True)