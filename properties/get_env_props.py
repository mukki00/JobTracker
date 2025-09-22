from dotenv import load_dotenv
from pathlib import Path
import os
def load_env_props():
    load_dotenv()
    user = os.getenv("DB_USER_CLOUD")
    password = os.getenv("DB_PASSWORD")
    dsn = os.getenv("DB_DSN")
    env = os.getenv("ENV")
    wallet_dir = str(Path(__file__).parent.parent / "Wallet_FREEPDB1")
    if not user or not password or not dsn:
        raise ValueError("Database connection properties are not set in the environment variables.")
    return user, password, dsn, wallet_dir, env

