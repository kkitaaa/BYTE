import flet as ft
from database import crear_tablas, obtener_productos
from database import conectar, obtener_productos_completos
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
            
            stock_view.controls.clear()
            stock_view.controls.append(ft.Text("Stock", size=20, weight="bold"))
            stock_view.controls.append(stock_view_content())
            page.update()
            
        return accion

    
    def actualizar_stats_view():
        conn = conectar()
        cursor = conn.cursor()

        # Total de ventas
        cursor.execute("SELECT COUNT(*) FROM ventas")
        total_ventas = cursor.fetchone()[0]

        # Total recaudado
        cursor.execute("SELECT SUM(total) FROM ventas")
        total_recaudado = cursor.fetchone()[0] or 0

        # Top 3 productos más vendidos
        cursor.execute("""
            SELECT p.nombre, SUM(d.cantidad) AS cantidad_vendida
            FROM detalle_venta d
            JOIN productos p ON d.producto_id = p.id
            GROUP BY p.id, p.nombre
            ORDER BY cantidad_vendida DESC
            LIMIT 3
        """)
        top_productos = cursor.fetchall()
        conn.close()

        stats_view.controls.clear()

        # Encabezado
        stats_view.controls.append(
            ft.Row([
                ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.AMBER, size=30),
                ft.Text("Estadísticas", size=24, weight="bold", color=ft.Colors.AMBER)
            ])
        )

        # Tarjeta total ventas
        stats_view.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Total de ventas", size=16, weight="bold"),
                        ft.Text(str(total_ventas), size=22, color=ft.Colors.GREEN)
                    ]),
                    padding=15,
                    bgcolor=ft.Colors.GREY_900,
                    border_radius=10
                )
            )
        )

        # Tarjeta total recaudado
        stats_view.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Total recaudado", size=16, weight="bold"),
                        ft.Text(f"${total_recaudado}", size=22, color=ft.Colors.CYAN)
                    ]),
                    padding=15,
                    bgcolor=ft.Colors.GREY_900,
                    border_radius=10
                )
            )
        )

        # Tabla top 3 productos
        stats_view.controls.append(
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Producto", weight="bold")),
                    ft.DataColumn(ft.Text("Cantidad vendida", weight="bold")),
                ],
                rows=[
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(nombre)),
                        ft.DataCell(ft.Text(str(cantidad)))
                    ]) for nombre, cantidad in top_productos
                ]
            )
        )

        page.update()
    
    def agregar_producto(producto):
        def accion(e):
            nonlocal total_valor
            from database import restar_producto

            # Verificar y restar stock
            if not restar_producto(producto["id"], 1):
                page.snack_bar = ft.SnackBar(ft.Text("Producto sin stock"))
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
            
            stock_view.controls.clear()
            stock_view.controls.append(ft.Text("Stock", size=20, weight="bold"))
            stock_view.controls.append(stock_view_content())
            page.update()
            
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
            page.snack_bar = ft.SnackBar(ft.Text("No hay productos en el pedido"))
            page.snack_bar.open = True
            page.update()
            return

        detalle = "\n".join([f"{p['nombre']} - ${p['precio']}" for p in pedido_actual])

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
        os.startfile(filename)

        # Guardar venta y detalle en BD
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO ventas (fecha, total) VALUES (?, ?)", 
                    (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total_valor))
        venta_id = cursor.lastrowid

        for p in pedido_actual:
            cursor.execute("""
                INSERT INTO detalle_venta (venta_id, producto_id, cantidad, subtotal)
                VALUES (?, ?, ?, ?)
            """, (venta_id, p["id"], 1, p["precio"]))

        conn.commit()
        conn.close()

        # Mostrar diálogo
        dialog = ft.AlertDialog(
            title=ft.Text("🧾 Boleta"),
            content=ft.Text(f"{detalle}\n\nTOTAL: ${total_valor}"),
            actions=[ft.TextButton("OK", on_click=lambda e: cerrar_boleta(dialog))]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

        # 🔹 limpiar pedido después de guardar en BD
        limpiar_pedido()

        # 🔹 refrescar stats
        actualizar_stats_view()

        

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


    def stock_view_content():
        productos = obtener_productos_completos()

        rows = []
        for id_, nombre, precio, stock in productos:
            nombre_field = ft.TextField(value=nombre, width=150)
            precio_field = ft.TextField(value=str(precio), width=100)
            stock_field = ft.Text(value=str(stock), width=80)

            def guardar_cambios(e, pid=id_, nf=nombre_field, pf=precio_field):
                from database import actualizar_producto
                actualizar_producto(pid, nombre=nf.value, precio=float(pf.value))
                # 🔹 reconstruir tabla completa
                stock_view.controls.clear()
                stock_view.controls.append(ft.Text("Stock", size=20, weight="bold"))
                stock_view.controls.append(stock_view_content())
                page.update()

            def sumar_stock(e, pid=id_):
                from database import actualizar_producto
                actualizar_producto(pid, stock=1)
                # 🔹 reconstruir tabla completa
                stock_view.controls.clear()
                stock_view.controls.append(ft.Text("Stock", size=20, weight="bold"))
                stock_view.controls.append(stock_view_content())
                page.update()

            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(nombre_field),
                    ft.DataCell(precio_field),
                    ft.DataCell(stock_field),
                    ft.DataCell(ft.Row([
                        ft.IconButton(icon=ft.Icons.SAVE, on_click=guardar_cambios),
                        ft.IconButton(icon=ft.Icons.ADD, on_click=sumar_stock)
                    ]))
                ])
            )

        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Precio")),
                ft.DataColumn(ft.Text("Stock")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=rows
        )


    stock_view = ft.Column([
    ft.Text("Stock", size=20, weight="bold"),
    stock_view_content()
    ])

    # ---------------- STATS ----------------
    
    stats_view = ft.Column()
    
    actualizar_stats_view()
    
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