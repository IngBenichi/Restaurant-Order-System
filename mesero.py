from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Clave para manejar sesiones
socketio = SocketIO(app, cors_allowed_origins="*")  # WebSockets
CORS(app)

pedidos = []  # Lista para almacenar pedidos

# Crear carpeta para facturas si no existe
if not os.path.exists("facturas"):
    os.makedirs("facturas")

# Datos de usuario (puedes cambiar esto a una base de datos)
USERS = {"admin": "1234"}

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("panel"))
        return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/panel")
def panel():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("panel.html", pedidos=pedidos)

# 🚀 NUEVO: Endpoint para recibir pedidos desde cliente.py
@app.route("/pedidos", methods=["POST"])
def recibir_pedido():
    try:
        # Extraer JSON del formulario enviado
        order_json = json.loads(request.form['order'])  
        pdf_file = request.files['pdf']  # Extraer el archivo PDF

        # Guardar PDF con el nombre del cliente
        pdf_filename = f"facturas/{order_json['client_name']}_factura.pdf"
        pdf_file.save(pdf_filename)

        # Guardar el pedido en la lista
        pedidos.append(order_json)

        print(f"Pedido recibido de {order_json['client_name']}: {order_json['order']}")  # Debugging

        # Notificar a clientes conectados vía WebSockets
        socketio.emit("actualizar_pedidos", pedidos)

        return jsonify({"mensaje": "Pedido recibido correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@socketio.on("nuevo_pedido")
def recibir_pedido_ws(data):
    """Recibe un pedido desde WebSockets y lo guarda en la lista de pedidos."""
    if "client_name" not in data or "order" not in data:
        return jsonify({"error": "Faltan datos"}), 400

    pedidos.append(data)
    print(f"Nuevo pedido recibido vía WebSockets: {data}")  # Debugging
    socketio.emit("actualizar_pedidos", pedidos)  # Notificar a todos los clientes
    return jsonify({"mensaje": "Pedido recibido", "pedido": data}), 200

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=8080)
