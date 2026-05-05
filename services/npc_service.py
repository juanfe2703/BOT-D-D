"""
Servicio de NPCs: maneja la creación, edición, consulta
de NPCs y sus inventarios, y la lógica de compra.
"""
from database.db import get_pool
from services.economia_service import (
    obtener_o_crear_jugador, a_cobre, desde_cobre, formato_monedas
)


# ─── NPCs ────────────────────────────────────────────────────────────────────

async def listar_npcs() -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM npcs WHERE activo=TRUE ORDER BY nombre"
        )
    return [dict(r) for r in rows]


async def obtener_npc(nombre: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM npcs WHERE LOWER(nombre)=LOWER($1) AND activo=TRUE",
            nombre.strip()
        )
    return dict(row) if row else None


async def crear_npc(
    nombre: str,
    descripcion: str = "",
    imagen_url: str = "",
    dialogo_bienvenida: str = "",
    dialogo_venta: str = "",
    dialogo_sin_stock: str = "",
) -> tuple[bool, str]:
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO npcs
                       (nombre, descripcion, imagen_url,
                        dialogo_bienvenida, dialogo_venta, dialogo_sin_stock)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   RETURNING id""",
                nombre.strip().title(),
                descripcion.strip(),
                imagen_url.strip(),
                dialogo_bienvenida.strip(),
                dialogo_venta.strip(),
                dialogo_sin_stock.strip(),
            )
        return True, str(row["id"])
    except Exception as e:
        if "unique" in str(e).lower():
            return False, f"Ya existe un NPC llamado **{nombre.title()}**."
        return False, str(e)


async def editar_npc(nombre: str, **kwargs) -> tuple[bool, str]:
    campos_validos = {
        "descripcion", "imagen_url",
        "dialogo_bienvenida", "dialogo_venta", "dialogo_sin_stock"
    }
    validos = {k: v.strip() for k, v in kwargs.items() if k in campos_validos and v is not None}
    if not validos:
        return False, "No se proporcionaron campos válidos para actualizar."

    pool = await get_pool()
    npc = await obtener_npc(nombre)
    if not npc:
        return False, f"No existe el NPC **{nombre.title()}**."

    sets = ", ".join(f"{k}=${i+2}" for i, k in enumerate(validos))
    valores = list(validos.values())
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE npcs SET {sets} WHERE id=$1",
            npc["id"], *valores
        )
    return True, "NPC actualizado."


async def eliminar_npc(nombre: str) -> tuple[bool, str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE npcs SET activo=FALSE WHERE LOWER(nombre)=LOWER($1) AND activo=TRUE",
            nombre.strip()
        )
    if result == "UPDATE 0":
        return False, f"No existe el NPC **{nombre.title()}**."
    return True, f"NPC **{nombre.title()}** eliminado."


# ─── Inventario de NPC ───────────────────────────────────────────────────────

async def obtener_inventario_npc(npc_id: int) -> list:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, item, descripcion,
                      precio_cobre, precio_plata, precio_oro, stock
               FROM npc_inventario
               WHERE npc_id=$1 AND activo=TRUE
               ORDER BY item""",
            npc_id
        )
    return [dict(r) for r in rows]


async def agregar_item_npc(
    npc_id: int,
    item: str,
    precio_cobre: int = 0,
    precio_plata: int = 0,
    precio_oro: int = 0,
    stock: int = -1,
    descripcion: str = "",
) -> tuple[bool, str]:
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            npc = await conn.fetchrow(
                "SELECT id FROM npcs WHERE id=$1 AND activo=TRUE", npc_id
            )
            if not npc:
                return False, "NPC no encontrado."
            await conn.execute(
                """INSERT INTO npc_inventario
                       (npc_id, item, descripcion,
                        precio_cobre, precio_plata, precio_oro, stock)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT (npc_id, item) DO UPDATE
                   SET descripcion=$3, precio_cobre=$4, precio_plata=$5,
                       precio_oro=$6, stock=$7, activo=TRUE""",
                npc_id, item.strip().title(), descripcion.strip(),
                precio_cobre, precio_plata, precio_oro, stock
            )
        return True, f"**{item.title()}** agregado al inventario."
    except Exception as e:
        return False, str(e)


async def quitar_item_npc(npc_id: int, item: str) -> tuple[bool, str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """UPDATE npc_inventario SET activo=FALSE
               WHERE npc_id=$1 AND LOWER(item)=LOWER($2)""",
            npc_id, item.strip()
        )
    if result == "UPDATE 0":
        return False, f"No existe **{item.title()}** en el inventario de ese NPC."
    return True, f"**{item.title()}** eliminado del inventario."


