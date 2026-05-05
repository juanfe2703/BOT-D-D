"""
Sistema monetario: cobre < plata < oro
  1 plata = 100 cobre
  1 oro   = 100 plata  = 10 000 cobre
"""
from database.db import get_pool


# ─── helpers ────────────────────────────────────────────────────────────────

def a_cobre(cobre: int = 0, plata: int = 0, oro: int = 0) -> int:
    """Convierte cualquier combinación de monedas a cobre total."""
    return cobre + plata * 100 + oro * 10_000


def desde_cobre(total: int) -> dict:
    """Descompone un total de cobre en oro/plata/cobre de forma óptima."""
    oro   = total // 10_000
    resto = total %  10_000
    plata = resto  // 100
    cobre = resto  %  100
    return {"oro": oro, "plata": plata, "cobre": cobre}


def formato_monedas(oro: int, plata: int, cobre: int) -> str:
    """Devuelve string legible, omitiendo denominaciones en 0."""
    partes = []
    if oro:   partes.append(f"**{oro}** 🥇")
    if plata: partes.append(f"**{plata}** 🥈")
    if cobre: partes.append(f"**{cobre}** 🟤")
    return " · ".join(partes) if partes else "**0** 🟤"


# ─── jugador ────────────────────────────────────────────────────────────────

async def obtener_o_crear_jugador(user_id: str) -> dict:
    """
    Devuelve la fila del jugador como dict. Si no existe, la crea con 100 cobre.

    BUG CORREGIDO: la versión anterior hacía INSERT y luego un segundo SELECT
    en autocommit separado. En PostgreSQL local con asyncpg esto podía devolver
    None en el segundo fetchrow (el INSERT aún no era visible), causando que
    dict(None) lanzara TypeError, o que asyncpg devolviera un Record sin las
    columnas esperadas → KeyError: 'plata'.

    Solución: usar INSERT ... ON CONFLICT DO NOTHING ... RETURNING *.
    Si el jugador ya existe, el RETURNING no devuelve nada, y hacemos
    un SELECT dentro de la misma transacción. Todo en una sola conexión,
    sin race conditions.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Intentar insertar; si ya existe no hace nada
            row = await conn.fetchrow(
                """INSERT INTO jugadores (id, cobre, plata, oro)
                   VALUES ($1, 100, 0, 0)
                   ON CONFLICT (id) DO NOTHING
                   RETURNING *""",
                user_id
            )
            if row is None:
                # Ya existía, traerlo
                row = await conn.fetchrow(
                    "SELECT * FROM jugadores WHERE id = $1", user_id
                )
    return dict(row)


async def obtener_monedas(user_id: str) -> dict:
    return await obtener_o_crear_jugador(user_id)


# ─── transferencias ─────────────────────────────────────────────────────────

async def transferir_monedas(
    emisor_id: str, receptor_id: str,
    cobre: int = 0, plata: int = 0, oro: int = 0
) -> tuple[bool, str]:
    """Transfiere monedas. Descuenta del saldo total del emisor."""
    total_envio = a_cobre(cobre, plata, oro)
    if total_envio <= 0:
        return False, "La cantidad debe ser mayor a 0."

    emisor = await obtener_o_crear_jugador(emisor_id)
    await obtener_o_crear_jugador(receptor_id)

    total_emisor = a_cobre(emisor["cobre"], emisor["plata"], emisor["oro"])
    if total_emisor < total_envio:
        restante = desde_cobre(total_emisor)
        return False, f"No tienes suficiente. Tienes {formato_monedas(**restante)}."

    nuevo_emisor = desde_cobre(total_emisor - total_envio)

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE jugadores SET cobre=$1, plata=$2, oro=$3 WHERE id=$4",
                nuevo_emisor["cobre"], nuevo_emisor["plata"], nuevo_emisor["oro"], emisor_id
            )
            receptor = await conn.fetchrow("SELECT * FROM jugadores WHERE id=$1", receptor_id)
            total_receptor = a_cobre(receptor["cobre"], receptor["plata"], receptor["oro"])
            nuevo_receptor = desde_cobre(total_receptor + total_envio)
            await conn.execute(
                "UPDATE jugadores SET cobre=$1, plata=$2, oro=$3 WHERE id=$4",
                nuevo_receptor["cobre"], nuevo_receptor["plata"], nuevo_receptor["oro"], receptor_id
            )
            await conn.execute(
                """INSERT INTO transacciones (emisor_id, receptor_id, tipo, cobre, plata, oro, detalle)
                   VALUES ($1, $2, 'transferencia', $3, $4, $5, $6)""",
                emisor_id, receptor_id, cobre, plata, oro,
                f"Transferencia de {formato_monedas(oro, plata, cobre)}"
            )
    return True, "Transferencia realizada"


# ─── admin ──────────────────────────────────────────────────────────────────

async def dar_monedas_admin(
    receptor_id: str,
    cobre: int = 0, plata: int = 0, oro: int = 0
) -> dict:
    """Añade monedas (admin). Devuelve el nuevo saldo."""
    total_add = a_cobre(cobre, plata, oro)
    jugador = await obtener_o_crear_jugador(receptor_id)
    total_actual = a_cobre(jugador["cobre"], jugador["plata"], jugador["oro"])
    nuevo = desde_cobre(total_actual + total_add)

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE jugadores SET cobre=$1, plata=$2, oro=$3 WHERE id=$4",
            nuevo["cobre"], nuevo["plata"], nuevo["oro"], receptor_id
        )
        await conn.execute(
            """INSERT INTO transacciones (receptor_id, tipo, cobre, plata, oro, detalle)
               VALUES ($1, 'admin_dar', $2, $3, $4, $5)""",
            receptor_id, cobre, plata, oro,
            f"Admin dio {formato_monedas(oro, plata, cobre)}"
        )
    return nuevo


async def quitar_monedas_admin(
    receptor_id: str,
    cobre: int = 0, plata: int = 0, oro: int = 0
) -> tuple[bool, dict]:
    """Quita monedas (admin). Devuelve (éxito, saldo_actual)."""
    total_quitar = a_cobre(cobre, plata, oro)
    jugador = await obtener_o_crear_jugador(receptor_id)
    total_actual = a_cobre(jugador["cobre"], jugador["plata"], jugador["oro"])

    if total_actual < total_quitar:
        return False, desde_cobre(total_actual)

    nuevo = desde_cobre(total_actual - total_quitar)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE jugadores SET cobre=$1, plata=$2, oro=$3 WHERE id=$4",
            nuevo["cobre"], nuevo["plata"], nuevo["oro"], receptor_id
        )
        await conn.execute(
            """INSERT INTO transacciones (receptor_id, tipo, cobre, plata, oro, detalle)
               VALUES ($1, 'admin_quitar', $2, $3, $4, $5)""",
            receptor_id, cobre, plata, oro,
            f"Admin quitó {formato_monedas(oro, plata, cobre)}"
        )
    return True, nuevo


# ─── historial ──────────────────────────────────────────────────────────────

async def obtener_historial(user_id: str, limite: int = 10) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM transacciones
               WHERE emisor_id = $1 OR receptor_id = $1
               ORDER BY creado_en DESC LIMIT $2""",
            user_id, limite
        )
    return [dict(r) for r in rows]


# ─── leaderboard ────────────────────────────────────────────────────────────

async def obtener_leaderboard(limite: int = 10) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id,
                      oro * 10000 + plata * 100 + cobre AS total_cobre,
                      oro, plata, cobre
               FROM jugadores
               ORDER BY total_cobre DESC
               LIMIT $1""",
            limite
        )
    return [dict(r) for r in rows]