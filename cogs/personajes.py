import discord
from discord.ext import commands
from services.personaje_service import (
    obtener_personaje, crear_personaje, actualizar_personaje
)


class CrearPersonajeModal(discord.ui.Modal, title="Crear Personaje"):
    nombre = discord.ui.TextInput(label="Nombre del personaje", placeholder="Ej: Aragorn", max_length=50)
    nick = discord.ui.TextInput(label="Nick / Apodo", placeholder="Ej: El Montaraz", max_length=50, required=False)
    nivel = discord.ui.TextInput(label="Nivel (1-20)", placeholder="Ej: 5", max_length=3)
    clase = discord.ui.TextInput(label="Clase", placeholder="Ej: Guerrero, Mago, Pícaro...", max_length=50)
    raza = discord.ui.TextInput(label="Raza", placeholder="Ej: Humano, Elfo, Enano...", max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            nivel_int = int(self.nivel.value)
            if nivel_int < 1 or nivel_int > 20:
                await interaction.response.send_message("❌ El nivel debe ser entre 1 y 20.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ El nivel debe ser un número.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        exito, mensaje = await crear_personaje(
            user_id,
            nombre=self.nombre.value,
            nick=self.nick.value or None,
            nivel=nivel_int,
            clase=self.clase.value,
            raza=self.raza.value
        )

        if exito:
            embed = _embed_personaje(await obtener_personaje(user_id), interaction.user)
            await interaction.response.send_message("✅ ¡Personaje creado exitosamente!", embed=embed)
            await interaction.followup.send(
                "¿Tienes el link de tu ficha en Nivel20? Haz clic para agregarlo (opcional):",
                view=_BotonModal(LinkFichaModal(), label="🔗 Agregar link de ficha", style=discord.ButtonStyle.secondary),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(f"❌ {mensaje}", ephemeral=True)


class LinkFichaModal(discord.ui.Modal, title="Link de Ficha — Nivel20"):
    link = discord.ui.TextInput(
        label="Link de tu ficha en Nivel20",
        placeholder="https://nivel20.com/...",
        max_length=300,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        url = self.link.value.strip()

        if not (url.startswith("http://") or url.startswith("https://")):
            await interaction.response.send_message(
                "❌ El link no es válido. Debe empezar con `http://` o `https://`.", ephemeral=True
            )
            return

        exito, mensaje = await actualizar_personaje(user_id, link_ficha=url)
        if exito:
            embed = _embed_personaje(await obtener_personaje(user_id), interaction.user)
            await interaction.response.send_message("✅ Ficha vinculada.", embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {mensaje}", ephemeral=True)


class ActualizarPersonajeModal(discord.ui.Modal, title="Actualizar Personaje"):
    nombre = discord.ui.TextInput(label="Nombre del personaje", max_length=50, required=False)
    nick = discord.ui.TextInput(label="Nick / Apodo", max_length=50, required=False)
    nivel = discord.ui.TextInput(label="Nivel (1-20)", max_length=3, required=False)
    clase = discord.ui.TextInput(label="Clase", max_length=50, required=False)
    raza = discord.ui.TextInput(label="Raza", max_length=50, required=False)

    def __init__(self, personaje_actual: dict):
        super().__init__()
        self.nombre.default = personaje_actual.get("nombre", "")
        self.nick.default = personaje_actual.get("nick") or ""
        self.nivel.default = str(personaje_actual.get("nivel", 1))
        self.clase.default = personaje_actual.get("clase", "")
        self.raza.default = personaje_actual.get("raza", "")

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        campos = {}

        if self.nombre.value:
            campos["nombre"] = self.nombre.value
        if self.nick.value:
            campos["nick"] = self.nick.value
        if self.clase.value:
            campos["clase"] = self.clase.value
        if self.raza.value:
            campos["raza"] = self.raza.value
        if self.nivel.value:
            try:
                nivel_int = int(self.nivel.value)
                if nivel_int < 1 or nivel_int > 20:
                    await interaction.response.send_message("❌ El nivel debe ser entre 1 y 20.", ephemeral=True)
                    return
                campos["nivel"] = nivel_int
            except ValueError:
                await interaction.response.send_message("❌ El nivel debe ser un número.", ephemeral=True)
                return

        exito, mensaje = await actualizar_personaje(user_id, **campos)
        if exito:
            embed = _embed_personaje(await obtener_personaje(user_id), interaction.user)
            await interaction.response.send_message("✅ Personaje actualizado.", embed=embed)
        else:
            await interaction.response.send_message(f"❌ {mensaje}", ephemeral=True)


def _embed_personaje(personaje: dict, usuario: discord.User | discord.Member) -> discord.Embed:
    embed = discord.Embed(title=f"⚔️ {personaje['nombre']}", color=discord.Color.dark_gold())
    embed.set_author(name=usuario.display_name, icon_url=usuario.display_avatar.url)

    if personaje.get("nick"):
        embed.add_field(name="🏷️ Apodo", value=personaje["nick"], inline=False)
    embed.add_field(name="⚔️ Clase", value=personaje.get("clase") or "—", inline=False)
    embed.add_field(name="🌿 Raza", value=personaje.get("raza") or "—", inline=False)
    embed.add_field(name="⭐ Nivel", value=str(personaje.get("nivel", 1)), inline=False)
    if personaje.get("link_ficha"):
        embed.add_field(name="📄 Ficha", value=f"[Ver en Nivel20]({personaje['link_ficha']})", inline=False)

    return embed


class Personajes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="crear_personaje", help="Abre el formulario para crear tu personaje.")
    async def crear_personaje(self, ctx):
        user_id = str(ctx.author.id)
        if await obtener_personaje(user_id):
            await ctx.send("❌ Ya tienes un personaje creado. Usa `!actualizar_personaje` para editarlo.")
            return
        view = _BotonModal(CrearPersonajeModal(), label="📝 Abrir Formulario", style=discord.ButtonStyle.primary)
        await ctx.send("Haz clic para crear tu personaje:", view=view)

    @commands.command(name="actualizar_personaje", help="Edita los datos de tu personaje.")
    async def actualizar_personaje_cmd(self, ctx):
        user_id = str(ctx.author.id)
        personaje = await obtener_personaje(user_id)
        if not personaje:
            await ctx.send("❌ No tienes un personaje creado. Usá `!crear_personaje`.")
            return
        view = _BotonModal(ActualizarPersonajeModal(personaje), label="✏️ Editar Personaje", style=discord.ButtonStyle.secondary)
        await ctx.send("Hacé clic para editar tu personaje:", view=view)

    @commands.command(name="ficha", help="Agrega o actualiza el link de tu ficha en Nivel20.")
    async def ficha(self, ctx, link: str):
        user_id = str(ctx.author.id)
        if not await obtener_personaje(user_id):
            await ctx.send("❌ Primero crea tu personaje con `!crear_personaje`.")
            return
        if not (link.startswith("http://") or link.startswith("https://")):
            await ctx.send("❌ El link no es válido. Debe empezar con `http://` o `https://`.")
            return
        exito, mensaje = await actualizar_personaje(user_id, link_ficha=link)
        if exito:
            await ctx.send(f"✅ Ficha actualizada. [Ver personaje]({link})")
        else:
            await ctx.send(f"❌ {mensaje}")

    @commands.command(name="personaje", help="Muestra la ficha de un jugador.")
    async def ver_personaje(self, ctx, miembro: discord.Member = None):
        objetivo = miembro or ctx.author
        personaje = await obtener_personaje(str(objetivo.id))
        if not personaje:
            nombre = "usted" if objetivo == ctx.author else objetivo.display_name
            await ctx.send(f"❌ {nombre} no tiene ningún personaje creado.")
            return
        embed = _embed_personaje(personaje, objetivo)
        await ctx.send(embed=embed)

    @commands.command(name="admin_set_nivel", help="[ADMIN] Establece el nivel de un personaje.")
    @commands.has_permissions(administrator=True)
    async def admin_set_nivel(self, ctx, miembro: discord.Member, nivel: int):
        if nivel < 1 or nivel > 20:
            await ctx.send("❌ El nivel debe ser entre 1 y 20.")
            return
        user_id = str(miembro.id)
        if not await obtener_personaje(user_id):
            await ctx.send(f"❌ {miembro.mention} no tiene personaje creado.")
            return
        await actualizar_personaje(user_id, nivel=nivel)
        await ctx.send(f"✅ Nivel de {miembro.mention} actualizado a **{nivel}**.")


class _BotonModal(discord.ui.View):
    def __init__(self, modal: discord.ui.Modal, label: str, style: discord.ButtonStyle):
        super().__init__(timeout=60)
        self.modal = modal
        boton = discord.ui.Button(label=label, style=style)
        boton.callback = self._callback
        self.add_item(boton)

    async def _callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)


async def setup(bot):
    await bot.add_cog(Personajes(bot))
