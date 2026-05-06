import discord
from discord.ext import commands
from services.personaje_service import (
    obtener_personaje_activo, obtener_personaje_por_nombre,
    listar_personajes, crear_personaje, actualizar_personaje,
    cambiar_personaje_activo, modificar_hp, modificar_hp_temporal,
    agregar_condicion, quitar_condicion, obtener_condiciones
)


# ─── helpers ────────────────────────────────────────────────────────────────

def _barra_hp(actual: int, maximo: int, temporal: int = 0, largo: int = 10) -> str:
    if maximo <= 0:
        return "*(sin HP configurado)*"
    llenos = round(actual / maximo * largo)
    barra = "█" * llenos + "░" * (largo - llenos) + f"  {actual}/{maximo}"
    if temporal > 0:
        barra += f" (+{temporal} temp)"
    return barra


def _barra_mana(actual: int, maximo: int, largo: int = 10) -> str:
    if maximo <= 0:
        return None
    llenos = round(actual / maximo * largo)
    return "🔹" * llenos + "▪" * (largo - llenos) + f"  {actual}/{maximo}"


async def _embed_personaje(personaje: dict, usuario: discord.User | discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title=f"⚔️ {personaje['nombre']}",
        color=discord.Color.dark_gold()
    )
    embed.set_author(name=usuario.display_name, icon_url=usuario.display_avatar.url)
    if personaje.get("nick"):
        embed.add_field(name="🏷️ Apodo",  value=personaje["nick"], inline=False)
    embed.add_field(name="⚔️ Clase",  value=personaje.get("clase") or "—", inline=True)
    embed.add_field(name="🌿 Raza",   value=personaje.get("raza")  or "—", inline=True)
    embed.add_field(name="⭐ Nivel",  value=str(personaje.get("nivel", 1)), inline=True)

    hp_max  = personaje.get("hp_max", 0)
    hp_act  = personaje.get("hp_actual", 0)
    hp_temp = personaje.get("hp_temporal", 0) or 0
    embed.add_field(name="❤️ HP", value=_barra_hp(hp_act, hp_max, hp_temp), inline=False)

    mana_max = personaje.get("mana_max", 0) or 0
    mana_act = personaje.get("mana_actual", 0) or 0
    barra_mana = _barra_mana(mana_act, mana_max)
    if barra_mana:
        embed.add_field(name="💙 Maná", value=barra_mana, inline=False)

    xp = personaje.get("xp", 0)
    if xp:
        embed.add_field(name="✨ XP", value=str(xp), inline=True)

    # Condiciones activas
    condiciones = await obtener_condiciones(personaje["id"])
    if condiciones:
        embed.add_field(
            name="⚠️ Condiciones",
            value=" · ".join(f"`{c}`" for c in condiciones),
            inline=False
        )

    if personaje.get("link_ficha"):
        embed.add_field(name="📄 Ficha", value=f"[Ver en Nivel20]({personaje['link_ficha']})", inline=False)

    activo_txt = "✅ Activo" if personaje.get("activo") else "💤 Inactivo"
    embed.set_footer(text=activo_txt)
    return embed


# ─── modals ─────────────────────────────────────────────────────────────────

class CrearPersonajeModal(discord.ui.Modal, title="Crear Personaje"):
    nombre = discord.ui.TextInput(label="Nombre", placeholder="Ej: Aragorn", max_length=50)
    nick   = discord.ui.TextInput(label="Apodo (opcional)", max_length=50, required=False)
    nivel  = discord.ui.TextInput(label="Nivel (1–20)", placeholder="5", max_length=2)
    clase  = discord.ui.TextInput(label="Clase", placeholder="Guerrero, Mago, Pícaro…", max_length=50)
    raza   = discord.ui.TextInput(label="Raza", placeholder="Humano, Elfo, Enano…", max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            nivel_int = int(self.nivel.value)
            if not 1 <= nivel_int <= 20:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ El nivel debe ser un número entre 1 y 20.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        exito, msg = await crear_personaje(
            user_id,
            nombre=self.nombre.value,
            nick=self.nick.value or None,
            nivel=nivel_int,
            clase=self.clase.value,
            raza=self.raza.value
        )
        if exito:
            personaje = await obtener_personaje_activo(user_id)
            embed = await _embed_personaje(personaje, interaction.user)
            # Pedir HP y ficha en un segundo paso
            view = _BotonModal(
                ConfigurarHPModal(personaje["id"]),
                "⚙️ Configurar HP y ficha",
                discord.ButtonStyle.secondary
            )
            await interaction.response.send_message(
                "✅ ¡Personaje creado! Configurá tu HP y ficha (opcional):",
                embed=embed,
                view=view
            )
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)


