from sqlalchemy import create_engine, text
from config import Config

try:
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT DATABASE()"))
        database = result.scalar()

        print("✅ MySQL connection successful!")
        print("Connected database:", database)

except Exception as e:
    print("❌ MySQL connection failed!")
    print("Error:", e)