# ─── Compra a NPC ─────────────────────────────────────────────────────────────

async def comprar_a_npc(
    jugador_id: str,
    npc_nombre: str,
    item_nombre: str,
    cantidad: int = 1,
) -> tuple[bool, str, dict | None]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        npc = await conn.fetchrow(
            "SELECT * FROM npcs WHERE LOWER(nombre)=LOWER($1) AND activo=TRUE",
            npc_nombre.strip()
        )
        if not npc:
            return False, f"No existe ningún NPC llamado **{npc_nombre.title()}**.", None

        npc = dict(npc)

        producto = await conn.fetchrow(
            """SELECT * FROM npc_inventario
               WHERE npc_id=$1 AND LOWER(item)=LOWER($2) AND activo=TRUE""",
            npc["id"], item_nombre.strip()
        )
        if not producto:
            dialogo = (
                npc["dialogo_sin_stock"]
                or f"*{npc['nombre']} niega con la cabeza.* — No tengo **{item_nombre.title()}**, lo siento."
            )
            return False, dialogo, npc

        producto = dict(producto)

        if producto["stock"] == 0:
            dialogo = (
                npc["dialogo_sin_stock"]
                or f"*{npc['nombre']} revisa sus estantes y suspira.* — Me quedé sin **{producto['item']}**."
            )
            return False, dialogo, npc

        if producto["stock"] != -1 and producto["stock"] < cantidad:
            dialogo = (
                f"*{npc['nombre']} levanta {producto['stock']} dedo(s).* "
                f"— Solo me quedan **{producto['stock']}** unidades de **{producto['item']}**."
            )
            return False, dialogo, npc

        precio_unit  = a_cobre(producto["precio_cobre"], producto["precio_plata"], producto["precio_oro"])
        precio_total = precio_unit * cantidad

        jugador = await obtener_o_crear_jugador(jugador_id)
        saldo   = a_cobre(jugador["cobre"], jugador["plata"], jugador["oro"])

        if saldo < precio_total:
            faltante = desde_cobre(precio_total - saldo)
            dialogo = (
                f"*{npc['nombre']} te mira con escepticismo.* "
                f"— No tienes suficiente. Te faltan **{formato_monedas(**faltante)}**."
            )
            return False, dialogo, npc

        nuevo_saldo = desde_cobre(saldo - precio_total)

        # BUG CORREGIDO: el insert al inventario del jugador ahora está DENTRO
        # del bloque transaction. Antes estaba afuera: si fallaba, el jugador
        # perdía el dinero pero no recibía el ítem.
        async with conn.transaction():
            await conn.execute(
                "UPDATE jugadores SET cobre=$1, plata=$2, oro=$3 WHERE id=$4",
                nuevo_saldo["cobre"], nuevo_saldo["plata"], nuevo_saldo["oro"], jugador_id,
            )
            if producto["stock"] != -1:
                await conn.execute(
                    "UPDATE npc_inventario SET stock=stock-$1 WHERE id=$2",
                    cantidad, producto["id"],
                )
            await conn.execute(
                """INSERT INTO transacciones
                       (emisor_id, tipo, cobre, plata, oro, detalle)
                   VALUES ($1, 'compra_npc', $2, $3, $4, $5)""",
                jugador_id,
                producto["precio_cobre"] * cantidad,
                producto["precio_plata"] * cantidad,
                producto["precio_oro"]   * cantidad,
                f"Compró {cantidad}x {producto['item']} a {npc['nombre']}",
            )
            # Agregar ítem al inventario dentro de la misma transacción
            item_norm = producto["item"].strip().title()
            existente = await conn.fetchrow(
                "SELECT id FROM inventario WHERE jugador_id=$1 AND LOWER(item)=LOWER($2)",
                jugador_id, item_norm
            )
            if existente:
                await conn.execute(
                    "UPDATE inventario SET cantidad=cantidad+$1 WHERE id=$2",
                    cantidad, existente["id"]
                )
            else:
                await conn.execute(
                    "INSERT INTO inventario (jugador_id, item, cantidad) VALUES ($1, $2, $3)",
                    jugador_id, item_norm, cantidad
                )

    dialogo = (
        npc["dialogo_venta"]
        or f"*{npc['nombre']} sonríe y envuelve el artículo.* — ¡Trato hecho! Que te sea útil."
    )
    return True, dialogo, npc