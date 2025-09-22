# python
import logging
import sys
import traceback
from DB.DB_Transactions import get_all_job_ids
from DB.db_connection import setup_db_connection, load_connection_properties
from WebScraping.web_scraping import chrome_sign_in, linkedin_data_scraper
from properties.get_env_props import load_env_props
try:
    user, password, dsn, wallet_dir, env = load_env_props()
    load_connection_properties(wallet_dir)
    conn = setup_db_connection(user=user, password=password, dsn=dsn)
    if env == "development":
        job_ids_in_db = get_all_job_ids(conn)
        options = chrome_sign_in()
        linkedin_data_scraper(options, job_ids_in_db, user, password, dsn)
except Exception as e:
    print("Error occurred:"+ str(e))
    logging.exception("Error occurred:"+ str(e))
    traceback.print_exc()
    sys.exit(1)