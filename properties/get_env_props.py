from dotenv import load_dotenv
import os
def load_env_props():
    load_dotenv()
    user = os.getenv("DB_USER_CLOUD")
    password = os.getenv("DB_PASSWORD")
    dsn = os.getenv("DB_DSN")
    wallet_dir = os.getenv("DB_WALLET_DIR")
    if not user or not password or not dsn:
        raise ValueError("Database connection properties are not set in the environment variables.")
    return user, password, dsn, wallet_dir

