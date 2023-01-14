import yaml
import json
import string
import re
import requests


class process_yml():

  def __init__(self):
    self.load_data()
    self.parse_data()

  def load_data(self):
    response = requests.get(
      "https://raw.githubusercontent.com/ilyas-it83/CloudComparer/main/_data/cloudservices.yml"
    )
    ymlFile = yaml.full_load(response.content)
    data = json.loads(json.dumps(ymlFile))
    self.data = data

  def process_data(self, provider_string, cloud_data, service):
    chars = re.escape(string.punctuation)
    for provider in service[provider_string]:
      if 'name' not in provider: continue
      if provider['name'] is None: continue
      cloud_data.append(
        re.sub(r'["()]', '', json.dumps(provider['name'])).strip().split())
      cloud_data.append(
        re.sub(r'[' + chars + ']', ' ',
               json.dumps(provider['name'])).strip().split())
      cloud_data.append([provider['name']])
      cloud_data.append([provider['name'].replace(' ', '')])
    if len(cloud_data) > 0:
      return None
    return cloud_data

  def flatten_list(self, list):
    flatten = [num for sublist in list for num in sublist]
    return flatten

  def parse_data(self):
    parsed_data = {}
    aws_data = []
    azure_data = []
    google_data = []
    category = self.data['services'][0]['category']
    for service_all in self.data['services']:
      for service in service_all['service']:
        if 'aws' in service:
          self.process_data("aws", aws_data, service)
        if 'azure' in service:
          self.process_data("azure", azure_data, service)
        if 'google' in service:
          self.process_data("google", google_data, service)
        if service_all['category'] != category:
          parsed_data[category] = {
            'aws': tuple(list(dict.fromkeys(self.flatten_list(aws_data)))),
            'azure': tuple(list(dict.fromkeys(self.flatten_list(azure_data)))),
            'google':
            tuple(list(dict.fromkeys(self.flatten_list(google_data))))
          }
          aws_data = []
          azure_data = []
          google_data = []
          category = service_all['category']
    self.data = parsed_data
