import discord
from discord.ext import commands
from services.inventario_service import (
    obtener_inventario, agregar_item, quitar_item, transferir_item
)


class Inventario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="inventario", help="Muestra tu inventario.")
    async def inventario(self, ctx, miembro: discord.Member = None):
        """!inventario [@usuario]"""
        objetivo = miembro or ctx.author
        items = await obtener_inventario(str(objetivo.id))

        embed = discord.Embed(
            title=f"🎒 Inventario de {objetivo.display_name}",
            color=discord.Color.blue()
        )
        if not items:
            embed.description = "*El inventario está vacío.*"
        else:
            embed.description = "\n".join(f"• **{row['item']}** x{row['cantidad']}" for row in items)

        await ctx.send(embed=embed)

    @commands.command(name="agregar_item", help="[ADMIN] Agrega un ítem al inventario de un jugador.")
    @commands.has_permissions(administrator=True)
    async def agregar_item_cmd(self, ctx, miembro: discord.Member, cantidad: int, *, item: str):
        """!agregar_item @usuario cantidad nombre del item"""
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        await agregar_item(str(miembro.id), item, cantidad)
        await ctx.send(f"✅ Se agregaron **{cantidad}x {item}** al inventario de {miembro.mention}.")

    @commands.command(name="quitar_item", help="[ADMIN] Quita un ítem del inventario de un jugador.")
    @commands.has_permissions(administrator=True)
    async def quitar_item_cmd(self, ctx, miembro: discord.Member, cantidad: int, *, item: str):
        """!quitar_item @usuario cantidad nombre del item"""
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return
        exito, mensaje = await quitar_item(str(miembro.id), item, cantidad)
        if exito:
            await ctx.send(f"✅ Se quitaron **{cantidad}x {item}** del inventario de {miembro.mention}.")
        else:
            await ctx.send(f"❌ {mensaje}")

    @commands.command(name="dar_item", help="Dale un ítem de tu inventario a otro jugador.")
    async def dar_item_cmd(self, ctx, miembro: discord.Member, cantidad: int, *, item: str):
        """!dar_item @usuario cantidad nombre del item"""
        emisor_id = str(ctx.author.id)
        receptor_id = str(miembro.id)

        if emisor_id == receptor_id:
            await ctx.send("❌ No podés darte ítems a vos mismo.")
            return
        if cantidad <= 0:
            await ctx.send("❌ La cantidad debe ser mayor a 0.")
            return

        exito, mensaje = await transferir_item(emisor_id, receptor_id, item, cantidad)
        if exito:
            embed = discord.Embed(
                title="📦 Ítem Transferido",
                description=f"{ctx.author.mention} le dio **{cantidad}x {item}** a {miembro.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {mensaje}")


async def setup(bot):
    await bot.add_cog(Inventario(bot))