class ConfigurarHPModal(discord.ui.Modal, title="Configurar HP y Ficha"):
    hp_max   = discord.ui.TextInput(label="HP Máximo", placeholder="Ej: 30", max_length=5)
    mana_max = discord.ui.TextInput(label="Maná Máximo (opcional)", placeholder="Ej: 20", max_length=5, required=False)
    link     = discord.ui.TextInput(
        label="Link de ficha Nivel20 (opcional)",
        placeholder="https://nivel20.com/...",
        max_length=300,
        required=False
    )

    def __init__(self, personaje_id: int | None = None):
        super().__init__()
        self.personaje_id = personaje_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            hp = int(self.hp_max.value)
            if hp <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ El HP debe ser un número mayor a 0.", ephemeral=True)
            return

        mana = 0
        if self.mana_max.value:
            try:
                mana = int(self.mana_max.value)
            except ValueError:
                await interaction.response.send_message("❌ El maná debe ser un número.", ephemeral=True)
                return

        link = self.link.value.strip() or None
        if link and not link.startswith(("http://", "https://")):
            await interaction.response.send_message("❌ El link debe empezar con `https://`.", ephemeral=True)
            return

        campos = {"hp_max": hp, "hp_actual": hp, "mana_max": mana, "mana_actual": mana}
        if link:
            campos["link_ficha"] = link

        await actualizar_personaje(str(interaction.user.id), **campos)
        personaje = await obtener_personaje_activo(str(interaction.user.id))
        embed = await _embed_personaje(personaje, interaction.user)
        await interaction.response.send_message("✅ ¡Configuración guardada!", embed=embed)


class ActualizarPersonajeModal(discord.ui.Modal, title="Actualizar Personaje"):
    nombre = discord.ui.TextInput(label="Nombre", max_length=50,  required=False)
    nick   = discord.ui.TextInput(label="Apodo",  max_length=50,  required=False)
    nivel  = discord.ui.TextInput(label="Nivel (1–20)", max_length=2, required=False)
    clase  = discord.ui.TextInput(label="Clase",  max_length=50,  required=False)
    raza   = discord.ui.TextInput(label="Raza",   max_length=50,  required=False)

    def __init__(self, personaje: dict):
        super().__init__()
        self.nombre.default = personaje.get("nombre", "")
        self.nick.default   = personaje.get("nick") or ""
        self.nivel.default  = str(personaje.get("nivel", 1))
        self.clase.default  = personaje.get("clase", "")
        self.raza.default   = personaje.get("raza", "")

    async def on_submit(self, interaction: discord.Interaction):
        campos = {}
        if self.nombre.value: campos["nombre"] = self.nombre.value
        if self.nick.value:   campos["nick"]   = self.nick.value
        if self.clase.value:  campos["clase"]  = self.clase.value
        if self.raza.value:   campos["raza"]   = self.raza.value
        if self.nivel.value:
            try:
                n = int(self.nivel.value)
                if not 1 <= n <= 20:
                    raise ValueError
                campos["nivel"] = n
            except ValueError:
                await interaction.response.send_message("❌ Nivel inválido.", ephemeral=True)
                return

        exito, msg = await actualizar_personaje(str(interaction.user.id), **campos)
        if exito:
            personaje = await obtener_personaje_activo(str(interaction.user.id))
            embed = await _embed_personaje(personaje, interaction.user)
            view = _BotonModal(
                ConfigurarHPModal(),
                "⚙️ Actualizar HP y ficha",
                discord.ButtonStyle.secondary
            )
            await interaction.response.send_message(
                "✅ Personaje actualizado. ¿Querés actualizar HP, maná o ficha también?",
                embed=embed,
                view=view
            )
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)


