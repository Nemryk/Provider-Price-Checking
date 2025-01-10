import yaml
import json
import string
import re
import requests
import logging

class ProcessYML:

    def __init__(self):
        self.load_data()
        self.parse_data()

    def load_data(self):
        try:
            response = requests.get(
                "https://raw.githubusercontent.com/ilyas-it83/CloudComparer/main/_data/cloudservices.yml"
            )
            response.raise_for_status()
            yml_file = yaml.safe_load(response.text)
            self.data = yml_file
            logging.info("YAML data loaded successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to load YAML data: {e}")
            self.data = {}

    def process_data(self, provider_string, cloud_data, service):
        chars = re.escape(string.punctuation)
        for provider in service.get(provider_string, []):
            name = provider.get('name')
            if not name:
                continue
            processed_names = [
                re.sub(r'["()]', '', name).strip().split(),
                re.sub(f'[{chars}]', ' ', name).strip().split(),
                [name],
                [name.replace(' ', '')]
            ]
            for processed_name in processed_names:
                cloud_data.append(processed_name)

    def flatten_list(self, lst):
        return [item for sublist in lst for item in sublist]

    def parse_data(self):
        if not self.data:
            logging.error("No data to parse.")
            self.data = {}
            return

        parsed_data = {}
        aws_data = []
        azure_data = []
        google_data = []
        current_category = None

        for service_group in self.data.get('services', []):
            category = service_group.get('category')
            if not category:
                continue
            for service in service_group.get('service', []):
                if 'aws' in service:
                    self.process_data("aws", aws_data, service)
                if 'azure' in service:
                    self.process_data("azure", azure_data, service)
                if 'google' in service:
                    self.process_data("google", google_data, service)
            if category:
                parsed_data[category] = {
                    'aws': tuple(list(dict.fromkeys(self.flatten_list(aws_data)))),
                    'azure': tuple(list(dict.fromkeys(self.flatten_list(azure_data)))),
                    'google': tuple(list(dict.fromkeys(self.flatten_list(google_data))))
                }
                aws_data.clear()
                azure_data.clear()
                google_data.clear()

        self.data = parsed_data
        logging.info("YAML data parsed successfully.")
