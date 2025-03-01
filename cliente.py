import flet as ft
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import socket
import json
import os
import openpyxl
from openpyxl import Workbook
from datetime import datetime
import os
import requests
# Función para guardar los pedidos en un archivo Excel
def save_order_to_excel(order, client_name):
    # Verificar si el archivo de Excel ya existe
    excel_filename = "base_datos/pedidos.xlsx"
    file_exists = os.path.exists(excel_filename)

    # Crear un libro de trabajo
    if not file_exists:
        wb = Workbook()
        ws = wb.active
        ws.title = "Pedidos"
        
        # Agregar encabezados de las columnas
        ws.append([
            "Fecha", "Cliente", "Producto", "Categoría", "Cantidad", "Precio Unitario", "Subtotal"
        ])
    else:
        wb = openpyxl.load_workbook(excel_filename)
        ws = wb.active
    
    # Calcular el total del pedido
    total = sum(item["subtotal"] for item in order.values())
    
    # Recorrer el pedido y agregar las filas
    for item in order.values():
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ws.append([
            date, 
            client_name, 
            item["name"], 
            item["category"], 
            item["quantity"], 
            item["unit_price"], 
            item["subtotal"]
        ])
    
    # Agregar una fila para el total
    ws.append(["", "", "Total", "", "", "", total])
    
    # Guardar el archivo de Excel
    wb.save(excel_filename)


# Menú de opciones
MENU = {
    "Salchipapas": [
        ("Sencilla", 10000),
        ("Ranchera", 15000),
        ("Alemana", 15000),
        ("Mixta", 17000),
        ("Combinada", 12000),
        ("Salchipollo", 15000),
        ("Especial M&M Personal", 15000),
        ("Familiar M&M x2", 25000),
        ("Familiar M&M x3", 35000),
        ("Familiar M&M x4", 48000),
    ],
    "Perro Caliente": [
        ("Sencillo", 6000),
        ("Ranchero", 10000),
        ("Suizo", 12000),
        ("Gemelo", 9000),
        ("Combinado", 9000),
        ("Alemán", 13000),
    ],
    "Hamburguesas": [
        ("Pechuga", 14000),
        ("Carne", 15000),
        ("Hamburguesa de Pollo", 20000),
        ("Hamburguesa de Carne", 22000),
    ],
    "Bebidas": [
        ("Agua Pequeña", 800),
        ("Agua Grande", 1500),
        ("Agua de Manzana", 1500),
        ("Jugo Hit Personal", 3000),
        ("Gaseosa Postobón (2LT)", 7000),
        ("Coca-Cola Personal", 2500),
        ("Coca-Cola 1.5", 7000),
        ("Costeña Bacana", 3000),
        ("Costeñita", 2500),
    ],
}

