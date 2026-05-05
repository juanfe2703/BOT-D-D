"""
Cog de administración: todos los comandos que requieren permisos de admin
agrupados en un solo lugar.
"""
import discord
from discord.ext import commands
from services.economia_service import dar_monedas_admin, quitar_monedas_admin, formato_monedas
from services.inventario_service import (
    agregar_item, quitar_item,
    agregar_producto_tienda, quitar_producto_tienda
)
from services.personaje_service import (
    obtener_personaje_activo, actualizar_personaje,
    agregar_condicion, quitar_condicion
)


def _parsear_monedas(args):
    """
    Parsea argumentos de monedas: 5o 3p 10c → (cobre, plata, oro)
    Devuelve None si el formato es inválido o si el total es 0.
    """
    cobre = plata = oro = 0
    for arg in args:
        arg = arg.lower().strip()
        try:
            if arg.endswith("o"):   oro   = int(arg[:-1])
            elif arg.endswith("p"): plata = int(arg[:-1])
            elif arg.endswith("c"): cobre = int(arg[:-1])
            else: return None
        except ValueError:
            return None
    return cobre, plata, oro


class Admin(commands.Cog, name="Administración"):
    def __init__(self, bot):
        self.bot = bot

    # ── economía ──────────────────────────────────────────────────────────────

    @commands.command(name="admin_dar", help="[ADMIN] Da monedas a un jugador. Ej: !admin_dar @u 5o 3p")
    @commands.has_permissions(administrator=True)
    async def admin_dar(self, ctx, miembro: discord.Member, *args):
        # BUG CORREGIDO #1: faltaba validar que se pasaron argumentos de monedas
        if not args:
            await ctx.send("❌ Indicá cuánto dar. Ej: `!admin_dar @usuario 5o 3p 10c`")
            return
        resultado = _parsear_monedas(args)
        if resultado is None:
            await ctx.send("❌ Formato inválido. Usá `5o`, `3p`, `10c`.")
            return
        cobre, plata, oro = resultado
        # BUG CORREGIDO #2: si todos los valores son 0, no hacer nada
        if cobre == 0 and plata == 0 and oro == 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        nuevo = await dar_monedas_admin(str(miembro.id), cobre, plata, oro)
        await ctx.send(
            f"✅ Se le dieron {formato_monedas(oro, plata, cobre)} a {miembro.mention}. "
            f"Nuevo saldo: {formato_monedas(nuevo['oro'], nuevo['plata'], nuevo['cobre'])}"
        )

    @commands.command(name="admin_quitar", help="[ADMIN] Quita monedas a un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_quitar(self, ctx, miembro: discord.Member, *args):
        if not args:
            await ctx.send("❌ Indicá cuánto quitar. Ej: `!admin_quitar @usuario 5o`")
            return
        resultado = _parsear_monedas(args)
        if resultado is None:
            await ctx.send("❌ Formato inválido. Usá `5o`, `3p`, `10c`.")
            return
        cobre, plata, oro = resultado
        if cobre == 0 and plata == 0 and oro == 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        exito, saldo = await quitar_monedas_admin(str(miembro.id), cobre, plata, oro)
        if exito:
            await ctx.send(
                f"✅ Se le quitaron {formato_monedas(oro, plata, cobre)} a {miembro.mention}. "
                f"Saldo restante: {formato_monedas(saldo['oro'], saldo['plata'], saldo['cobre'])}"
            )
        else:
            await ctx.send(
                f"❌ {miembro.mention} no tiene suficiente. "
                f"Tiene {formato_monedas(saldo['oro'], saldo['plata'], saldo['cobre'])}."
            )

    # ── inventario ────────────────────────────────────────────────────────────

    @commands.command(name="admin_agregar_item",
                      help="[ADMIN] Agrega ítems al inventario de un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_agregar_item(self, ctx, miembro: discord.Member, cantidad: int, *, item: str):
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        nombre = await agregar_item(str(miembro.id), item, cantidad)
        await ctx.send(f"✅ Se agregaron **{cantidad}× {nombre}** al inventario de {miembro.mention}.")

    @commands.command(name="admin_quitar_item",
                      help="[ADMIN] Quita ítems del inventario de un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_quitar_item(self, ctx, miembro: discord.Member, cantidad: int, *, item: str):
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        exito, msg = await quitar_item(str(miembro.id), item, cantidad)
        if exito:
            await ctx.send(f"✅ Se quitaron **{cantidad}× {item.title()}** del inventario de {miembro.mention}.")
        else:
            await ctx.send(f"❌ {msg}")

    # ── tienda ────────────────────────────────────────────────────────────────

    @commands.command(name="tienda_agregar",
                      help="[ADMIN] Agrega un producto a la tienda. Ej: !tienda_agregar 5o 2p | Espada | Descripción | stock")
    @commands.has_permissions(administrator=True)
    async def tienda_agregar(self, ctx, *args):
        texto = " ".join(args)
        partes = [p.strip() for p in texto.split("|")]

        if len(partes) < 2:
            await ctx.send(
                "❌ Formato: `!tienda_agregar <precio> | <nombre> | [descripción] | [stock]`\n"
                "Ejemplo: `!tienda_agregar 5o 2p | Espada Larga | Una espada de acero | 10`"
            )
            return

        precio_args = partes[0].split()
        nombre      = partes[1]
        descripcion = partes[2] if len(partes) > 2 else ""
        stock_raw   = partes[3] if len(partes) > 3 else "-1"

        if not nombre:
            await ctx.send("❌ El nombre del producto no puede estar vacío.")
            return

        resultado = _parsear_monedas(precio_args)
        if resultado is None:
            await ctx.send("❌ Precio inválido. Usá `5o`, `2p`, `10c`.")
            return
        cobre, plata, oro = resultado

        # BUG CORREGIDO #3: avisar si el precio queda en 0 (probablemente error del admin)
        if cobre == 0 and plata == 0 and oro == 0:
            await ctx.send(
                "⚠️ El precio quedó en **0**. Si es intencional, confirmá con "
                "`!tienda_agregar 0c | <nombre>`. "
                "Si no, revisá el formato del precio."
            )
            return

        try:
            stock = int(stock_raw)
        except ValueError:
            stock = -1

        exito, msg = await agregar_producto_tienda(nombre, descripcion, cobre, plata, oro, stock)
        if exito:
            stock_txt = "ilimitado" if stock == -1 else str(stock)
            await ctx.send(
                f"✅ **{nombre.title()}** agregado a la tienda. "
                f"Precio: {formato_monedas(oro, plata, cobre)} | Stock: {stock_txt}"
            )
        else:
            await ctx.send(f"❌ {msg}")

    @commands.command(name="tienda_quitar",
                      help="[ADMIN] Elimina un producto de la tienda.")
    @commands.has_permissions(administrator=True)
    async def tienda_quitar(self, ctx, *, nombre: str):
        exito, msg = await quitar_producto_tienda(nombre)
        if exito:
            await ctx.send(f"✅ {msg}")
        else:
            await ctx.send(f"❌ {msg}")

    # ── personajes ────────────────────────────────────────────────────────────

    @commands.command(name="admin_nivel",
                      help="[ADMIN] Establece el nivel de un personaje.")
    @commands.has_permissions(administrator=True)
    async def admin_nivel(self, ctx, miembro: discord.Member, nivel: int):
        if not 1 <= nivel <= 20:
            await ctx.send("❌ El nivel debe ser entre 1 y 20.")
            return
        personaje = await obtener_personaje_activo(str(miembro.id))
        if not personaje:
            await ctx.send(f"❌ {miembro.mention} no tiene personaje activo.")
            return
        await actualizar_personaje(str(miembro.id), nivel=nivel)
        await ctx.send(f"✅ Nivel de **{personaje['nombre']}** ({miembro.mention}) actualizado a **{nivel}**.")

    @commands.command(name="admin_set_hp",
                      help="[ADMIN] Establece el HP máximo y actual de un personaje.")
    @commands.has_permissions(administrator=True)
    async def admin_set_hp(self, ctx, miembro: discord.Member, hp_max: int, hp_actual: int = None):
        personaje = await obtener_personaje_activo(str(miembro.id))
        if not personaje:
            await ctx.send(f"❌ {miembro.mention} no tiene personaje activo.")
            return
        if hp_actual is None:
            hp_actual = hp_max
        await actualizar_personaje(str(miembro.id), hp_max=hp_max, hp_actual=hp_actual)
        await ctx.send(
            f"✅ HP de **{personaje['nombre']}** establecido a `{hp_actual}/{hp_max}`."
        )

    @commands.command(name="admin_condicion",
                      help="[ADMIN] Agrega una condición al personaje de un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_condicion(self, ctx, miembro: discord.Member, *, condicion: str):
        exito, msg = await agregar_condicion(str(miembro.id), condicion)
        if exito:
            await ctx.send(f"⚠️ Condición **{msg}** aplicada a {miembro.mention}.")
        else:
            await ctx.send(f"❌ {msg}")

    @commands.command(name="admin_quitar_condicion",
                      help="[ADMIN] Quita una condición del personaje de un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_quitar_condicion(self, ctx, miembro: discord.Member, *, condicion: str):
        exito, msg = await quitar_condicion(str(miembro.id), condicion)
        if exito:
            await ctx.send(f"✅ Condición **{msg}** eliminada de {miembro.mention}.")
        else:
            await ctx.send(f"❌ {msg}")

    @commands.command(name="admin_xp",
                      help="[ADMIN] Da XP a un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_xp(self, ctx, miembro: discord.Member, xp: int):
        personaje = await obtener_personaje_activo(str(miembro.id))
        if not personaje:
            await ctx.send(f"❌ {miembro.mention} no tiene personaje activo.")
            return
        nuevo_xp = (personaje.get("xp") or 0) + xp
        await actualizar_personaje(str(miembro.id), xp=nuevo_xp)
        signo = "+" if xp > 0 else ""
        await ctx.send(f"✨ {miembro.mention} {signo}{xp} XP. Total: **{nuevo_xp} XP**")

    # ── manejador de errores de permisos ──────────────────────────────────────
    # BUG CORREGIDO #4: sin este handler, cuando alguien sin permisos usa un
    # comando admin, Discord.py lanza CheckFailure en silencio y el bot no responde nada.

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🔒 No tenés permisos de administrador para usar ese comando.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"❌ Falta el argumento `{error.param.name}`.\n"
                f"Usá `!ayuda` para ver el uso correcto."
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Argumento inválido. Revisá el comando con `!ayuda`.")
        # No manejar otros errores acá para que los procese el handler global en main.py


async def setup(bot):
    await bot.add_cog(Admin(bot))