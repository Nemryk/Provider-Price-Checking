# result.py
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion
import matplotlib.pyplot as plt
import logging

class Result:

    def __init__(self):
        values = self.input_values()
        self.name = values[0]
        self.provider = values[1]
        self.price = values[2]

    def input_values(self):
        name = input("Podaj nazwę usługi: ").strip()
        provider = input("Podaj providera (aws/azure/gcp): ").strip().lower()
        if provider not in ["aws", "azure", "gcp"]:
            logging.error("Invalid provider. Please enter aws, azure, or gcp.")
            return self.input_values()
        price = input("Podaj cenę: ").strip()
        try:
            price = float(price)
        except ValueError:
            logging.error("Invalid price. Please enter a numeric value.")
            return self.input_values()
        return [name, provider, price]

    def get_result(self, df, data):
        if df.empty:
            logging.error("DataFrame is empty. Cannot compute results.")
            return

        texts = []
        categories = []
        for category in data:
            for platform in data[category]:
                texts.append(" ".join(data[category][platform]))
                categories.append(category)
        text_clf = Pipeline([
            ('union',
             FeatureUnion(
                 transformer_list=[('cv_word', CountVectorizer()),
                                   ('cv_char', CountVectorizer(analyzer="char"))],
                 transformer_weights={
                     'cv_word': 0.8,
                     'cv_char': 0.2
                 },
             )),
            ('clf', MultinomialNB())
        ])
        text_clf.fit(texts, categories)
        predicted_category = text_clf.predict([self.name])[0]
        logging.info(f"Przybliżona kategoria: {predicted_category}")

        filtered_df = df[df['category'] == predicted_category]
        if filtered_df.empty:
            logging.error("No data found for the predicted category.")
            return

        if f'{self.provider}_median' not in filtered_df.columns:
            logging.error(f"Provider {self.provider} data is missing.")
            return

        x_median = filtered_df[f'{self.provider}_median'].values[0]
        other_providers = ['aws', 'azure', 'gcp']
        other_providers.remove(self.provider)
        factor = self.price / x_median
        logging.info(f"Szacowana cena w innych providerach (faktor: {factor:.2f}):")
        for prov in other_providers:
            if f'{prov}_median' in filtered_df.columns:
                estimated_price = filtered_df[f'{prov}_median'].values[0] * factor
                logging.info(f"  {prov.upper()}: {estimated_price:.2f} USD")

        # Export results
        self.export_to_csv(filtered_df, predicted_category)

        # Visualize results
        self.visualize_median_prices(filtered_df, predicted_category)

    def export_to_csv(self, df, category, filename=None):
        if not filename:
            filename = f"results_{category}.csv"
        df.to_csv(filename, index=False)
        logging.info(f"Results exported to {filename}")

    def visualize_median_prices(self, df, category):
        providers = ['aws_median', 'azure_median', 'gcp_median']
        prices = df.loc[df['category'] == category, providers].values.flatten()

        plt.figure(figsize=(8, 6))
        plt.bar(providers, prices, color=['blue', 'green', 'orange'])
        plt.xlabel('Providers')
        plt.ylabel('Median Price (USD)')
        plt.title(f'Median Prices for {category}')
        plt.tight_layout()
        plt.show()
