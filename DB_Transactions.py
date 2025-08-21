from queries.SQL_QUERIES import get_all_companies_query

def runDBTransactions(conn):
    with conn.cursor() as cursor:
        cursor.execute(get_all_companies_query())
    conn.close()