from DB.db_connection import setup_db_connection
from properties.get_env_props import load_env_props
from DB.DB_Transactions import get_all_job_ids
from WebScraping.web_scraping import chrome_sign_in, linkedin_data_scraper
from logger.logger_config import setup_logging
if __name__ == "__main__":
    user, password, dsn = load_env_props()
    conn = setup_db_connection(user, password, dsn)
    job_ids_in_db = get_all_job_ids(conn)
    options = chrome_sign_in()
    linkedin_data_scraper(options, job_ids_in_db, user, password, dsn)