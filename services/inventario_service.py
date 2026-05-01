from database.db import get_pool
from services.economia_service import (
    obtener_o_crear_jugador, a_cobre, desde_cobre, formato_monedas
)


async def obtener_inventario(jugador_id: str) -> list:
    await obtener_o_crear_jugador(jugador_id)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT item, cantidad FROM inventario WHERE jugador_id = $1 ORDER BY item",
            jugador_id
        )
    return [dict(r) for r in rows]


async def agregar_item(jugador_id: str, item: str, cantidad: int = 1) -> str:
    """Agrega ítem. El nombre se normaliza a title case para evitar duplicados."""
    await obtener_o_crear_jugador(jugador_id)
    item_normalizado = item.strip().title()
    pool = await get_pool()
    async with pool.acquire() as conn:
        existente = await conn.fetchrow(
            "SELECT id, cantidad FROM inventario WHERE jugador_id=$1 AND LOWER(item)=LOWER($2)",
            jugador_id, item_normalizado
        )
        if existente:
            await conn.execute(
                "UPDATE inventario SET cantidad=cantidad+$1 WHERE id=$2",
                cantidad, existente["id"]
            )
        else:
            await conn.execute(
                "INSERT INTO inventario (jugador_id, item, cantidad) VALUES ($1, $2, $3)",
                jugador_id, item_normalizado, cantidad
            )
    return item_normalizado


async def quitar_item(jugador_id: str, item: str, cantidad: int = 1) -> tuple[bool, str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        existente = await conn.fetchrow(
            "SELECT id, cantidad, item FROM inventario WHERE jugador_id=$1 AND LOWER(item)=LOWER($2)",
            jugador_id, item.strip()
        )
        if not existente:
            return False, f"No tienes **{item}** en tu inventario."
        if existente["cantidad"] < cantidad:
            return False, f"Solo tienes **{existente['cantidad']}x {existente['item']}**."
        if existente["cantidad"] == cantidad:
            await conn.execute("DELETE FROM inventario WHERE id=$1", existente["id"])
        else:
            await conn.execute(
                "UPDATE inventario SET cantidad=cantidad-$1 WHERE id=$2",
                cantidad, existente["id"]
            )
    return True, f"Se quitaron {cantidad}x {existente['item']}"


async def transferir_item(emisor_id: str, receptor_id: str, item: str, cantidad: int = 1) -> tuple[bool, str]:
    exito, msg = await quitar_item(emisor_id, item, cantidad)
    if not exito:
        return False, msg
    nombre_final = await agregar_item(receptor_id, item, cantidad)
    return True, f"Transferido {cantidad}x {nombre_final}"


# ─── tienda ─────────────────────────────────────────────────────────────────

async def obtener_tienda() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tienda WHERE activo=TRUE ORDER BY nombre"
        )
    return [dict(r) for r in rows]


async def agregar_producto_tienda(
    nombre: str, descripcion: str,
    precio_cobre: int = 0, precio_plata: int = 0, precio_oro: int = 0,
    stock: int = -1
) -> tuple[bool, str]:
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO tienda (nombre, descripcion, precio_cobre, precio_plata, precio_oro, stock)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT (nombre) DO UPDATE
                   SET descripcion=$2, precio_cobre=$3, precio_plata=$4, precio_oro=$5,
                       stock=$6, activo=TRUE""",
                nombre.strip().title(), descripcion, precio_cobre, precio_plata, precio_oro, stock
            )
        return True, "Producto agregado/actualizado"
    except Exception as e:
        return False, str(e)


async def quitar_producto_tienda(nombre: str) -> tuple[bool, str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE tienda SET activo=FALSE WHERE LOWER(nombre)=LOWER($1)",
            nombre.strip()
        )
    if result == "UPDATE 0":
        return False, f"No existe '{nombre}' en la tienda."
    return True, f"'{nombre}' eliminado de la tienda."


async def comprar_item_tienda(jugador_id: str, nombre: str, cantidad: int = 1) -> tuple[bool, str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        producto = await conn.fetchrow(
            "SELECT * FROM tienda WHERE LOWER(nombre)=LOWER($1) AND activo=TRUE",
            nombre.strip()
        )
        if not producto:
            return False, f"No se encontró **{nombre}** en la tienda."

        if producto["stock"] != -1 and producto["stock"] < cantidad:
            return False, f"Solo quedan **{producto['stock']}** unidades disponibles."

        precio_total = a_cobre(
            producto["precio_cobre"] * cantidad,
            producto["precio_plata"] * cantidad,
            producto["precio_oro"]   * cantidad
        )

        jugador = await obtener_o_crear_jugador(jugador_id)
        saldo = a_cobre(jugador["cobre"], jugador["plata"], jugador["oro"])
        if saldo < precio_total:
            actual = desde_cobre(saldo)
            return False, f"No tienes suficiente. Tienes {formato_monedas(**actual)}."

        nuevo_saldo = desde_cobre(saldo - precio_total)

        async with conn.transaction():
            await conn.execute(
                "UPDATE jugadores SET cobre=$1, plata=$2, oro=$3 WHERE id=$4",
                nuevo_saldo["cobre"], nuevo_saldo["plata"], nuevo_saldo["oro"], jugador_id
            )
            if producto["stock"] != -1:
                await conn.execute(
                    "UPDATE tienda SET stock=stock-$1 WHERE id=$2",
                    cantidad, producto["id"]
                )
            await conn.execute(
                """INSERT INTO transacciones (emisor_id, tipo, cobre, plata, oro, detalle)
                   VALUES ($1, 'compra', $2, $3, $4, $5)""",
                jugador_id,
                producto["precio_cobre"] * cantidad,
                producto["precio_plata"] * cantidad,
                producto["precio_oro"]   * cantidad,
                f"Compró {cantidad}x {producto['nombre']}"
            )

    await agregar_item(jugador_id, producto["nombre"], cantidad)
    return True, producto["nombre"]
