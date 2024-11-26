import socket
import flet as ft
import threading
import json
import queue  # Para pasar datos entre hilos
import time
from datetime import datetime

# Cola para pasar mensajes desde los hilos al hilo principal
update_queue = queue.Queue()

# Contador de pedidos pendientes
pedido_count = 0

# Función para manejar la conexión de cada cliente
# Función para manejar la conexión de cada cliente
def handle_client(client_socket, page):
    try:
        # Recibir los datos del pedido (JSON)
        order_data = client_socket.recv(1024).decode('utf-8')
        print(f"Datos recibidos: {order_data}")  # Para depuración

        if order_data:
            try:
                # Convertir los datos del pedido de nuevo a un diccionario
                order = json.loads(order_data)  # Aseguramos que el pedido sea un JSON válido
                print("Pedido recibido:", order)

                # Usar la cola para pasar el pedido a la interfaz principal
                update_queue.put(order)

                # Guardar el archivo PDF con un nombre único basado en el contador de pedidos
                pdf_filename = f"recibido_factura_{pedido_count}.pdf"
                with open(pdf_filename, 'wb') as pdf_file:
                    while True:
                        pdf_chunk = client_socket.recv(1024)
                        if not pdf_chunk:
                            break
                        pdf_file.write(pdf_chunk)

                print(f"Archivo PDF recibido: {pdf_filename}")

                # Responder al cliente
                client_socket.send("Pedido y factura recibidos y procesados.".encode('utf-8'))
            except json.JSONDecodeError as e:
                print(f"Error al procesar el pedido (JSON inválido): {e}")
                client_socket.send("Error al procesar el pedido: formato JSON inválido.".encode('utf-8'))
            except Exception as e:
                print(f"Error al procesar el pedido: {e}")
                client_socket.send("Error al procesar el pedido.".encode('utf-8'))
        else:
            client_socket.send("Error: No se recibieron datos.".encode('utf-8'))

    except Exception as e:
        print(f"Error al recibir datos del cliente: {e}")
        client_socket.send("Error al recibir datos.".encode('utf-8'))

    client_socket.close()

# Función para mostrar el pedido en la interfaz del mesero
def display_order(order_data, page):
    global pedido_count  # Contador de pedidos

    # Incrementar el contador de pedidos
    pedido_count += 1

    # Extraer el 'order' del pedido completo
    order = order_data.get('order', {})  # Acceder al campo 'order'

    # Imprimir el pedido para verificar qué datos contiene
    print("Pedido recibido:", order_data)  # Verifica que el pedido contenga el 'client_name'

    # Obtener el nombre del cliente y la fecha (estos deberían ser parte del pedido)
    client_name = order_data.get('client_name', 'Desconocido')  # Se obtiene 'client_name' desde el pedido
    order_date = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    # Crear una cadena con los detalles del pedido
    order_str = "\n".join(
        [f"{item[1]['name']} ({item[1]['quantity']}x) - ${item[1]['subtotal']:,}" for item in order.items()]
    )
    order_str += f"\nTotal: ${sum(item[1]['subtotal'] for item in order.items()):,}"

    # Crear el contenedor transparente con los detalles del pedido
    order_details = ft.Container(
        content=ft.Column([ 
            ft.Row([  # Mostrar el número de pedido, el nombre del cliente y la fecha
                ft.Text(f"Pedido #{pedido_count}", size=18, weight="bold", color="white"),
                ft.Text(f"Cliente: {client_name}", size=16, color="white"),
                ft.Text(f"Fecha: {order_date}", size=16, color="white"),
            ], alignment="center"),
            ft.Text(order_str, size=16, weight="bold", color="white"),
        ], spacing=5),
        padding=ft.Padding(top=10, right=10, bottom=10, left=10),  # Corregido aquí
        bgcolor=ft.colors.TRANSPARENT,  # Fondo transparente
        border_radius=10,  # Bordes redondeados
        margin=ft.Margin(top=10, right=10, bottom=10, left=10)  # Corregido aquí
    )

    # Insertar el nuevo pedido al final de la lista
    orders_list.controls.append(order_details)

    # Actualizar la interfaz con el nuevo pedido
    page.update()

    # Actualizar el contenido de la notificación
    notification.content.controls.append(ft.Text(f"Nuevo pedido: {order_str}", size=16, color="white"))
    
    # Actualizar el texto del badge con el número de pedidos pendientes
    notification_button_badge.value = str(pedido_count)
    page.update()  # Actualizar la página para reflejar el cambio

