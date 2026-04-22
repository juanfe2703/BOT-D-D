import discord
from discord.ext import commands
from services.economia_service import (
    obtener_oro, transferir_oro, dar_oro_admin, quitar_oro_admin
)


class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="oro", help="Muestra tu cantidad de oro actual.")
    async def oro(self, ctx):
        """!oro — Muestra cuánto oro tenés."""
        cantidad = await obtener_oro(str(ctx.author.id))
        embed = discord.Embed(
            title="💰 Tu Tesoro",
            description=f"{ctx.author.mention} tiene **{cantidad} monedas de oro** 🪙",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(name="dar_oro", help="Envía oro a otro jugador.")
    async def dar_oro(self, ctx, miembro: discord.Member, cantidad: int):
        """!dar_oro @usuario cantidad"""
        emisor_id = str(ctx.author.id)
        receptor_id = str(miembro.id)

        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        if emisor_id == receptor_id:
            await ctx.send("❌ No podés enviarte oro a vos mismo.")
            return

        exito, mensaje = await transferir_oro(emisor_id, receptor_id, cantidad)
        if exito:
            embed = discord.Embed(
                title="💸 Transferencia de Oro",
                description=f"{ctx.author.mention} le envió **{cantidad} 🪙** a {miembro.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {mensaje}")

    @commands.command(name="admin_dar_oro", help="[ADMIN] Da oro a un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_dar_oro(self, ctx, miembro: discord.Member, cantidad: int):
        """!admin_dar_oro @usuario cantidad"""
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        nuevo_total = await dar_oro_admin(str(miembro.id), cantidad)
        await ctx.send(f"✅ Se le dieron **{cantidad} 🪙** a {miembro.mention}. Total: **{nuevo_total} 🪙**")

    @commands.command(name="admin_quitar_oro", help="[ADMIN] Quita oro a un jugador.")
    @commands.has_permissions(administrator=True)
    async def admin_quitar_oro(self, ctx, miembro: discord.Member, cantidad: int):
        """!admin_quitar_oro @usuario cantidad"""
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        exito, total = await quitar_oro_admin(str(miembro.id), cantidad)
        if exito:
            await ctx.send(f"✅ Se quitaron **{cantidad} 🪙** a {miembro.mention}. Total: **{total} 🪙**")
        else:
            await ctx.send(f"❌ {miembro.mention} no tiene suficiente oro (tiene **{total} 🪙**).")


async def setup(bot):
    await bot.add_cog(Economia(bot))
