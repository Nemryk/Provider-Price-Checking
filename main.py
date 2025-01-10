import dotenv
from processingYml import ProcessYML
from infracost_fetch import InfracostFetch
from pandas_setup import PandasDataFormatter
from result import Result
from setup_environment import setup_environment
import os
import logging

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    dotenv.load_dotenv()

    setup_environment()

    result = Result()

    logging.info("Loading data about services...")
    yml_processor = ProcessYML()
    if not yml_processor.data:
        logging.error("YAML processing failed. Exiting.")
        return

    logging.info("Loading data API Infracost...")
    github_token = os.getenv('GITHUB_TOKEN')
    infracost_api_key = os.getenv('INFRACOST_API_KEY')
    if not github_token:
        logging.error("Missing GITHUB_TOKEN. Please set GITHUB_TOKEN in .env.")
        return
    if not infracost_api_key:
        logging.error("Missing INFRACOST_API_KEY. Please set INFRACOST_API_KEY in .env.")
        return

    infracost_fetch = InfracostFetch(github_token)

    import asyncio
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))

    logging.info("Buliding DataFrames in Pandas...")
    pandas_formatter = PandasDataFormatter(infracost_fetch, yml_processor.data)
    if pandas_formatter.data.empty:
        logging.error("No data available after formatting. Exiting.")
        return

    result.get_result(pandas_formatter.data, yml_processor.data)

    logging.info("Autorzy: DP, DP, JK, RM")

if __name__ == "__main__":
    main()
