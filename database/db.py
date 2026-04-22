import asyncpg
import os

# Pool global de conexiones
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Devuelve el pool de conexiones. Lo crea si no existe."""
    global _pool
    if _pool is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("No se encontró DATABASE_URL en el archivo .env")
        _pool = await asyncpg.create_pool(database_url)
    return _pool


async def init_db():
    """Crea las tablas si no existen."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS jugadores (
                id TEXT PRIMARY KEY,
                oro INTEGER DEFAULT 100
            );

            CREATE TABLE IF NOT EXISTS inventario (
                id SERIAL PRIMARY KEY,
                jugador_id TEXT NOT NULL,
                item TEXT NOT NULL,
                cantidad INTEGER DEFAULT 1,
                FOREIGN KEY (jugador_id) REFERENCES jugadores(id)
            );

            CREATE TABLE IF NOT EXISTS personajes (
                id SERIAL PRIMARY KEY,
                jugador_id TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                nick TEXT,
                nivel INTEGER DEFAULT 1,
                clase TEXT,
                raza TEXT,
                link_ficha TEXT,
                FOREIGN KEY (jugador_id) REFERENCES jugadores(id)
            );
        """)
    print("✅ Base de datos inicializada")
