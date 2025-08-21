def get_company_info_query():
    return """
    SELECT id, name, website, country, city,
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at
    FROM company
    WHERE id = :id
    """

def get_all_companies_query():
    return """
    SELECT id, name, website, country, city,
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at
    FROM company order by id asc
    """

def insert_companies_query():
    return """
    INSERT INTO COMPANY (NAME, WEBSITE, COUNTRY, CITY, CREATED_AT)
    VALUES ('XpressJobs', 'https://xpress.jobs', 'SRI LANKA', 'COLOMBO', SYSDATE)
    """