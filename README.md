# 🎲 Bot D&D — Guía de Comandos

## ⚙️ Instalación local

1. Instalá las dependencias:
   ```
   pip install -r requirements.txt
   ```

2. Copiá `.env.example` como `.env` y completá los valores:
   ```
   DISCORD_TOKEN=tu_token_aqui
   DATABASE_URL=postgresql://usuario:contraseña@host:puerto/nombre_db
   ```

3. Corré el bot:
   ```
   python main.py
   ```

---

## 🚀 Deploy en Railway (24/7 gratis)

1. Subir el proyecto a GitHub (sin el `.env`)
2. Entrar a [railway.app](https://railway.app) y crear un nuevo proyecto
3. Elegir **"Deploy from GitHub repo"** y seleccionar mi repositorio
4. Agregar una base de datos: **New → Database → PostgreSQL**
5. En mi servicio del bot, ir a **Variables** y agregar:
   - `DISCORD_TOKEN` → mi token de Discord
   - `DATABASE_URL` → Railway lo genera automáticamente desde la base de datos (copiarlo desde la tab de PostgreSQL → Connect)
6. ¡Listo! Railway despliega solo cada vez que se pushees a GitHub

---

## 💰 Economía

| Comando | Descripción |
|---|---|
| `!oro` | Muestra cuánto oro tenés |
| `!dar_oro @usuario cantidad` | Enviás oro a otro jugador |
| `!admin_dar_oro @usuario cantidad` | *(Admin)* Da oro a alguien |
| `!admin_quitar_oro @usuario cantidad` | *(Admin)* Quita oro a alguien |

---

## 🎒 Inventario

| Comando | Descripción |
|---|---|
| `!inventario` | Muestra tu inventario |
| `!inventario @usuario` | Muestra el inventario de otro |
| `!dar_item @usuario cantidad item` | Le pasás un ítem a alguien |
| `!agregar_item @usuario cantidad item` | *(Admin)* Agrega ítems |
| `!quitar_item @usuario cantidad item` | *(Admin)* Quita ítems |

---

## ⚔️ Personajes

| Comando | Descripción |
|---|---|
| `!crear_personaje` | Abre un formulario para crear tu personaje |
| `!actualizar_personaje` | Edita los datos de tu personaje |
| `!ficha <url>` | Guarda el link de tu ficha de Nivel20 |
| `!personaje` | Muestra tu personaje |
| `!personaje @usuario` | Muestra el personaje de otro |
| `!admin_set_nivel @usuario nivel` | *(Admin)* Cambia el nivel de alguien |
# BOT-D-D
