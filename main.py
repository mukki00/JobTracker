from db_connection import setup_db_connection
from get_env_props import load_env_props
from DB_Transactions import runDBTransactions
from WebScraping.web_scraping import chrome_sign_in

if __name__ == "__main__":
    user, password, dsn = load_env_props()
    conn = setup_db_connection(user, password, dsn)
    runDBTransactions(conn)
    chrome_sign_in()
    # scrape_jobs()



