from queries.SQL_QUERIES import get_all_companies_query, get_all_jobs_ids, insert_job_post_query

def runDBTransactions(conn):
    with conn.cursor() as cursor:
       cursor.execute(get_all_companies_query())
       for row in cursor:
           print(row)
    conn.close()

def get_all_job_ids(conn):
    job_ids = set()
    with conn.cursor() as cursor:
       cursor.execute(get_all_jobs_ids())
       for row in cursor:
           job_ids.add(row[0])
    conn.close()
    return job_ids

def insert_job_posts(conn, job_posts):
    with conn.cursor() as cursor:
        cursor.executemany(insert_job_post_query(), job_posts)
        conn.commit()
    conn.close()
