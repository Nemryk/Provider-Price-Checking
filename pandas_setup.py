import json
import pandas as pd
import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion


class Pandas_data_formatter:
  categories = {}
  yml = {}
  def __init__(self, infracost_data, processed_yml):
    self.yml = processed_yml
    self.aws_dataframe = self.generate_dataframe("aws",
                                                 infracost_data.aws_data)
    self.azure_dataframe = self.generate_dataframe("azure",
                                                   infracost_data.azure_data)
    self.gcp_dataframe = self.generate_dataframe("gcp",
                                                 infracost_data.gcp_data)
    data_new = {}
    for category in self.categories:
      if 'aws' in self.categories[category] and 'azure' in self.categories[
          category] and 'gcp' in self.categories[category]:
        data_new[category] = self.yml[category]
    self.yml = data_new
    self.aws_dataframe = self.generate_dataframe("aws",
                                                 infracost_data.aws_data)
    self.azure_dataframe = self.generate_dataframe("azure",
                                                   infracost_data.azure_data)
    self.gcp_dataframe = self.generate_dataframe("gcp",
                                                 infracost_data.gcp_data)
    self.filter_data()
  def try_convert(self, x):
    try:
      return x.get("USD")
    except:
      return 0

  def generate_dataframe(self, type, cloud_data):
    df = pd.read_json(json.dumps(cloud_data))
    df = df.explode('prices')
    df['prices'] = df['prices'].apply(lambda x: self.try_convert(x))
    df['prices'] = df['prices'].astype(np.float64)
    df = df.reset_index(drop=True)
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
             transformer_list=[('cv_word', CountVectorizer()),
                               ('cv_char', CountVectorizer(analyzer="char"))],
             transformer_weights={
               'cv_word': 1,
               'cv_char': 0
             },
           )), ('clf', MultinomialNB())
        ])
        text_clf.fit(texts, categories)
        predicted_category = text_clf.predict([service_name])
        final_category.append(predicted_category[0])
        if predicted_category[0] in self.categories:
          self.categories[predicted_category[0]][type] = 1
        else:
          self.categories[predicted_category[0]] = {type: 1}
        predictions[service_name] = predicted_category[0]
      else:
        final_category.append(predictions[service_name])
    df['category'] = final_category
    return df

  def filter_data(self):
    self.aws_dataframe = self.aws_dataframe[(self.aws_dataframe['prices'] >= 0.1) & (self.aws_dataframe['prices'] < 5)]
    self.aws_dataframe = self.aws_dataframe.sort_values(by=['prices'], ascending=True)
    self.azure_dataframe = self.azure_dataframe[(self.azure_dataframe['prices'] >= 0.1) & (self.azure_dataframe['prices'] < 5)]
    self.azure_dataframe = self.azure_dataframe.sort_values(by=['prices'], ascending=True)
    self.gcp_dataframe = self.gcp_dataframe[(self.gcp_dataframe['prices'] >= 0.1) & (self.gcp_dataframe['prices'] < 5)]
    self.gcp_dataframe = self.gcp_dataframe.sort_values(by=['prices'], ascending=True)
    max_values = [len(self.aws_dataframe.index), len(self.azure_dataframe.index), len(self.gcp_dataframe.index)]
    min_values = min(max_values)
    self.aws_dataframe = self.aws_dataframe.head(min_values)
    self.azure_dataframe = self.azure_dataframe.head(min_values)
    self.gcp_dataframe = self.gcp_dataframe.head(min_values)
    self.aws_dataframe = self.aws_dataframe.groupby(['category']).prices.agg(['median'])
    self.aws_dataframe = self.aws_dataframe.reset_index()
    self.aws_dataframe.columns = ['category', 'aws_median']
    self.azure_dataframe = self.azure_dataframe.groupby(['category']).prices.agg(['median'])
    self.azure_dataframe = self.azure_dataframe.reset_index()
    self.azure_dataframe.columns = ['category', 'azure_median']
    self.gcp_dataframe = self.gcp_dataframe.groupby(['category']).prices.agg(['median'])
    self.gcp_dataframe = self.gcp_dataframe.reset_index()
    self.gcp_dataframe.columns = ['category', 'gcp_median']
    self.data = self.aws_dataframe.merge(self.azure_dataframe, on='category', how='outer').merge(self.gcp_dataframe, on='category', how='outer')
    
    