class _BotonModal(discord.ui.View):
    def __init__(self, modal, label: str, style: discord.ButtonStyle):
        super().__init__(timeout=60)
        self.modal = modal
        boton = discord.ui.Button(label=label, style=style)
        boton.callback = self._cb
        self.add_item(boton)

    async def _cb(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal)


# ─── cog ────────────────────────────────────────────────────────────────────

class Personajes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="crear_personaje",
                      help="Abre el formulario para crear un nuevo personaje.")
    async def crear_personaje_cmd(self, ctx):
        # Los modales solo se pueden abrir desde una interacción (botón/slash).
        # Enviamos un mensaje con un botón que abre el modal inmediatamente.
        view = _BotonModal(CrearPersonajeModal(), "📝 Crear personaje", discord.ButtonStyle.primary)
        await ctx.send(
            f"{ctx.author.mention} Hacé clic para abrir el formulario de creación:",
            view=view,
            delete_after=120  # se auto-elimina después de 2 min
        )

    @commands.command(name="actualizar_personaje",
                      help="Edita los datos de tu personaje activo.")
    async def actualizar_personaje_cmd(self, ctx):
        personaje = await obtener_personaje_activo(str(ctx.author.id))
        if not personaje:
            await ctx.send("❌ No tienes un personaje activo. Usá `!crear_personaje`.")
            return
        view = _BotonModal(ActualizarPersonajeModal(personaje), "✏️ Editar", discord.ButtonStyle.secondary)
        await ctx.send("Haz clic para editar tu personaje:", view=view)

    @commands.command(name="personaje", aliases=["ficha_p"],
                      help="Muestra tu personaje activo (o el de otro jugador).")
    async def ver_personaje(self, ctx, miembro: discord.Member = None):
        objetivo = miembro or ctx.author
        personaje = await obtener_personaje_activo(str(objetivo.id))
        if not personaje:
            await ctx.send(f"❌ {objetivo.display_name} no tiene personaje activo.")
            return
        embed = await _embed_personaje(personaje, objetivo)
        await ctx.send(embed=embed)

    @commands.command(name="mis_personajes",
                      help="Lista todos tus personajes.")
    async def mis_personajes(self, ctx):
        lista = await listar_personajes(str(ctx.author.id))
        if not lista:
            await ctx.send("❌ No tienes personajes. Usá `!crear_personaje`.")
            return
        embed = discord.Embed(title="📋 Tus personajes", color=discord.Color.blurple())
        for p in lista:
            estado = "✅ Activo" if p["activo"] else "💤"
            embed.add_field(
                name=f"{estado} {p['nombre']}",
                value=f"Nv.{p['nivel']} {p.get('clase','?')} · {p.get('raza','?')}",
                inline=False
            )
        embed.set_footer(text="Cambia con: !jugar_como <nombre>")
        await ctx.send(embed=embed)

    @commands.command(name="jugar_como",
                      help="Cambia tu personaje activo. Ej: !jugar_como Thorin")
    async def jugar_como(self, ctx, *, nombre: str):
        exito, msg = await cambiar_personaje_activo(str(ctx.author.id), nombre)
        if exito:
            personaje = await obtener_personaje_activo(str(ctx.author.id))
            embed = await _embed_personaje(personaje, ctx.author)
            await ctx.send(f"✅ {msg}", embed=embed)
        else:
            await ctx.send(f"❌ {msg}")

    @commands.command(name="ficha",
                      help="Guarda el link de tu ficha en Nivel20.")
    async def ficha(self, ctx, link: str):
        if not link.startswith(("http://", "https://")):
            await ctx.send("❌ El link debe empezar con `https://`.")
            return
        exito, msg = await actualizar_personaje(str(ctx.author.id), link_ficha=link)
        if exito:
            await ctx.send(f"✅ Ficha vinculada.")
        else:
            await ctx.send(f"❌ {msg}")

    # ── HP ────────────────────────────────────────────────────────────────────

    @commands.command(name="hp",
                      help="Modifica tus HP. Ej: !hp -5  o  !hp +10")
    async def hp_cmd(self, ctx, valor: str):
        try:
            delta = int(valor)
        except ValueError:
            await ctx.send("❌ Usá `!hp +10` para curar o `!hp -5` para recibir daño.")
            return
        exito, personaje = await modificar_hp(str(ctx.author.id), delta)
        if not exito:
            await ctx.send("❌ No tienes personaje activo.")
            return
        hp_temp = personaje.get("hp_temporal", 0) or 0
        barra   = _barra_hp(personaje["hp_actual"], personaje["hp_max"], hp_temp)
        signo   = "+" if delta > 0 else ""
        color   = discord.Color.green() if delta > 0 else discord.Color.red()
        embed   = discord.Embed(
            title=f"❤️ HP de {personaje['nombre']}",
            description=f"`{barra}`\n*Cambio: {signo}{delta}*",
            color=color
        )
        if personaje["hp_actual"] == 0:
            embed.add_field(name="💀", value="¡El personaje está a 0 HP!", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="hp_temp",
                      help="Agrega HP temporales a tu personaje. Ej: !hp_temp 8")
    async def hp_temp_cmd(self, ctx, valor: int):
        if valor <= 0:
            await ctx.send("❌ El valor debe ser mayor a 0.")
            return
        exito, personaje = await modificar_hp_temporal(str(ctx.author.id), valor)
        if not exito:
            await ctx.send("❌ No tienes personaje activo.")
            return
        hp_temp = personaje.get("hp_temporal", 0) or 0
        barra   = _barra_hp(personaje["hp_actual"], personaje["hp_max"], hp_temp)
        embed   = discord.Embed(
            title=f"🛡️ HP temporales — {personaje['nombre']}",
            description=f"`{barra}`\n*+{valor} HP temporales otorgados*",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Los HP temporales absorben daño primero. No se curan con !hp.")
        await ctx.send(embed=embed)

    @commands.command(name="mana",
                      help="Modifica tu maná. Ej: !mana -3  o  !mana +5")
    async def mana_cmd(self, ctx, valor: str):
        try:
            delta = int(valor)
        except ValueError:
            await ctx.send("❌ Usá `!mana +5` para recuperar o `!mana -3` para gastar.")
            return
        personaje = await obtener_personaje_activo(str(ctx.author.id))
        if not personaje:
            await ctx.send("❌ No tienes personaje activo.")
            return
        mana_max = personaje.get("mana_max", 0) or 0
        if mana_max == 0:
            await ctx.send("❌ Tu personaje no tiene maná configurado. Pedile a un admin `!admin_set_hp`.")
            return
        mana_act   = personaje.get("mana_actual", 0) or 0
        nuevo_mana = max(0, min(mana_max, mana_act + delta))
        exito, msg = await actualizar_personaje(str(ctx.author.id), mana_actual=nuevo_mana)
        barra  = _barra_mana(nuevo_mana, mana_max)
        signo  = "+" if delta > 0 else ""
        color  = discord.Color.blue() if delta > 0 else discord.Color.dark_blue()
        embed  = discord.Embed(
            title=f"💙 Maná de {personaje['nombre']}",
            description=f"`{barra}`\n*Cambio: {signo}{delta}*",
            color=color
        )
        if nuevo_mana == 0:
            embed.add_field(name="🔵", value="¡Sin maná!", inline=False)
        await ctx.send(embed=embed)

    # ── condiciones ───────────────────────────────────────────────────────────

    @commands.command(name="condicion",
                      help="Agrega una condición a tu personaje. Ej: !condicion envenenado")
    async def condicion_add(self, ctx, *, condicion: str):
        exito, msg = await agregar_condicion(str(ctx.author.id), condicion)
        if exito:
            await ctx.send(f"⚠️ Condición **{msg}** agregada a tu personaje.")
        else:
            await ctx.send(f"❌ {msg}")

    @commands.command(name="quitar_condicion",
                      help="Quita una condición de tu personaje.")
    async def condicion_remove(self, ctx, *, condicion: str):
        exito, msg = await quitar_condicion(str(ctx.author.id), condicion)
        if exito:
            await ctx.send(f"✅ Condición **{msg}** eliminada.")
        else:
            await ctx.send(f"❌ {msg}")


async def setup(bot):
    await bot.add_cog(Personajes(bot))
