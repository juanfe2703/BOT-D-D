"""
Cog de NPCs: comandos para que los jugadores interactúen
con los personajes no jugadores y sus tiendas individuales.
"""
import discord
from discord.ext import commands
from services.npc_service import (
    listar_npcs, obtener_npc,
    obtener_inventario_npc, comprar_a_npc,
)
from services.economia_service import formato_monedas


def _embed_npc(npc: dict, titulo: str, color=discord.Color.teal()) -> discord.Embed:
    embed = discord.Embed(title=titulo, color=color)
    if npc.get("descripcion"):
        embed.description = f"*{npc['descripcion']}*"
    if npc.get("imagen_url"):
        embed.set_thumbnail(url=npc["imagen_url"])
    return embed


class Npcs(commands.Cog, name="NPCs"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="npcs", help="Muestra todos los NPCs disponibles.")
    async def npcs(self, ctx):
        lista = await listar_npcs()
        if not lista:
            await ctx.send("📭 No hay ningún NPC registrado todavía.")
            return
        embed = discord.Embed(
            title="🧑‍🤝‍🧑 NPCs disponibles",
            description="Usá `!npc <nombre>` para hablar con alguno.",
            color=discord.Color.teal(),
        )
        for npc in lista:
            embed.add_field(
                name=f"• {npc['nombre']}",
                value=npc["descripcion"] or "*Sin descripción.*",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command(name="npc", help="Interactúa con un NPC. Ej: !npc Gausto")
    async def npc(self, ctx, *, nombre: str):
        npc = await obtener_npc(nombre)
        if not npc:
            await ctx.send(
                f"❌ No encontré ningún NPC llamado **{nombre.title()}**. "
                f"Usá `!npcs` para ver la lista."
            )
            return

        embed = _embed_npc(npc, titulo=f"🧙 {npc['nombre']}", color=discord.Color.teal())
        bienvenida = (
            npc["dialogo_bienvenida"]
            or f"*{npc['nombre']} te mira y asiente con la cabeza.* — ¿En qué te puedo ayudar?"
        )
        embed.add_field(name="💬", value=bienvenida, inline=False)

        items = await obtener_inventario_npc(npc["id"])
        if not items:
            embed.add_field(name="🛍️ Inventario", value="*No tiene nada para vender.*", inline=False)
        else:
            lineas = []
            for p in items:
                precio    = formato_monedas(p["precio_oro"], p["precio_plata"], p["precio_cobre"])
                stock_txt = "∞" if p["stock"] == -1 else str(p["stock"])
                desc      = f" — *{p['descripcion']}*" if p.get("descripcion") else ""
                lineas.append(f"🔹 **{p['item']}**{desc}\n  Precio: {precio} · Stock: {stock_txt}")
            embed.add_field(name="🛍️ Lo que vende", value="\n".join(lineas), inline=False)

        embed.set_footer(text=f"Comprá con: !comprar_npc {npc['nombre']} <ítem>  o  !comprar_npc {npc['nombre']} <cantidad> <ítem>")
        await ctx.send(embed=embed)

    # ── comprar a NPC ────────────────────────────────────────────────────────
    # BUG CORREGIDO: la firma original era comprar_npc(ctx, npc_nombre, cantidad=1, *, item).
    # Esto hacía que `!comprar_npc Gausto Estofado Real` intentara parsear "Estofado"
    # como int para `cantidad` → BadArgument antes de que el comando pudiera ejecutarse.
    # Solución: recibir el resto como *args y detectar si el primer token es número.

    @commands.command(
        name="comprar_npc",
        aliases=["cnpc"],
        help=(
            "Comprá un ítem a un NPC.\n"
            "Ej: !comprar_npc Gausto Estofado Real\n"
            "Ej: !comprar_npc Gausto 3 Estofado Real"
        ),
    )
    async def comprar_npc(self, ctx, npc_nombre: str, *args):
        if not args:
            await ctx.send(
                "❌ Indicá qué querés comprar.\n"
                "Uso: `!comprar_npc <NPC> <ítem>` o `!comprar_npc <NPC> <cantidad> <ítem>`"
            )
            return

        try:
            cantidad = int(args[0])
            item = " ".join(args[1:])
        except ValueError:
            cantidad = 1
            item = " ".join(args)

        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        if not item:
            await ctx.send("❌ Indicá el nombre del ítem.")
            return

        exito, dialogo, npc = await comprar_a_npc(str(ctx.author.id), npc_nombre, item, cantidad)

        if npc is None:
            await ctx.send(f"❌ {dialogo}")
            return

        color  = discord.Color.green() if exito else discord.Color.orange()
        titulo = f"✅ Compra a {npc['nombre']}" if exito else f"💬 {npc['nombre']}"
        embed  = _embed_npc(npc, titulo=titulo, color=color)
        embed.add_field(name="💬", value=dialogo, inline=False)

        if exito:
            embed.add_field(name="📦 Recibiste", value=f"**{cantidad}×** {item.title()}", inline=True)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Npcs(bot))