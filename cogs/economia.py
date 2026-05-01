import discord
from discord.ext import commands
from services.economia_service import (
    obtener_monedas, transferir_monedas,
    obtener_historial, obtener_leaderboard,
    formato_monedas, desde_cobre
)


def _parsear_monedas(args: tuple) -> tuple[int, int, int] | None:
    """
    Interpreta argumentos de monedas desde la línea de comandos.
    Formatos aceptados:
      !dar 5o 3p 10c         → 5 oro, 3 plata, 10 cobre
      !dar 5o                → solo oro
      !dar 200c              → solo cobre
    Devuelve (cobre, plata, oro) o None si el formato es inválido.
    """
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


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── ver monedas ──────────────────────────────────────────────────────────

    @commands.command(name="monedas", aliases=["oro", "dinero"],
                      help="Muestra tus monedas actuales.")
    async def monedas(self, ctx, miembro: discord.Member = None):
        objetivo = miembro or ctx.author
        datos = await obtener_monedas(str(objetivo.id))
        embed = discord.Embed(
            title=f"💰 Tesoro de {objetivo.display_name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="🥇 Oro",   value=str(datos["oro"]),   inline=True)
        embed.add_field(name="🥈 Plata", value=str(datos["plata"]), inline=True)
        embed.add_field(name="🟤 Cobre", value=str(datos["cobre"]), inline=True)
        total_c = datos["oro"] * 10_000 + datos["plata"] * 100 + datos["cobre"]
        embed.set_footer(text=f"Total equivalente: {total_c:,} cobres")
        await ctx.send(embed=embed)

    # ── dar monedas ──────────────────────────────────────────────────────────

    @commands.command(name="dar",
                      help="Envía monedas a otro jugador. Ej: !dar @usuario 5o 3p 10c")
    async def dar(self, ctx, miembro: discord.Member, *args):
        if not args:
            await ctx.send("❌ Debes indicar cuánto enviar. Ej: `!dar @usuario 5o 3p 10c`")
            return
        resultado = _parsear_monedas(args)
        if resultado is None:
            await ctx.send("❌ Formato inválido. Usá `5o`, `3p`, `10c` para oro/plata/cobre.")
            return
        cobre, plata, oro = resultado

        if miembro.id == ctx.author.id:
            await ctx.send("❌ No podés enviarte monedas a vos mismo.")
            return

        exito, msg = await transferir_monedas(str(ctx.author.id), str(miembro.id), cobre, plata, oro)
        if exito:
            embed = discord.Embed(
                title="💸 Transferencia",
                description=f"{ctx.author.mention} le envió {formato_monedas(oro, plata, cobre)} a {miembro.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {msg}")

    # ── historial ─────────────────────────────────────────────────────────────

    @commands.command(name="historial",
                      help="Muestra tus últimas transacciones.")
    async def historial(self, ctx):
        registros = await obtener_historial(str(ctx.author.id), limite=8)
        if not registros:
            await ctx.send("📭 No tenés transacciones registradas todavía.")
            return
        embed = discord.Embed(title="📜 Historial de transacciones", color=discord.Color.blurple())
        tipos_emoji = {
            "transferencia": "💸", "admin_dar": "➕",
            "admin_quitar": "➖", "compra": "🛒", "venta": "💰"
        }
        for r in registros:
            emoji = tipos_emoji.get(r["tipo"], "📌")
            monto = formato_monedas(r["oro"], r["plata"], r["cobre"])
            fecha = r["creado_en"].strftime("%d/%m %H:%M")
            embed.add_field(
                name=f"{emoji} {r['tipo'].upper()} — {fecha}",
                value=r["detalle"] or monto,
                inline=False
            )
        await ctx.send(embed=embed)

    # ── ranking ───────────────────────────────────────────────────────────────

    @commands.command(name="ranking", aliases=["leaderboard", "top"],
                      help="Muestra los jugadores más ricos.")
    async def ranking(self, ctx):
        tabla = await obtener_leaderboard(limite=10)
        embed = discord.Embed(title="🏆 Ranking de riqueza", color=discord.Color.gold())
        medallas = ["🥇", "🥈", "🥉"]
        lineas = []
        for i, row in enumerate(tabla):
            try:
                miembro = ctx.guild.get_member(int(row["id"])) or await ctx.guild.fetch_member(int(row["id"]))
                nombre = miembro.display_name
            except Exception:
                nombre = f"Jugador {row['id'][:6]}"
            medalla = medallas[i] if i < 3 else f"`#{i+1}`"
            monto = formato_monedas(row["oro"], row["plata"], row["cobre"])
            lineas.append(f"{medalla} **{nombre}** — {monto}")
        embed.description = "\n".join(lineas) if lineas else "*Nadie tiene monedas todavía.*"
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economia(bot))
