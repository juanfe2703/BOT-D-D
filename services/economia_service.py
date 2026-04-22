from database.db import get_pool


async def obtener_o_crear_jugador(user_id: str) -> int:
    """Devuelve el oro del jugador. Si no existe, lo crea con 1 de oro."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT oro FROM jugadores WHERE id = $1", user_id)
        if row is None:
            await conn.execute(
                "INSERT INTO jugadores (id, oro) VALUES ($1, 100)", user_id
            )
            return 1
        return row["oro"]


async def obtener_oro(user_id: str) -> int:
    return await obtener_o_crear_jugador(user_id)


async def transferir_oro(emisor_id: str, receptor_id: str, cantidad: int) -> tuple[bool, str]:
    """Transfiere oro de un jugador a otro. Retorna (éxito, mensaje)."""
    emisor_oro = await obtener_o_crear_jugador(emisor_id)
    await obtener_o_crear_jugador(receptor_id)

    if emisor_oro < cantidad:
        return False, f"Usted está pobre. Actualmente tiene **{emisor_oro}** 🪙"

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE jugadores SET oro = oro - $1 WHERE id = $2", cantidad, emisor_id
            )
            await conn.execute(
                "UPDATE jugadores SET oro = oro + $1 WHERE id = $2", cantidad, receptor_id
            )
    return True, "Transferencia realizada"


async def dar_oro_admin(receptor_id: str, cantidad: int) -> int:
    """Agrega oro a un jugador (uso de admin). Devuelve el nuevo total."""
    await obtener_o_crear_jugador(receptor_id)
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE jugadores SET oro = oro + $1 WHERE id = $2 RETURNING oro",
            cantidad, receptor_id
        )
    return row["oro"]


async def quitar_oro_admin(receptor_id: str, cantidad: int) -> tuple[bool, int]:
    """Quita oro a un jugador (uso de admin). Devuelve (éxito, nuevo total)."""
    oro_actual = await obtener_o_crear_jugador(receptor_id)
    if oro_actual < cantidad:
        return False, oro_actual
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE jugadores SET oro = oro - $1 WHERE id = $2", cantidad, receptor_id
        )
    return True, oro_actual - cantidad
