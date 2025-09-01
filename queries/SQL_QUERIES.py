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

def get_all_jobs_ids():
    return "SELECT JOB_ID FROM JOB_POST"

def insert_companies_query():
    return """
    INSERT INTO COMPANY (NAME, WEBSITE, COUNTRY, CITY, CREATED_AT)
    VALUES (:name, :website, :country, :city, SYSTIMESTAMP)
    """

def insert_job_post_query():
    return """
    INSERT INTO JOB_POST (
    job_id, job_title, company, company_location, job_link, job_type, linkedin_verified, JOB_CATEGORY
    ) VALUES (
    :job_id, :job_title, :company, :company_location, :job_link, :job_type, :linkedin_verified, :job_category)"""