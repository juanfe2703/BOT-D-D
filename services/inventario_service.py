from database.db import get_pool
from services.economia_service import obtener_o_crear_jugador


async def obtener_inventario(jugador_id: str) -> list:
    """Devuelve la lista de ítems del jugador."""
    await obtener_o_crear_jugador(jugador_id)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT item, cantidad FROM inventario WHERE jugador_id = $1 ORDER BY item",
            jugador_id
        )
    return rows


async def agregar_item(jugador_id: str, item: str, cantidad: int = 1) -> str:
    """Agrega un ítem al inventario. Si ya existe, suma la cantidad."""
    await obtener_o_crear_jugador(jugador_id)
    pool = await get_pool()
    async with pool.acquire() as conn:
        existente = await conn.fetchrow(
            "SELECT id, cantidad FROM inventario WHERE jugador_id = $1 AND LOWER(item) = LOWER($2)",
            jugador_id, item
        )
        if existente:
            await conn.execute(
                "UPDATE inventario SET cantidad = cantidad + $1 WHERE id = $2",
                cantidad, existente["id"]
            )
        else:
            await conn.execute(
                "INSERT INTO inventario (jugador_id, item, cantidad) VALUES ($1, $2, $3)",
                jugador_id, item, cantidad
            )
    return item


async def quitar_item(jugador_id: str, item: str, cantidad: int = 1) -> tuple[bool, str]:
    """Quita cantidad de un ítem. Retorna (éxito, mensaje)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        existente = await conn.fetchrow(
            "SELECT id, cantidad FROM inventario WHERE jugador_id = $1 AND LOWER(item) = LOWER($2)",
            jugador_id, item
        )
        if not existente:
            return False, f"No tienes **{item}** en tu inventario."
        if existente["cantidad"] < cantidad:
            return False, f"Solo tienes **{existente['cantidad']}x {item}**, no puede quitar {cantidad}."
        if existente["cantidad"] == cantidad:
            await conn.execute("DELETE FROM inventario WHERE id = $1", existente["id"])
        else:
            await conn.execute(
                "UPDATE inventario SET cantidad = cantidad - $1 WHERE id = $2",
                cantidad, existente["id"]
            )
    return True, f"Se quitaron {cantidad}x {item}"


async def transferir_item(emisor_id: str, receptor_id: str, item: str, cantidad: int = 1) -> tuple[bool, str]:
    """Transfiere un ítem de un jugador a otro."""
    exito, msg = await quitar_item(emisor_id, item, cantidad)
    if not exito:
        return False, msg
    await agregar_item(receptor_id, item, cantidad)
    return True, "Chanchullo ejecutado >:) "
