"""
Comandos de administración para NPCs.
Se agregan como una extensión separada del cog Admin principal
para mantener el archivo manejable.
"""
import discord
from discord.ext import commands
from services.npc_service import (
    listar_npcs, obtener_npc, crear_npc, editar_npc, eliminar_npc,
    obtener_inventario_npc, agregar_item_npc, quitar_item_npc,
)
from services.economia_service import formato_monedas


def _parsear_precio(args: list[str]) -> tuple[int, int, int] | None:
    """Parsea una lista de strings tipo ['5o', '3p', '10c'] → (cobre, plata, oro)."""
    cobre = plata = oro = 0
    for arg in args:
        arg = arg.lower().strip()
        try:
            if arg.endswith("o"):
                oro   = int(arg[:-1])
            elif arg.endswith("p"):
                plata = int(arg[:-1])
            elif arg.endswith("c"):
                cobre = int(arg[:-1])
            else:
                return None
        except ValueError:
            return None
    return cobre, plata, oro


class AdminNpcs(commands.Cog, name="Admin NPCs"):
    def __init__(self, bot):
        self.bot = bot

    # ── Crear NPC ─────────────────────────────────────────────────────────────

    @commands.command(
        name="npc_crear",
        help=(
            "[ADMIN] Crea un NPC nuevo.\n"
            "Formato: !npc_crear <nombre> | [descripción] | [url_imagen]\n"
            "Ejemplo: !npc_crear Gausto | El mejor cocinero del reino | https://i.imgur.com/xxx.png"
        ),
    )
    @commands.has_permissions(administrator=True)
    async def npc_crear(self, ctx, *, args: str):
        partes = [p.strip() for p in args.split("|")]
        nombre      = partes[0]
        descripcion = partes[1] if len(partes) > 1 else ""
        imagen_url  = partes[2] if len(partes) > 2 else ""

        if not nombre:
            await ctx.send("❌ Debes indicar al menos el nombre del NPC.")
            return

        exito, resultado = await crear_npc(
            nombre=nombre,
            descripcion=descripcion,
            imagen_url=imagen_url,
        )
        if exito:
            embed = discord.Embed(
                title=f"🧙 NPC creado: {nombre.title()}",
                color=discord.Color.teal(),
            )
            if descripcion:
                embed.description = f"*{descripcion}*"
            if imagen_url:
                embed.set_thumbnail(url=imagen_url)
            embed.add_field(
                name="Siguiente paso",
                value=(
                    f"Agregá productos con:\n"
                    f"`!npc_item_agregar {nombre.title()} | <precio> | <ítem> | [desc] | [stock]`"
                ),
                inline=False,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {resultado}")

    # ── Editar NPC ────────────────────────────────────────────────────────────

    @commands.command(
        name="npc_editar",
        help=(
            "[ADMIN] Edita un campo de un NPC existente.\n"
            "Formato: !npc_editar <nombre> <campo> | <valor>\n"
            "Campos: descripcion, imagen_url, dialogo_bienvenida, dialogo_venta, dialogo_sin_stock\n"
            "Ejemplo: !npc_editar Gausto dialogo_venta | ¡Excelente elección, aventurero!"
        ),
    )
    @commands.has_permissions(administrator=True)
    async def npc_editar(self, ctx, npc_nombre: str, campo: str, *, valor: str):
        campos_validos = {
            "descripcion", "imagen_url",
            "dialogo_bienvenida", "dialogo_venta", "dialogo_sin_stock",
        }
        if campo not in campos_validos:
            await ctx.send(
                f"❌ Campo inválido. Los campos editables son:\n"
                f"`{'`, `'.join(sorted(campos_validos))}`"
            )
            return

        exito, msg = await editar_npc(npc_nombre, **{campo: valor})
        if exito:
            await ctx.send(f"✅ **{npc_nombre.title()}** — campo `{campo}` actualizado.")
        else:
            await ctx.send(f"❌ {msg}")

    # ── Eliminar NPC ──────────────────────────────────────────────────────────

    @commands.command(
        name="npc_eliminar",
        help="[ADMIN] Elimina un NPC. Ej: !npc_eliminar Gausto",
    )
    @commands.has_permissions(administrator=True)
    async def npc_eliminar(self, ctx, *, nombre: str):
        exito, msg = await eliminar_npc(nombre)
        if exito:
            await ctx.send(f"🗑️ {msg}")
        else:
            await ctx.send(f"❌ {msg}")

    # ── Ver inventario NPC (admin) ────────────────────────────────────────────

    @commands.command(
        name="npc_inv",
        help="[ADMIN] Muestra el inventario completo de un NPC. Ej: !npc_inv Gausto",
    )
    @commands.has_permissions(administrator=True)
    async def npc_inv(self, ctx, *, nombre: str):
        npc = await obtener_npc(nombre)
        if not npc:
            await ctx.send(f"❌ No existe el NPC **{nombre.title()}**.")
            return

        items = await obtener_inventario_npc(npc["id"])
        embed = discord.Embed(
            title=f"📋 Inventario de {npc['nombre']} (admin)",
            color=discord.Color.blurple(),
        )
        if npc.get("imagen_url"):
            embed.set_thumbnail(url=npc["imagen_url"])

        if not items:
            embed.description = "*Sin productos cargados.*"
        else:
            lineas = []
            for p in items:
                precio = formato_monedas(
                    p["precio_oro"], p["precio_plata"], p["precio_cobre"]
                )
                stock_txt = "∞" if p["stock"] == -1 else str(p["stock"])
                desc = f" — *{p['descripcion']}*" if p.get("descripcion") else ""
                lineas.append(f"• **{p['item']}**{desc} | {precio} | Stock: {stock_txt}")
            embed.description = "\n".join(lineas)

        await ctx.send(embed=embed)

    # ── Agregar ítem a NPC (uno) ──────────────────────────────────────────────

    @commands.command(
        name="npc_item_agregar",
        aliases=["npc_ia"],
        help=(
            "[ADMIN] Agrega un ítem al inventario de un NPC.\n"
            "Formato: !npc_item_agregar <NPC> | <precio> | <ítem> | [desc] | [stock]\n"
            "Precio: combinación de 5o 2p 10c  (stock -1 = ilimitado)\n"
            "Ejemplo: !npc_item_agregar Gausto | 3o | Estofado Real | Delicioso | 20"
        ),
    )
    @commands.has_permissions(administrator=True)
    async def npc_item_agregar(self, ctx, *, args: str):
        partes = [p.strip() for p in args.split("|")]
        if len(partes) < 3:
            await ctx.send(
                "❌ Formato: `!npc_item_agregar <NPC> | <precio> | <ítem> | [desc] | [stock]`\n"
                "Ejemplo: `!npc_item_agregar Gausto | 3o | Estofado Real | Delicioso | 20`"
            )
            return

        npc_nombre  = partes[0]
        precio_raw  = partes[1].split()
        item_nombre = partes[2]
        descripcion = partes[3] if len(partes) > 3 else ""
        stock_raw   = partes[4] if len(partes) > 4 else "-1"

        npc = await obtener_npc(npc_nombre)
        if not npc:
            await ctx.send(f"❌ No existe el NPC **{npc_nombre.title()}**.")
            return

        resultado_precio = _parsear_precio(precio_raw)
        if resultado_precio is None:
            await ctx.send("❌ Precio inválido. Usá `5o`, `2p`, `10c`.")
            return
        cobre, plata, oro = resultado_precio

        try:
            stock = int(stock_raw)
        except ValueError:
            stock = -1

        exito, msg = await agregar_item_npc(
            npc["id"], item_nombre, cobre, plata, oro, stock, descripcion
        )
        if exito:
            precio_fmt = formato_monedas(oro, plata, cobre)
            stock_txt  = "ilimitado" if stock == -1 else str(stock)
            await ctx.send(
                f"✅ **{item_nombre.title()}** agregado a **{npc['nombre']}**. "
                f"Precio: {precio_fmt} | Stock: {stock_txt}"
            )
        else:
            await ctx.send(f"❌ {msg}")

    # ── Agregar MÚLTIPLES ítems a NPC (bulk) ──────────────────────────────────

    @commands.command(
        name="npc_items_agregar",
        aliases=["npc_ias"],
        help=(
            "[ADMIN] Agrega varios ítems al inventario de un NPC de una sola vez.\n"
            "Cada ítem en una línea separada con el formato: precio | ítem | [desc] | [stock]\n\n"
            "Ejemplo:\n"
            "!npc_items_agregar Gausto\n"
            "3o | Estofado Real | Delicioso guiso | 20\n"
            "1o 5p | Pan de Centeno | Crujiente |\n"
            "2o | Vino Élfico || 10"
        ),
    )
    @commands.has_permissions(administrator=True)
    async def npc_items_agregar(self, ctx, npc_nombre: str, *, items_raw: str):
        npc = await obtener_npc(npc_nombre)
        if not npc:
            await ctx.send(f"❌ No existe el NPC **{npc_nombre.title()}**.")
            return

        lineas = [l.strip() for l in items_raw.strip().splitlines() if l.strip()]
        if not lineas:
            await ctx.send("❌ No se encontraron ítems para agregar.")
            return

        resultados_ok  = []
        resultados_err = []

        for linea in lineas:
            partes = [p.strip() for p in linea.split("|")]
            if len(partes) < 2:
                resultados_err.append(f"`{linea}` — formato incorrecto (faltan campos)")
                continue

            precio_raw  = partes[0].split()
            item_nombre = partes[1]
            descripcion = partes[2] if len(partes) > 2 else ""
            stock_raw   = partes[3] if len(partes) > 3 else "-1"

            if not item_nombre:
                resultados_err.append(f"`{linea}` — el nombre del ítem no puede estar vacío")
                continue

            resultado_precio = _parsear_precio(precio_raw)
            if resultado_precio is None:
                resultados_err.append(f"`{item_nombre}` — precio inválido (`{partes[0]}`)")
                continue
            cobre, plata, oro = resultado_precio

            try:
                stock = int(stock_raw) if stock_raw else -1
            except ValueError:
                stock = -1

            exito, msg = await agregar_item_npc(
                npc["id"], item_nombre, cobre, plata, oro, stock, descripcion
            )
            if exito:
                precio_fmt = formato_monedas(oro, plata, cobre)
                stock_txt  = "∞" if stock == -1 else str(stock)
                resultados_ok.append(f"✅ **{item_nombre.title()}** — {precio_fmt} | {stock_txt}")
            else:
                resultados_err.append(f"❌ **{item_nombre.title()}** — {msg}")

        embed = discord.Embed(
            title=f"📦 Carga masiva → {npc['nombre']}",
            color=discord.Color.green() if not resultados_err else discord.Color.orange(),
        )
        if npc.get("imagen_url"):
            embed.set_thumbnail(url=npc["imagen_url"])
        if resultados_ok:
            embed.add_field(
                name=f"Agregados ({len(resultados_ok)})",
                value="\n".join(resultados_ok),
                inline=False,
            )
        if resultados_err:
            embed.add_field(
                name=f"Errores ({len(resultados_err)})",
                value="\n".join(resultados_err),
                inline=False,
            )
        await ctx.send(embed=embed)

    # ── Quitar ítem de NPC ────────────────────────────────────────────────────

    @commands.command(
        name="npc_item_quitar",
        aliases=["npc_iq"],
        help=(
            "[ADMIN] Quita un ítem del inventario de un NPC.\n"
            "Ejemplo: !npc_item_quitar Gausto | Estofado Real"
        ),
    )
    @commands.has_permissions(administrator=True)
    async def npc_item_quitar(self, ctx, *, args: str):
        partes = [p.strip() for p in args.split("|")]
        if len(partes) < 2:
            await ctx.send(
                "❌ Formato: `!npc_item_quitar <NPC> | <ítem>`\n"
                "Ejemplo: `!npc_item_quitar Gausto | Estofado Real`"
            )
            return

        npc_nombre  = partes[0]
        item_nombre = partes[1]

        npc = await obtener_npc(npc_nombre)
        if not npc:
            await ctx.send(f"❌ No existe el NPC **{npc_nombre.title()}**.")
            return

        exito, msg = await quitar_item_npc(npc["id"], item_nombre)
        if exito:
            await ctx.send(f"✅ {msg} del inventario de **{npc['nombre']}**.")
        else:
            await ctx.send(f"❌ {msg}")

    # ── Listar todos los NPCs (admin) ─────────────────────────────────────────

    @commands.command(
        name="npc_lista",
        help="[ADMIN] Lista todos los NPCs con sus IDs internos.",
    )
    @commands.has_permissions(administrator=True)
    async def npc_lista(self, ctx):
        lista = await listar_npcs()
        if not lista:
            await ctx.send("📭 No hay NPCs registrados.")
            return

        embed = discord.Embed(
            title="🗂️ Lista de NPCs (admin)",
            color=discord.Color.blurple(),
        )
        for npc in lista:
            items = await obtener_inventario_npc(npc["id"])
            embed.add_field(
                name=f"ID {npc['id']} — {npc['nombre']}",
                value=(
                    f"{npc['descripcion'] or '*Sin descripción*'}\n"
                    f"Productos: **{len(items)}**"
                ),
                inline=False,
            )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AdminNpcs(bot))
