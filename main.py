import flet as ft
from database import crear_tablas, obtener_productos
from database import conectar
from reportlab.pdfgen import canvas
import os
import datetime

def main(page: ft.Page):
    page.title = "Byte 🍔"
    page.theme_mode = ft.ThemeMode.DARK

    # ---------------- PEDIDOS ----------------
    productos_db = obtener_productos()

    total = ft.Text("Total: $0", size=18, weight="bold")
    lista_pedido = ft.ListView(
        expand=False,
        auto_scroll=False,
        spacing=5,
        padding=10
    )

    total_valor = 0
    pedido_actual = []

    def actualizar_total():
        total.value = f"Total: ${total_valor}"
        page.update()

    def eliminar_producto(producto, row):
        def accion(e):
            nonlocal total_valor
            from database import devolver_stock

            if producto in pedido_actual:
                pedido_actual.remove(producto)
                total_valor -= producto["precio"]

                # devolver stock
                devolver_stock(producto["id"], 1)

            if row in lista_pedido.controls:
                lista_pedido.controls.remove(row)

            actualizar_total()
        return accion


    def agregar_producto(producto):
        def accion(e):
            nonlocal total_valor
            from database import restar_producto

            # Verificar y restar stock
            if not restar_producto(producto["id"], 1):
                page.snack_bar = ft.SnackBar(ft.Text("❌ Producto sin stock"))
                page.snack_bar.open = True
                page.update()
                return

            pedido_actual.append(producto)

            row = ft.Row([
                ft.Text(f"{producto['nombre']} - ${producto['precio']}"),
                ft.IconButton(icon=ft.Icons.DELETE)
            ])
            row.controls[1].on_click = eliminar_producto(producto, row)

            lista_pedido.controls.append(row)

            total_valor += producto["precio"]
            actualizar_total()
        return accion



    def limpiar_pedido():
        nonlocal total_valor, pedido_actual
        pedido_actual.clear()
        lista_pedido.controls.clear()
        total_valor = 0
        actualizar_total()
        page.update()


    def generar_boleta(e):
        
        
        if not pedido_actual:
            page.snack_bar = ft.SnackBar(ft.Text("No hay productos en el pedido 😐"))
            page.snack_bar.open = True
            page.update()
            return

        detalle = "\n".join(
            [f"{p['nombre']} - ${p['precio']}" for p in pedido_actual]
        )

        # Generar PDF
        filename = f"boleta_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename)
        c.drawString(100, 750, "🧾 Boleta")
        y = 700
        for p in pedido_actual:
            c.drawString(100, y, f"{p['nombre']} - ${p['precio']}")
            y -= 20
        c.drawString(100, y - 20, f"TOTAL: ${total_valor}")
        c.save()
        # Abrir el PDF
        os.startfile(filename)

        dialog = ft.AlertDialog(
            title=ft.Text("🧾 Boleta"),
            content=ft.Text(f"{detalle}\n\nTOTAL: ${total_valor}"),
            actions=[
                ft.TextButton("OK", on_click=lambda e: cerrar_boleta(dialog))
            ]
        )

        page.dialog = dialog
        dialog.open = True
        page.update()
        
        limpiar_pedido()
        
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO ventas (fecha, total) VALUES (?, ?)", 
                    (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total_valor))
        venta_id = cursor.lastrowid

        for p in pedido_actual:
            cursor.execute("INSERT INTO detalle_venta (venta_id, producto_id, cantidad, subtotal) VALUES (?, ?, ?, ?)",
                        (venta_id, p["id"], 1, p["precio"]))

        conn.commit()
        conn.close()
        

    def cerrar_boleta(dialog):
        nonlocal total_valor, pedido_actual
        dialog.open = False

        # limpiar pedido
        pedido_actual.clear()
        lista_pedido.controls.clear()
        total_valor = 0
        actualizar_total()

    # ----------- MENÚ -----------

    menu = ft.GridView(
        expand=True,
        runs_count=3,
        spacing=10,
        run_spacing=10
    )

    imagenes = {
        "Burger 404": "img/Burger404.png",
        "Ctrl+Bite": "img/Ctrl+Bite.png",
        "Debug & Grill": "img/Debug&Grill.png",
        "Papas Fritas": "img/Papas.png",
        "Coca Zero": "img/CocaCola.png",
        "Sprite": "img/Sprite.png",
        "Fanta": "img/Fanta.png",
    }

    for p in productos_db:
        id_, nombre, precio = p
        ruta_imagen = imagenes.get(nombre, "img/default.png")

        card = ft.Container(
            content=ft.Column([
                ft.Image(src=ruta_imagen, height=100),
                ft.Text(nombre, weight="bold"),
                ft.Text(f"${precio}", color=ft.Colors.GREEN),
                ft.Button(
                    "Agregar",
                    on_click=agregar_producto({
                        "id": id_,
                        "nombre": nombre,
                        "precio": precio
                    })
                )
            ],
            horizontal_alignment="center"
            ),
            padding=10,
            bgcolor=ft.Colors.GREY_900,
            border_radius=15,
            width=180
        )

        menu.controls.append(card)

    pedidos_view = ft.Column([
        ft.Text("Carta 🍔", size=22, weight="bold"),
        menu,
        ft.Divider(),
        ft.Text("Pedido:", weight="bold"),
        ft.Container(
            content=lista_pedido,
            height=100, 
            bgcolor=ft.Colors.GREY_900,
            border_radius=10,
            padding=10,
            expand=False,

        ),
        ft.Divider(),
        total,
        ft.ElevatedButton("Generar Boleta", on_click=generar_boleta)
    ])


    # ---------------- STOCK ----------------
    stock_view = ft.Column([
        ft.Text("Stock", size=20, weight="bold"),
        ft.Text("Aquí verás y manejarás productos 📦 (próximamente..)")
    ])

    # ---------------- STATS ----------------
    stats_view = ft.Column([
        ft.Text("Estadísticas", size=20, weight="bold"),
        ft.Text("Ventas, totales, etc 📊 (próximamente..)")
    ])

    # ---------------- CONTENEDOR ----------------
    content = ft.Container(content=pedidos_view, expand=True)

    def cambiar_tab(e):
        index = e.control.selected_index

        if index == 0:
            content.content = pedidos_view
        elif index == 1:
            content.content = stock_view
        elif index == 2:
            content.content = stats_view

        page.update()

    navbar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.RECEIPT, label="Pedidos"),
            ft.NavigationBarDestination(icon=ft.Icons.INVENTORY, label="Stock"),
            ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART, label="Stats"),
        ],
        on_change=cambiar_tab
    )

    page.add(content, navbar)


# ----------- INICIO APP -----------
crear_tablas()
ft.app(target=main)