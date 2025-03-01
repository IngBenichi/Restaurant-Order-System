from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilita CORS para que el cliente pueda hacer solicitudes

pedidos = []  # Lista temporal para almacenar pedidos

@app.route("/")
def home():
    return "Servidor de mesero funcionando correctamente."

@app.route("/pedidos", methods=["POST"])
def recibir_pedido():
    data = request.get_json()
    
    if not data or "cliente" not in data or "productos" not in data:
        return jsonify({"error": "Faltan datos"}), 400
    
    pedidos.append(data)  # Guarda el pedido
    return jsonify({"mensaje": "Pedido recibido", "pedido": data}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
