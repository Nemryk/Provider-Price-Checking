from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion


class Result:

  def __init__(self):
    values = self.input_values()
    self.name = values[0]
    self.provider = values[1]
    self.price = values[2]

  def input_values(self):
    name = input("Podaj nazwę usługi: ")
    provider = input("Podaj providera (aws/azure/gcp): ")
    if provider.lower().strip() not in ["aws", "azure", "gcp"]:
      return self.input_values()
    price = input("Podaj cenę: ")
    if not price.replace(".", "", 1).isdigit():
      return self.input_values()
    return [name, provider, price]

  def get_result(self, df, data):
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
       )), ('clf', MultinomialNB())
    ])
    text_clf.fit(texts, categories)
    predicted_category = text_clf.predict([self.name])
    df = df[df['category'] == predicted_category[0]]
    y_median = ['aws_median', 'azure_median', 'gcp_median']
    x_median = df[f'{self.provider}_median'].values[0]
    y_median.remove(f'{self.provider}_median')
    factor = float(self.price) / x_median
    print(f"Przybliżona kategoria: {predicted_category[0]}")
    for median in y_median:
      val = "{:.2f}".format(df[median].values[0] * factor)
      print(
        f"Szacowana cena w {median.replace('_median', '').upper()}: {val}")
