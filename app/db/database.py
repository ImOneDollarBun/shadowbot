import aiosqlite as aiosql
from app.commands import generate_ssr, generate_password


class SQLBase:
    def __init__(self, url):
        self.url = url

    async def create_db(self):
        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    port INTEGER,
                    password TEXT,
                    ssr TEXT,
                    mark TEXT,
                    flag TEXT
                )
            ''')

    async def update_port_mark(self, port, mark):
        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            await cursor.execute("UPDATE users SET mark = ? WHERE port = ?", (mark, port,))
            await conn.commit()

    async def find_mark_by_port(self, port):
        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            res = await cursor.execute("SELECT mark FROM users WHERE port = ?", (port,))
            row = await res.fetchone()
            return row[0] if row else None

    async def update_flag_by_port(self, port, flag):
        async with aiosql.connect(self.url) as conn:
            try:
                cursor = await conn.cursor()
                await cursor.execute("UPDATE users SET flag = ? WHERE port = ?", (flag, port,))
            except Exception as e:
                return e

    async def get_user_ports(self):
        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT port FROM users")
            return [row[0] for row in await cursor.fetchall()]

    async def get_ssr(self, port):
        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            res = await cursor.execute("SELECT ssr FROM users WHERE port = ?", (port,))
            res = await res.fetchone()
            return res[0]

    async def add_user(self, port):
        password = generate_password()
        ssr = generate_ssr(port, password)

        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            await cursor.execute("INSERT INTO users (port, password, ssr) VALUES (?, ?, ?)",
                                 (port, password, ssr))
            await conn.commit()
        return password

    async def remove_user(self, port):
        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM users WHERE port = ?", (port,))
            await conn.commit()

    async def list_users(self):
        async with aiosql.connect(self.url) as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM users")
            return await cursor.fetchall()
