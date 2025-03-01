from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

pedidos = []

if not os.path.exists("facturas"):
    os.makedirs("facturas")

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


@app.route("/pedidos", methods=["POST"])
def recibir_pedido():
    """Recibe un pedido desde el cliente y lo guarda en la lista de pedidos."""

    pdf_file = request.files.get("pdf")

    if "order" not in request.form:
        return jsonify({"error": "Faltan datos"}), 400


    try:
        data = json.loads(request.form["order"])

        if isinstance(data["order"], str):
            data["order"] = json.loads(data["order"])

        print("Pedido procesado:", json.dumps(data, indent=2, ensure_ascii=False))

    except json.JSONDecodeError:
        return jsonify({"error": "Formato JSON inválido"}), 400

    if "client_name" not in data or not isinstance(data["order"], list):
        return jsonify({"error": "Faltan datos o el formato es incorrecto"}), 400

    total = sum(item["quantity"] * item["unit_price"] for item in data["order"])

    pdf_filename = f"{data['client_name'].replace(' ', '_')}_factura.pdf"
    pdf_path = os.path.join("facturas", pdf_filename)

    if pdf_file:
        pdf_file.save(pdf_path)

    pdf_url = f"/facturas/{pdf_filename}"

    pedido = {
        "client_name": data["client_name"],
        "order": data["order"],
        "total": total,
        "pdf_url": pdf_url,
    }

    pedidos.append(pedido)

    socketio.emit("actualizar_pedidos", {"pedidos": pedidos})

    return jsonify({"mensaje": "Pedido recibido", "pedido": pedido}), 200


@socketio.on("nuevo_pedido")
def recibir_pedido_ws(data):
    if "client_name" not in data or "order" not in data:
        return jsonify({"error": "Faltan datos"}), 400

    pedidos.append(data)
    print(f"Nuevo pedido recibido vía WebSockets: {data}")
    socketio.emit("actualizar_pedidos", pedidos)
    return jsonify({"mensaje": "Pedido recibido", "pedido": data}), 200


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=8080)
