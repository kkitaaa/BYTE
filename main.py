import flet as ft
from database import crear_tablas, obtener_productos

def main(page: ft.Page):
    page.title = "Byte 🍔"
    page.theme_mode = ft.ThemeMode.DARK

    # ---------------- PEDIDOS ----------------
    productos_db = obtener_productos()

    total = ft.Text("Total: $0", size=18, weight="bold")
    lista_pedido = ft.Column()
    total_valor = 0

    def agregar_producto(producto):
        def accion(e):
            nonlocal total_valor

            lista_pedido.controls.append(
                ft.Text(f"{producto['nombre']} - ${producto['precio']}")
            )

            total_valor += producto["precio"]
            total.value = f"Total: ${total_valor}"

            page.update()
        return accion

    # ----------- MENÚ TIPO CARTA -----------
    menu = ft.GridView(
        expand=True,
        runs_count=3,
        spacing=10,
        run_spacing=10
    )

    # ----------- MAPA DE IMÁGENES -----------
    imagenes = {
    "Burger 404": "img/Burger404.png",
    "Ctrl+Bite": "img/Ctrl+Bite.png",
    "Debug & Grill": "img/Debug&Grill.png",
    "Papas Sad": "img/Papas.png",
    "Coca Zero Drama": "img/CocaCola.png",
    "Sprite Chill": "img/Sprite.png",
    "Fanta Mood": "img/Fanta.png",
    }

    for p in productos_db:
        id_, nombre, precio = p
        ruta_imagen = imagenes.get(nombre, "img/default.png")
        card = ft.Container(
            content=ft.Column([
                
                # 📸 Placeholder imagen
                ft.Container(
                    content=ft.Image(src=ruta_imagen),

                    alignment=ft.Alignment.CENTER,
                ),

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
        lista_pedido,
        ft.Divider(),
        total,
        ft.Button("Generar Boleta")
    ])

    # ---------------- STOCK ----------------
    stock_view = ft.Column([
        ft.Text("Stock", size=20, weight="bold"),
        ft.Text("Aquí verás y manejarás productos 📦")
    ])

    # ---------------- STATS ----------------
    stats_view = ft.Column([
        ft.Text("Estadísticas", size=20, weight="bold"),
        ft.Text("Ventas, totales, etc 📊")
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