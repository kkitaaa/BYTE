import sqlite3

def conectar():
    return sqlite3.connect("restaurante.db")

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL,
        stock INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        total REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_venta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER,
        producto_id INTEGER,
        cantidad INTEGER,
        subtotal REAL,
        FOREIGN KEY (venta_id) REFERENCES ventas(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    )
    """)

    conn.commit()
    conn.close()

def insertar_productos_base():
    conn = conectar()
    cursor = conn.cursor()

    productos = [
        ("Burger 404", 5990, 10),
        ("Ctrl+Bite", 6490, 10),
        ("Debug & Grill", 6990, 10),
        ("Papas Sad", 2490, 20),
        ("Coca Zero Drama", 1990, 30),
        ("Sprite Chill", 1990, 30),
        ("Fanta Mood", 1990, 30),
    ]

    cursor.executemany("""
        INSERT INTO productos (nombre, precio, stock)
        VALUES (?, ?, ?)
    """, productos)

    conn.commit()
    conn.close()

def obtener_productos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre, precio FROM productos")
    productos = cursor.fetchall()

    conn.close()
    return productos

def restar_producto(producto_id, cantidad=1):
    conn = conectar()
    cursor = conn.cursor()

    # Verificar stock actual
    cursor.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,))
    resultado = cursor.fetchone()

    if resultado is None:
        conn.close()
        return False  # producto no existe

    stock_actual = resultado[0]

    if stock_actual < cantidad:
        conn.close()
        return False  # no hay suficiente stock

    # Restar stock
    cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (cantidad, producto_id))
    conn.commit()
    conn.close()
    return True

def devolver_stock(producto_id, cantidad=1):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, producto_id))
    conn.commit()
    conn.close()
    
# ****** PESTAÑA STOCK ******

def obtener_productos_completos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, precio, stock FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return productos

def actualizar_producto(producto_id, nombre=None, precio=None, stock=None):
    conn = conectar()
    cursor = conn.cursor()
    if nombre is not None:
        cursor.execute("UPDATE productos SET nombre = ? WHERE id = ?", (nombre, producto_id))
    if precio is not None:
        cursor.execute("UPDATE productos SET precio = ? WHERE id = ?", (precio, producto_id))
    if stock is not None:
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (stock, producto_id))
    conn.commit()
    conn.close()
