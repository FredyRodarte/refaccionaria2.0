from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient, ReturnDocument
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId

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

#Funcion para autoincremento de ID_usuario
def getNextUserId(nombreCount):
    # Obtiene el siguiente ID autoincemental para usuarios
    counters = db.counters
    seq_doc = counters.find_one_and_update(
        {'_id': nombreCount},
        {'$inc': {'sequence_value':1}},
        return_document=ReturnDocument.AFTER,
        upsert=True #Si el documento no existe se crea.
    )
    return seq_doc['sequence_value']

# Rutas de la app
#===================================Fredy Rodarte==========================================================
@app.route('/')
def index():
    return render_template('index.html')

# AQUI COMIENZA EL CRUD DE USUARIOS
#Mostrar usuarios en la tabla
@app.route('/usuarios')
def usuarios():
    try:
        usuarios = list(db.usuarios.find({}))
        #print(usuarios)
        return render_template('usuarios/usuarios.html', usuarios=usuarios)
    except Exception as e:
        print("No se pudo realizar la consulta, Error: "+e)
        return render_template('usuarios/usuarios.html')

#Mostrar el formulario de Registrar usuarios:
@app.route('/registrar_usuario')
def mostrar_formulario():
    return render_template('usuarios/agregar_usuario.html')

@app.route('/registrar_usuario', methods=['POST'])
def registrar_usuario():
    try:
        # Obtener datos del formulario
        nombre = request.form.get('nombreA')
        correo = request.form.get('correoA')
        usuario = request.form.get('usuarioA')
        contrasena = request.form.get('contrasenaA')
        rol = request.form.get('rol_userA')
        
        # Validar que todos los campos estén presentes
        if not all([nombre, correo, usuario, contrasena, rol]):
            return "Todos los campos son requeridos", 400
        
        # Verificar si el usuario o correo ya existen
        if db.usuarios.find_one({'$or': [{'email': correo}, {'nickname': usuario}]}):
            return "El correo o usuario ya están registrados", 400
        
        # Crear el nuevo usuario (con contraseña hasheada)
        nuevo_usuario = {
            '_id': getNextUserId('user_id'),
            'nombre': nombre,
            'email': correo,
            'nickname': usuario,
            'contrasena': contrasena,  # Hasheamos la contraseña
            'rol': rol
        }
        
        # Insertar en la base de datos
        db.usuarios.insert_one(nuevo_usuario)
        
        # Redirigir a la lista de usuarios después de registrar
        return redirect(url_for('usuarios'))
    
    except Exception as e:
        print("Error al registrar usuario:", e)
        return "Ocurrió un error al registrar el usuario", 500
    

#Mostrar el formulario para editar usuario
@app.route('/editar_usuario/<user_id>')
def mostrar_editar_usuario(user_id):
    print("user: ", user_id)
    try:
        usuario = db.usuarios.find_one({'_id': int(user_id)})
        print("usuario: ", usuario)
        return render_template('usuarios/editar_usuario.html', usuario=usuario)
    except Exception as e:
        print("Error:", e)
        return "Ocurrio un error", 500
        

@app.route('/editar_usuario/<user_id>', methods=['POST'])
def editar_usuario(user_id):
    print("Si entro al metodo para guardar los cambios")
    try:
        #Obtener los datos del formulario
        nombre = request.form.get('nombreE')
        correo = request.form.get('correoE')
        usuario_nick = request.form.get('usuarioE')
        contrasena = request.form.get('contrasenaE')
        rol = request.form.get('rol_userE')

        # Validar campos
        if not all([nombre, correo, usuario_nick, rol]):
            return "Todos los campos son requeridos", 400
        
        # Actualizar el usuario
        db.usuarios.update_one(
            {'_id': int(user_id)},
            {'$set': {
                'nombre': nombre,
                'email': correo,
                'nickname': usuario_nick,
                'contrasena': contrasena,
                'rol': rol
            }}
        )
        
        return redirect(url_for('usuarios'))
    
    except Exception as e:
        print("Error al editar usuario: ", e)
        return "Ocurrió un error al editar el usuario", 500

# Eliminar Usuarios
@app.route('/eliminar_usuario/<user_id>', methods=['GET'])
def eliminar_usuario(user_id):
    db.usuarios.delete_one({'_id': int(user_id)})
    return redirect(url_for('usuarios'))


#===================================Eduardo Picazo ==========================================================
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


# ================================================== Adán Gurrola Grijalva ==================================================
# =================== AQUI COMIENZA LA SECCION DE CATEGORIAS ======================== 
# ===== Sección de Categorías =====

@app.route('/registrar_categorias', methods=['POST'])
def registrar_categorias():
    datos = request.form
    categoria = {
        "nombre": datos['nombre'],
        "descripcion": datos['descripcion']
    }
    db.categorias.insert_one(categoria)
    return redirect(url_for('categorias'))

# ===== Registrar Categorias =====

@app.route('/registrar_categorias', methods=['GET'])
def mostrar_formulario_categorias():
    return render_template('categorias/registrar_categorias.html')

@app.route('/categorias')
def categorias():
    lista_categorias = list(db.categorias.find())
    return render_template('categorias/categorias.html', categorias=lista_categorias)

# ===== Modificar Categorias =====

@app.route('/modificar_categoria/<id>', methods=['GET', 'POST'])
def modificar_categoria(id):
    if request.method == 'POST':
        datos = request.form
        db.categorias.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                "nombre": datos['nombre'],
                "descripcion": datos['descripcion']
            }}
        )
        return redirect(url_for('categorias'))
    
    categoria = db.categorias.find_one({'_id': ObjectId(id)})
    return render_template('categorias/modificar_categoria.html', categoria=categoria)

# ===== Eliminar Categorias =====

@app.route('/eliminar_categoria/<id>', methods=['POST'])
def eliminar_categoria(id):
    db.categorias.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('categorias'))






if __name__ == '__main__':
    app.run(debug=True)