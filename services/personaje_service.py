from database.db import get_pool
from services.economia_service import obtener_o_crear_jugador


async def obtener_personaje(jugador_id: str) -> dict | None:
    """Devuelve el personaje del jugador o None si no tiene."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM personajes WHERE jugador_id = $1", jugador_id
        )
    if row is None:
        return None
    return dict(row)


async def crear_personaje(jugador_id: str, nombre: str, nick: str, nivel: int,
                          clase: str, raza: str, link_ficha: str = None) -> tuple[bool, str]:
    """Crea un personaje. Retorna (éxito, mensaje)."""
    await obtener_o_crear_jugador(jugador_id)
    if await obtener_personaje(jugador_id):
        return False, "Ya tienes un personaje creado. Usa `!actualizar_personaje` para editarlo."
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO personajes (jugador_id, nombre, nick, nivel, clase, raza, link_ficha)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                jugador_id, nombre, nick, nivel, clase, raza, link_ficha
            )
        return True, "Personaje creado exitosamente"
    except Exception as e:
        return False, f"Error al crear personaje: {e}"


async def actualizar_personaje(jugador_id: str, **campos) -> tuple[bool, str]:
    """
    Actualiza campos del personaje. Solo actualiza los campos pasados.
    Campos válidos: nombre, nick, nivel, clase, raza, link_ficha
    """
    if not await obtener_personaje(jugador_id):
        return False, "No tienes un personaje creado todavía. Usa `!crear_personaje`."

    campos_validos = {"nombre", "nick", "nivel", "clase", "raza", "link_ficha"}
    actualizaciones = {k: v for k, v in campos.items() if k in campos_validos and v is not None}

    if not actualizaciones:
        return False, "No se especificó ningún campo válido para actualizar."

    # PostgreSQL usa $1, $2... en lugar de ?
    keys = list(actualizaciones.keys())
    values = list(actualizaciones.values())
    set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(keys))
    values.append(jugador_id)
    where_placeholder = f"${len(values)}"

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE personajes SET {set_clause} WHERE jugador_id = {where_placeholder}",
            *values
        )
    return True, "Personaje actualizado"
