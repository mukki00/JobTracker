import oracledb
from DB_props import DB_props


def setup_db_connection(user:str, password:str, dsn:str):
    db_props = DB_props(user, password, dsn)
    return oracledb.connect(
        user=db_props.user,
        password=db_props.password,
        dsn=db_props.dsn   # host/service, not SID
    )
