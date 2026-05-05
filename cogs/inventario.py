import discord
from discord.ext import commands
from services.inventario_service import (
    obtener_inventario, agregar_item, quitar_item, transferir_item,
    obtener_tienda, comprar_item_tienda
)
from services.economia_service import formato_monedas


class Inventario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── ver inventario ───────────────────────────────────────────────────────

    @commands.command(name="inventario", aliases=["inv"],
                      help="Muestra tu inventario (o el de otro jugador).")
    async def inventario(self, ctx, miembro: discord.Member = None):
        objetivo = miembro or ctx.author
        items = await obtener_inventario(str(objetivo.id))
        embed = discord.Embed(
            title=f"🎒 Inventario de {objetivo.display_name}",
            color=discord.Color.blue()
        )
        if not items:
            embed.description = "*Vacío como las arcas del reino.*"
        else:
            embed.description = "\n".join(
                f"• **{row['item']}** ×{row['cantidad']}" for row in items
            )
        await ctx.send(embed=embed)

    # ── dar ítem ─────────────────────────────────────────────────────────────

    @commands.command(name="dar_item",
                      help="Dale un ítem de tu inventario a otro jugador.")
    async def dar_item(self, ctx, miembro: discord.Member, cantidad: int, *, item: str):
        if miembro.id == ctx.author.id:
            await ctx.send("❌ No podés darte ítems a vos mismo.")
            return
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        exito, msg = await transferir_item(str(ctx.author.id), str(miembro.id), item, cantidad)
        if exito:
            embed = discord.Embed(
                title="📦 Ítem transferido",
                description=f"{ctx.author.mention} le dio **{cantidad}× {item.title()}** a {miembro.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {msg}")

    # ── tienda ───────────────────────────────────────────────────────────────

    @commands.command(name="tienda",
                      help="Muestra los ítems disponibles en la tienda.")
    async def tienda(self, ctx):
        productos = await obtener_tienda()
        embed = discord.Embed(title="🏪 Tienda", color=discord.Color.dark_gold())
        if not productos:
            embed.description = "*La tienda está vacía. Un admin puede agregar productos con `!tienda_agregar`.*"
        else:
            for p in productos:
                precio = formato_monedas(p["precio_oro"], p["precio_plata"], p["precio_cobre"])
                stock_txt = "∞" if p["stock"] == -1 else str(p["stock"])
                valor = f"Precio: {precio} | Stock: {stock_txt}"
                if p.get("descripcion"):
                    valor = f"*{p['descripcion']}*\n{valor}"
                embed.add_field(name=f"🔹 {p['nombre']}", value=valor, inline=False)
        embed.set_footer(text="Comprá con: !comprar <ítem>  o  !comprar <cantidad> <ítem>")
        await ctx.send(embed=embed)

    # ── comprar ───────────────────────────────────────────────────────────────
    # BUG CORREGIDO: la firma original era `comprar(ctx, cantidad: int = 1, *, item: str)`.
    # Esto hacía que `!comprar Poción de Curación` intentara parsear "Poción" como int
    # y lanzara BadArgument antes de que el comando pudiera ejecutarse.
    # Solución: recibir todo como *args y parsear la cantidad manualmente.

    @commands.command(
        name="comprar",
        help="Comprá un ítem de la tienda.\nEj: !comprar Poción de Curación\nEj: !comprar 3 Poción de Curación"
    )
    async def comprar(self, ctx, *args):
        if not args:
            await ctx.send(
                "❌ Indicá qué querés comprar.\n"
                "Uso: `!comprar <ítem>` o `!comprar <cantidad> <ítem>`"
            )
            return

        # Si el primer argumento es un número, es la cantidad
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
            await ctx.send("❌ Indicá el nombre del ítem después de la cantidad.")
            return

        exito, resultado = await comprar_item_tienda(str(ctx.author.id), item, cantidad)
        if exito:
            embed = discord.Embed(
                title="🛒 Compra exitosa",
                description=f"{ctx.author.mention} compró **{cantidad}× {resultado}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {resultado}")


async def setup(bot):
    await bot.add_cog(Inventario(bot))