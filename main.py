from DB.db_connection import setup_db_connection
from properties.get_env_props import load_env_props
from DB.DB_Transactions import runDBTransactions
from WebScraping.web_scraping import chrome_sign_in, linkedin_data_scraper

if __name__ == "__main__":
    user, password, dsn = load_env_props()
    conn = setup_db_connection(user, password, dsn)
    runDBTransactions(conn)
    options = chrome_sign_in()
    linkedin_data_scraper(options)
    # scrape_jobs()



