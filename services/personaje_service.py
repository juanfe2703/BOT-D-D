from database.db import get_pool
from services.economia_service import obtener_o_crear_jugador


# ─── obtener ────────────────────────────────────────────────────────────────

async def obtener_personaje_activo(jugador_id: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM personajes WHERE jugador_id=$1 AND activo=TRUE",
            jugador_id
        )
    return dict(row) if row else None


async def obtener_personaje_por_nombre(jugador_id: str, nombre: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM personajes WHERE jugador_id=$1 AND LOWER(nombre)=LOWER($2)",
            jugador_id, nombre
        )
    return dict(row) if row else None


async def listar_personajes(jugador_id: str) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM personajes WHERE jugador_id=$1 ORDER BY activo DESC, nombre",
            jugador_id
        )
    return [dict(r) for r in rows]


# ─── crear ──────────────────────────────────────────────────────────────────

async def crear_personaje(
    jugador_id: str, nombre: str, nick: str | None,
    nivel: int, clase: str, raza: str,
    hp_max: int = 0, link_ficha: str | None = None
) -> tuple[bool, str]:
    await obtener_o_crear_jugador(jugador_id)
    if await obtener_personaje_por_nombre(jugador_id, nombre):
        return False, f"Ya tienes un personaje llamado **{nombre}**."
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Desactivar personaje activo actual
            await conn.execute(
                "UPDATE personajes SET activo=FALSE WHERE jugador_id=$1 AND activo=TRUE",
                jugador_id
            )
            await conn.execute(
                """INSERT INTO personajes
                   (jugador_id, nombre, nick, nivel, clase, raza, hp_max, hp_actual, xp, link_ficha, activo)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$7,$8,$9,TRUE)""",
                jugador_id, nombre.strip(), nick, nivel, clase, raza,
                hp_max, 0, link_ficha
            )
        return True, "Personaje creado exitosamente"
    except Exception as e:
        return False, f"Error al crear personaje: {e}"


# ─── actualizar ─────────────────────────────────────────────────────────────

async def actualizar_personaje(jugador_id: str, nombre_personaje: str | None = None, **campos) -> tuple[bool, str]:
    """Actualiza el personaje activo (o el especificado por nombre_personaje)."""
    if nombre_personaje:
        personaje = await obtener_personaje_por_nombre(jugador_id, nombre_personaje)
    else:
        personaje = await obtener_personaje_activo(jugador_id)

    if not personaje:
        return False, "No se encontró el personaje."

    campos_validos = {"nombre", "nick", "nivel", "clase", "raza", "link_ficha", "hp_max", "hp_actual", "xp"}
    actualizaciones = {k: v for k, v in campos.items() if k in campos_validos and v is not None}
    if not actualizaciones:
        return False, "No se especificó ningún campo válido."

    keys   = list(actualizaciones.keys())
    values = list(actualizaciones.values())
    set_clause = ", ".join(f"{k}=${i+1}" for i, k in enumerate(keys))
    values.append(personaje["id"])

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE personajes SET {set_clause} WHERE id=${len(values)}",
            *values
        )
    return True, "Personaje actualizado"


# ─── cambiar activo ─────────────────────────────────────────────────────────

async def cambiar_personaje_activo(jugador_id: str, nombre: str) -> tuple[bool, str]:
    personaje = await obtener_personaje_por_nombre(jugador_id, nombre)
    if not personaje:
        return False, f"No tienes ningún personaje llamado **{nombre}**."
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE personajes SET activo=FALSE WHERE jugador_id=$1", jugador_id
            )
            await conn.execute(
                "UPDATE personajes SET activo=TRUE WHERE id=$1", personaje["id"]
            )
    return True, f"Ahora jugando como **{personaje['nombre']}**."


# ─── HP ─────────────────────────────────────────────────────────────────────

async def modificar_hp(jugador_id: str, delta: int) -> tuple[bool, dict]:
    """Suma o resta HP al personaje activo. Nunca baja de 0 ni sube de hp_max."""
    personaje = await obtener_personaje_activo(jugador_id)
    if not personaje:
        return False, {}
    nuevo_hp = max(0, min(personaje["hp_max"], personaje["hp_actual"] + delta))
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE personajes SET hp_actual=$1 WHERE id=$2",
            nuevo_hp, personaje["id"]
        )
    personaje["hp_actual"] = nuevo_hp
    return True, personaje


# ─── condiciones ────────────────────────────────────────────────────────────

async def agregar_condicion(jugador_id: str, condicion: str) -> tuple[bool, str]:
    personaje = await obtener_personaje_activo(jugador_id)
    if not personaje:
        return False, "No tienes personaje activo."
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO condiciones (personaje_id, condicion) VALUES ($1, $2)",
            personaje["id"], condicion.strip().lower()
        )
    return True, condicion


async def quitar_condicion(jugador_id: str, condicion: str) -> tuple[bool, str]:
    personaje = await obtener_personaje_activo(jugador_id)
    if not personaje:
        return False, "No tienes personaje activo."
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM condiciones WHERE personaje_id=$1 AND LOWER(condicion)=LOWER($2)",
            personaje["id"], condicion.strip()
        )
    if result == "DELETE 0":
        return False, f"**{condicion}** no estaba activa."
    return True, condicion


async def obtener_condiciones(personaje_id: int) -> list[str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT condicion FROM condiciones WHERE personaje_id=$1 ORDER BY condicion",
            personaje_id
        )
    return [r["condicion"] for r in rows]
