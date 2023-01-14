import dotenv
from processingYml import process_yml
import infracost_fetch
from pandas_setup import Pandas_data_formatter
from result import Result
from setup_environment import setupEnvironment
import os

dotenv.load_dotenv()
setupEnvironment()
result = Result()
print("Ładowanie danych o usługach...")
YMLProvider = process_yml()
print("Ładowanie danych z API infracost...")
secrets = [os.environ['github'], os.environ['INFRACOST_API_KEY']]
infracost_data = infracost_fetch.Infracost_Fetch(secrets)
print("Budowanie dataframes w Pandas...")
pandas_dataframe = Pandas_data_formatter(infracost_data, YMLProvider.data)
result.get_result(pandas_dataframe.data, YMLProvider.data)
print("Autorzy: DP,DP,JK")
