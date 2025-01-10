import pandas as pd
import logging
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PandasDataFormatter:
    def __init__(self, infracost_data, processed_yml):
        self.yml = processed_yml
        self.aws_dataframe = self.generate_dataframe("aws", infracost_data.aws_data)
        self.azure_dataframe = self.generate_dataframe("azure", infracost_data.azure_data)
        self.gcp_dataframe = self.generate_dataframe("gcp", infracost_data.gcp_data)
        self.aggregate_counts()

    def generate_dataframe(self, provider, cloud_data):
        if not cloud_data:
            logger.warning(f"No data to generate DataFrame for provider: {provider}")
            return pd.DataFrame()
        
        df = pd.json_normalize(cloud_data)
        
        if 'service' not in df.columns:
            logger.error(f"'service' column missing in DataFrame for provider: {provider}")
            return pd.DataFrame()

        logger.info(f"DataFrame for provider {provider} before processing:\n{df.head()}")

        final_category = []
        predictions = {}
        for service in df['service'].tolist():
            service_name = service
            if service_name not in predictions:
                texts = []
                categories = []
                for category in self.yml:
                    for platform in self.yml[category]:
                        texts.append(" ".join(self.yml[category][platform]))
                        categories.append(category)
                text_clf = Pipeline([
                    ('union',
                     FeatureUnion(
                         transformer_list=[
                             ('cv_word', CountVectorizer()),
                             ('cv_char', CountVectorizer(analyzer="char"))
                         ],
                         transformer_weights={
                             'cv_word': 1,
                             'cv_char': 0
                         },
                     )),
                    ('clf', MultinomialNB())
                ])
                try:
                    text_clf.fit(texts, categories)
                except Exception as e:
                    logger.error(f"Error training classifier for provider {provider}: {e}")
                    return pd.DataFrame()
                try:
                    predicted_category = text_clf.predict([service_name])[0]
                    logger.info(f"Service '{service_name}' predicted as category '{predicted_category}' for provider '{provider}'")
                except Exception as e:
                    logger.error(f"Error predicting category for service '{service_name}': {e}")
                    predicted_category = "Unknown"
                final_category.append(predicted_category)
                predictions[service_name] = predicted_category
            else:
                final_category.append(predictions[service_name])
        df['category'] = final_category

        logger.info(f"DataFrame for provider {provider} with categories:\n{df.head()}")

        return df

    def aggregate_counts(self):
        aggregated_data = {}

        for provider, df in [('aws', self.aws_dataframe),
                             ('azure', self.azure_dataframe),
                             ('gcp', self.gcp_dataframe)]:
            if df.empty:
                continue
            count_series = df['category'].value_counts()
            for category, count in count_series.items():
                if category not in aggregated_data:
                    aggregated_data[category] = {'aws_count': 0, 'azure_count': 0, 'gcp_count': 0}
                aggregated_data[category][f"{provider}_count"] += count
        
        self.data = pd.DataFrame.from_dict(aggregated_data, orient='index').reset_index()
        self.data.rename(columns={'index': 'category'}, inplace=True)

        self.data.fillna(0, inplace=True)

        for provider in ['aws', 'azure', 'gcp']:
            col = f"{provider}_count"
            if col in self.data.columns:
                self.data[col] = self.data[col].astype(int)
        
        logger.info(f"Aggregated DataFrame (Counts):\n{self.data.head()}")
