"""
Tiradas de dados. Soporta notación XdY+Z estándar de D&D.
Ejemplos: 1d20, 2d6+3, 4d4-1, d20 (=1d20)
"""
import discord
from discord.ext import commands
import random
import re


_PATRON = re.compile(
    r"^(?P<num>\d+)?d(?P<caras>\d+)(?P<mod>[+-]\d+)?$",
    re.IGNORECASE
)


def _tirar(expresion: str) -> tuple[list[int], int, str] | None:
    """
    Parsea y ejecuta una expresión de dados.
    Devuelve (resultados_individuales, total, expresion_normalizada) o None.
    """
    m = _PATRON.match(expresion.strip())
    if not m:
        return None
    num   = int(m.group("num") or 1)
    caras = int(m.group("caras"))
    mod   = int(m.group("mod") or 0)

    if num < 1 or num > 100 or caras < 2 or caras > 1000:
        return None

    resultados = [random.randint(1, caras) for _ in range(num)]
    total      = sum(resultados) + mod

    expr_norm = f"{num}d{caras}"
    if mod > 0:  expr_norm += f"+{mod}"
    elif mod < 0: expr_norm += str(mod)

    return resultados, total, expr_norm


class Dados(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tirar", aliases=["roll", "dado", "r"],
                      help="Tira dados. Ej: !tirar 1d20  !tirar 2d6+3  !tirar d20 d20 d20")
    async def tirar(self, ctx, *expresiones: str):
        if not expresiones:
            expresiones = ("1d20",)

        # Máximo 5 expresiones por tirada
        expresiones = expresiones[:5]

        embed = discord.Embed(title="🎲 Tirada de dados", color=discord.Color.blurple())
        grand_total = 0

        for expr in expresiones:
            resultado = _tirar(expr)
            if resultado is None:
                await ctx.send(
                    f"❌ Expresión inválida: `{expr}`\n"
                    "Usá formato `XdY` o `XdY+Z`. Ejemplos: `1d20`, `2d6+3`, `d4`."
                )
                return

            individuales, total, expr_norm = resultado
            grand_total += total

            # Marcar críticos y pifias en d20
            caras = int(re.search(r"d(\d+)", expr_norm).group(1))
            detalle = []
            for r in individuales:
                if caras == 20 and r == 20: detalle.append(f"**[{r}]✨**")
                elif caras == 20 and r == 1: detalle.append(f"**[{r}]💀**")
                else: detalle.append(str(r))

            mod_str = ""
            m = re.search(r"([+-]\d+)$", expr_norm)
            if m:
                mod_str = f" {m.group(1)}"

            valor = f"[{', '.join(detalle)}]{mod_str} = **{total}**"
            embed.add_field(name=f"`{expr_norm}`", value=valor, inline=False)

        if len(expresiones) > 1:
            embed.set_footer(text=f"Total combinado: {grand_total}")

        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="ventaja",
                      help="Tira con ventaja (2d20, toma el mayor). Ej: !ventaja +3")
    async def ventaja(self, ctx, mod: str = ""):
        a, b = random.randint(1, 20), random.randint(1, 20)
        mayor = max(a, b)
        mod_val = 0
        if mod:
            try:
                mod_val = int(mod)
            except ValueError:
                pass
        total = mayor + mod_val
        mod_str = f" {mod_val:+}" if mod_val else ""
        embed = discord.Embed(
            title="🎲 Tirada con ventaja",
            description=f"[{a}, {b}] → **{mayor}**{mod_str} = **{total}**",
            color=discord.Color.green()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="desventaja",
                      help="Tira con desventaja (2d20, toma el menor).")
    async def desventaja(self, ctx, mod: str = ""):
        a, b = random.randint(1, 20), random.randint(1, 20)
        menor = min(a, b)
        mod_val = 0
        if mod:
            try:
                mod_val = int(mod)
            except ValueError:
                pass
        total = menor + mod_val
        mod_str = f" {mod_val:+}" if mod_val else ""
        embed = discord.Embed(
            title="🎲 Tirada con desventaja",
            description=f"[{a}, {b}] → **{menor}**{mod_str} = **{total}**",
            color=discord.Color.red()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Dados(bot))