# Iniciar servidor y escuchar en el puerto 8080
def start_server(page):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8080))  # Aseguramos que el servidor escuche en localhost:8080
    server_socket.listen(5)
    print("Esperando pedidos...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexión establecida con {addr}")
        # Manejar cada cliente en un hilo separado
        client_handler = threading.Thread(target=handle_client, args=(client_socket, page))
        client_handler.start()

# Función para escuchar la cola y actualizar la interfaz
def process_queue(page):
    while True:
        if not update_queue.empty():
            order = update_queue.get()
            display_order(order, page)
        time.sleep(0.1)  # Evitar que el hilo se ejecute sin descanso


# Función principal de la interfaz gráfica del mesero
def main(page: ft.Page):
    global orders_list, notification, notification_button, notification_button_badge  # Declarar las variables como global

    page.title = "M&M Food & Drink - Mesero"
    page.scroll = ft.ScrollMode.AUTO

    # Estilización de la página: fondo negro
    page.bgcolor = "#1a1a1a"  # Fondo negro

    # Crear el logo
    logo = ft.Image(src="logo.png", width=100, height=100)  # Ajusta la ruta y el tamaño

    # Contenedor de pedidos
    orders_list = ft.Column(
        spacing=10, 
        controls=[],
        scroll=ft.ScrollMode.AUTO
    )

    # Notificación de pedidos
    notification = ft.Container(
        content=ft.Column([], spacing=10),
        padding=ft.Padding(top=10, right=10, bottom=10, left=10),
        bgcolor=ft.colors.GREEN,
        border_radius=10,
        visible=False,  # Ocultar la notificación por defecto
        expand=True
    )

    # Crear un contenedor para el badge del botón de notificaciones
    notification_button_badge = ft.Text(
        value="0", size=12, color="white", weight="bold", bgcolor=ft.colors.RED,
    )

    # Crear el botón de notificaciones
    notification_button = ft.IconButton(
        icon=ft.icons.NOTIFICATIONS,
        icon_size=30,
        on_click=lambda e: toggle_notification_visibility()  # Alternar visibilidad
    )

    # Función para alternar la visibilidad
    def toggle_notification_visibility():
        notification.visible = not notification.visible
        page.update()  # Actualizar la página para reflejar el cambio

    # Contenedor principal con botones y controles
    main_container = ft.Container(
        content=ft.Column([  
            ft.Row([
                logo,  # Agregar el logo aquí
                ft.Text("Pedidos recibidos", size=24, weight="bold", color="white"),
                ft.Container(
                    content=notification_button_badge,
                    padding=ft.Padding(left=12, top=5, right=0, bottom=0),  # Corregido el padding
                    alignment=ft.alignment.top_right,
                    expand=True
                ),
                notification_button
            ], alignment="center"),
            notification,
            orders_list,
        ], expand=True, alignment="start"),
        padding=ft.Padding(top=20, right=20, bottom=20, left=20)  # Padding aplicado en Container
    )

    page.add(main_container)

    # Iniciar el servidor en un hilo para no bloquear la interfaz de usuario
    threading.Thread(target=start_server, args=(page,), daemon=True).start()

    # Iniciar un hilo para procesar la cola y actualizar la interfaz
    threading.Thread(target=process_queue, args=(page,), daemon=True).start()

    page.update()
ft.app(target=main)
