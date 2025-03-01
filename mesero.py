import requests

# URL del servidor (Render proporcionará un dominio)
SERVER_URL = "https://tu-servidor-render.onrender.com"

def hacer_pedido():
    cliente = input("Ingrese su nombre: ")
    productos = []

    while True:
        nombre = input("Nombre del producto (o 'fin' para terminar): ")
        if nombre.lower() == "fin":
            break
        cantidad = input("Cantidad: ")
        precio = input("Precio unitario: ")

        productos.append({
            "nombre": nombre,
            "cantidad": cantidad,
            "precio": precio
        })

    # Enviar datos al servidor
    response = requests.post(f"{SERVER_URL}/pedidos", json={"cliente": cliente, "productos": productos})

    if response.status_code == 200:
        print("✅ Pedido realizado con éxito:", response.json())
    else:
        print("❌ Error en el pedido:", response.json())

if __name__ == "__main__":
    hacer_pedido()