# Función para generar el PDF del pedido
def generate_pdf(order, client_name):
    # Crear la carpeta "factura" si no existe
    if not os.path.exists("factura"):
        os.makedirs("factura")

    filename = f"factura/factura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    print(f"Generando PDF: {filename}") 
    pdf = SimpleDocTemplate(filename, pagesize=letter)

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal_style = styles["BodyText"]

    elements = []

    # Título
    title = Paragraph("M&M Food & Drink - Factura", title_style)
    elements.append(title)

    # Información del cliente
    client_info = Paragraph(
        f"<b>Cliente:</b> {client_name}<br/>"
        f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        normal_style,
    )
    elements.append(client_info)
    elements.append(Paragraph("<br/><br/>", normal_style))  # Espaciado

    # Tabla de productos
    data = [["Descripción", "Cantidad", "Precio Unitario", "Subtotal"]]
    total = 0

    for item in order.values():
        data.append([ 
            f"{item['name']} ({item['category']})", 
            str(item["quantity"]), 
            f"${item['unit_price']:,}", 
            f"${item['subtotal']:,}",
        ])
        total += item["subtotal"]

    # Agregar total
    data.append(["", "", "Total:", f"${total:,}"])

    # Crear tabla
    table = Table(data, colWidths=[200, 80, 100, 100])
    table.setStyle(TableStyle([ 
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f9f9f9")),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    # Generar PDF
    pdf.build(elements)
    return filename

# Función para enviar el pedido al servidor
# Función para enviar el pedido al servidor


# Reemplaza con la URL de tu servidor en Render
SERVER_URL = "https://restaurant-order-system-9tn7.onrender.com"

def send_order_to_server(order, client_name, pdf_filename):
    # Crear el pedido con el client_name incluido
    order_with_client = {"client_name": client_name, "order": order}

    # Leer el archivo PDF
    with open(pdf_filename, 'rb') as pdf_file:
        files = {'pdf': pdf_file}
        data = {'order': json.dumps(order_with_client)}

        try:
            # Enviar el pedido como una petición POST
            response = requests.post(f"{SERVER_URL}/pedidos", files=files, data=data)

            # Imprimir la respuesta del servidor
            print("Respuesta del servidor:", response.text)
        except Exception as e:
            print(f"Error al conectar con el servidor: {e}")




import flet as ft

# Función principal de la interfaz gráfica
def main(page: ft.Page):
    
    # Ruta del archivo de la imagen del logo
    logo_path = "images/logo.png"  # Asegúrate de tener la ruta correcta al logo

    # Crear el logo como un componente de imagen
    logo = ft.Image(src=logo_path, width=200, height=100)

    page.add(
        ft.Column([
            logo,  # Agregar el logo
            ft.Text("M&M Food & Drink", size=24, weight="bold", text_align="center"),  # Corregido 'alignment' por 'text_align'
        ])
    )
    page.title = "M&M Food & Drink - Cliente"
    page.scroll = ft.ScrollMode.AUTO

    order = {}
    client_name = ft.TextField(label="Nombre del cliente", width=300)
    resumen_pedido = ft.Column()

    qty_labels = {}  # Diccionario para almacenar referencias a las cantidades

    def update_summary():
        resumen_pedido.controls.clear()
        total = 0
        for item in order.values():
            resumen_pedido.controls.append(
                ft.Text(f"{item['name']} ({item['quantity']}x): ${item['subtotal']:,}")
            )
            total += item["subtotal"]
        resumen_pedido.controls.append(ft.Text(f"Total: ${total:,}", weight="bold"))
        page.update()

    def add_to_order(name, price, category, qty_label):
        if name not in order:
            order[name] = {"name": name, "quantity": 0, "unit_price": price, "subtotal": 0, "category": category}
        order[name]["quantity"] += 1
        order[name]["subtotal"] = order[name]["quantity"] * order[name]["unit_price"]
        qty_label.value = str(order[name]["quantity"])
        update_summary()

    def remove_from_order(name, qty_label):
        if name in order:
            order[name]["quantity"] -= 1
            if order[name]["quantity"] <= 0:
                del order[name]
            else:
                order[name]["subtotal"] = order[name]["quantity"] * order[name]["unit_price"]
            qty_label.value = str(order.get(name, {}).get("quantity", 0))
        update_summary()

    # Función para enviar el pedido al servidor
    # Función para borrar todo el pedido y formatear los datos
    def clear_order(e):
        # Limpiar el pedido y el nombre del cliente
        order.clear()
        client_name.value = ""

        # Limpiar el resumen del pedido
        resumen_pedido.controls.clear()

        # Reiniciar los contadores de cantidad de cada producto en el menú
        for name, qty_label in qty_labels.items():
            qty_label.value = "0"  # Restablecer la cantidad a 0
    
        page.update()

    def send_order(e):
        if not client_name.value.strip():
            page.overlay.append(ft.SnackBar(ft.Text("Por favor ingrese su nombre."), open=True))
            page.update()
            return

        if not order:
            page.overlay.append(ft.SnackBar(ft.Text("No hay productos en el pedido."), open=True))
            page.update()
            return

        # Guardar el pedido en el archivo de Excel
        save_order_to_excel(order, client_name.value.strip())

        # Generar el PDF
        filename = generate_pdf(order, client_name.value.strip())

        # Enviar el pedido al servidor (mesero) junto con el archivo PDF y el nombre del cliente
        send_order_to_server(order, client_name.value.strip(), filename)

        # Mostrar mensaje de éxito
        page.overlay.append(ft.SnackBar(ft.Text(f"Factura generada y enviada: {filename}"), open=True))

        # Limpiar los datos del formulario para permitir un nuevo pedido
        order.clear()  # Limpiar el pedido
        client_name.value = ""  # Limpiar el nombre del cliente
        resumen_pedido.controls.clear()  # Limpiar el resumen del pedido

        # Reiniciar los contadores de cantidad de cada producto en el menú
        for name, qty_label in qty_labels.items():
            qty_label.value = "0"  # Restablecer la cantidad a 0

        # Forzar la actualización de la página
        page.update()  # Actualizar la página para reflejar todos los cambios

    menu_items = []
    for category, items in MENU.items():
        menu_items.append(ft.Text(category, weight="bold", size=18))
        for name, price in items:
            qty_label = ft.Text("0")
            qty_labels[name] = qty_label  # Guardar la referencia al qty_label
            menu_items.append(
                ft.Row([ 
                    ft.Text(f"{name} - ${price:,}", expand=True),
                    ft.IconButton(icon=ft.icons.REMOVE, on_click=lambda e, n=name, ql=qty_label: remove_from_order(n, ql)),
                    qty_label,
                    ft.IconButton(icon=ft.icons.ADD, on_click=lambda e, n=name, p=price, c=category, ql=qty_label: add_to_order(n, p, c, ql)),
                ], alignment="center")
            )
    
    page.add(
        ft.Column([ 
            ft.Row([client_name]),
            ft.Column(menu_items, scroll=ft.ScrollMode.AUTO, expand=True),  # Menú con scroll dinámico
            ft.Text("Resumen del Pedido", size=20, weight="bold"),
            resumen_pedido,
            ft.ElevatedButton("Enviar Pedido", on_click=send_order),
            ft.ElevatedButton("Borrar Pedido", on_click=clear_order)
        ])
    )

ft.app(target=main)
