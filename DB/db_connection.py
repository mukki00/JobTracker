import oracledb
from pathlib import Path
import os

def load_connection_properties(wallet_dir:str):
    os.environ["TNS_ADMIN"] = wallet_dir
    check_sql_net(wallet_dir)
    try:
        oracledb.init_oracle_client(config_dir=wallet_dir)
        print("init_oracle_client OK")
    except Exception as e:
        print("init_oracle_client exception (continuing):", type(e).__name__, e)

def setup_db_connection(user:str, password:str, dsn:str):
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    return conn

def check_sql_net(wallet_dir:str):
    sqlnet = Path(wallet_dir) / "sqlnet.ora"
    if sqlnet.exists():
        txt = sqlnet.read_text(errors="ignore")
        for ln in txt.splitlines():
            if "WALLET" in ln.upper():
                print("sqlnet.ora:", ln)
            else:
                print(f"`{sqlnet}` not found")
