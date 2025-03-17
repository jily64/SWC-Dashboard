import psycopg2
import uuid
class Adapter:

    def __init__(self, host, port, dbname, schema_name, user, password, sslmode=None, target_session_attrs=None):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.schema_name = schema_name
        self.user = user
        self.password = password
        self.sslmode = sslmode
        self.target_session_attrs = target_session_attrs
        self.conn = None
        self.cursor = None
        self.recreate = "--"

    def create_logs(self):
        try:
            query = f"""
                --DROP TABLE IF EXISTS public.logs;

                CREATE TABLE public.logs
                (
                    id SERIAL PRIMARY KEY,
                    log TEXT NOT NULL,
                    type TEXT NOT NULL,
                    time TIMESTAMP NOT NULL
                )
                TABLESPACE pg_default;

                ALTER TABLE IF EXISTS public.logs
                    OWNER to {self.user};
            """

            self.cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            print(f"Произошла ошибка при создании таблицы: {e}")
            self.conn.rollback()

    def create_logs(self):
        try:
            query = f"""
                --DROP TABLE IF EXISTS public.users;

                CREATE TABLE public.users
                (
                    id SERIAL PRIMARY KEY,
                    ds_id VARCHAR(255),
                    global_name VARCHAR(255),
                    username VARCHAR(255),
                    avatar_url VARCHAR(255)
                )
                TABLESPACE pg_default;

                ALTER TABLE IF EXISTS public.users
                    OWNER to {self.user};
            """

            self.cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            print(f"Произошла ошибка при создании таблицы: {e}")
            self.conn.rollback()


    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                sslmode=self.sslmode,
                target_session_attrs=self.target_session_attrs,
            )
            self.cursor = self.conn.cursor()
            self.create_logs()

        except Exception as error:
            print(f"Connection error: {error}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def select(self, table, where_clause=None, params=None):
        query = f"SELECT * FROM \"{self.schema_name}\".\"{table}\""
        if where_clause:
            query += f" WHERE {where_clause}"
        self.cursor.execute(query, params)
        #print(query)
        return self.cursor.fetchall()

    def largest_id(self, tabel):
        query = f"""SELECT id FROM {self.schema_name}.{tabel} ORDER BY id DESC LIMIT 1"""
        self.cursor.execute(query, None)
        return self.cursor.fetchall()

    def insert(self, table: str, data: dict, session_uuid:str = None):
        columns = ", ".join(f'"{col}"' for col in data.keys())
        placeholders = ", ".join("%s" for _ in data.values())

        session_request = ["", ""]
        if session_uuid != None:
            session_request = [", session_id", f", '{session_uuid}'"]

        query = f"""INSERT INTO \"{self.schema_name}\".\"{table}\" ({columns}) VALUES ({placeholders})"""
        #print(query)
        self.cursor.execute(query, tuple(data.values()))
        self.conn.commit()
        return id

    def update(self, table, updates, where_clause, params=None):
        set_clause = ", ".join(f'"{col}" = %s' for col in updates.keys())
        query = f"UPDATE \"{self.schema_name}\".\"{table}\" SET {set_clause} WHERE {where_clause}"
        self.cursor.execute(query, tuple(updates.values()))
        self.conn.commit()

    def delete(self, table, where_clause, params=None):
        query = f"DELETE FROM \"{self.schema_name}\".\"{table}\" WHERE {where_clause}"
        self.cursor.execute(query, params)
        self.conn.commit()

    def delete_all(self, table):
        query = f"DELETE FROM \"{self.schema_name}\".\"{table}\""
        self.cursor.execute(query)
        self.conn.commit()