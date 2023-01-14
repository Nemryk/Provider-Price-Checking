from github import Github
import requests


class Infracost_Fetch:
  gcp_data = []
  aws_data = []
  azure_data = []

  def __init__(self, secrets):
    aws_services = self.get_services("infracost/infracost",
                                     "internal/resources", "aws", secrets[0])
    self.aws_data = self.fetch_infracost(aws_services, "aws", secrets[1])
    azure_services = self.get_services("infracost/infracost",
                                       "internal/resources", "azure",
                                       secrets[0])
    self.azure_data = self.fetch_infracost(azure_services, "azure", secrets[1])
    gcp_services = self.get_services("infracost/infracost",
                                     "internal/resources", "google",
                                     secrets[0])
    self.gcp_data = self.fetch_infracost(gcp_services, "gcp", secrets[1])

  def get_services(self, repository, path, provider, github_key):
    g = Github(github_key)
    repo = g.get_repo(repository)
    value = repo.get_contents(path + "/" + provider)
    while len(value) > 0:
      file_content = value.pop(0)
      if file_content.type == 'dir':
        value.extend(repo.get_contents(file_content.path))
      else:
        table = ""
        for single_file in value:
          raw_file_content = single_file.decoded_content.decode('utf-8')
          is_service_found = False
          for item in raw_file_content.split("\n"):
            if "Service:" in item and is_service_found:
              table += "|"
              is_service_found = False
            if "Service:" in item:
              item = item.strip().replace("Service:    ", "")
              table += item
              is_service_found = True
            if "ProductFamily:" in item:
              item = item.replace(" ", "")
              table += item + "|"
              is_service_found = False
        table = table.replace("strPtr", "")
        table = table.replace("ProductFamily", "")
        table = table.replace("(", "")
        table = table.replace(")", "")
        table = table.replace('"', '')
        table = table.replace(",|", "|")
        table = table.replace(":", "")
        table = table.strip()
        formatted_data = []
        rows = table.split("|")
        for row in rows:
          row_formatted = row.split(",")
          if len(row_formatted) > 0:
            a = row_formatted[0].strip()
          else:
            a = None
          if len(row_formatted) > 1:
            b = row_formatted[1].strip()
          else:
            b = None
          if a != "" and b != "" and a != None and b != None:
            formatted_data.append(a)
        formatted_data = list(dict.fromkeys(formatted_data))
        return formatted_data

  def get_infracost(self, body, api_key):
    response = requests.post('https://pricing.api.infracost.io/graphql',
                             headers={
                               'X-Api-Key': api_key,
                               'Content-Type': 'application/json'
                             },
                             json={"query": body})
    return response.json()['data']['products']

  def fetch_infracost(self, srvs, provider, api_key):
    body_template = """
      {
        products(
          filter: {
            vendorName: "VENDOR"
            service: "SERVICE"
          }
        ) {
          productFamily
          service
          prices(
            filter: {}
          ){ USD }
        }
      }
    """
    body_template = body_template.replace("VENDOR", provider)
    data = []
    for service in srvs:
      body = body_template.replace("SERVICE", service)
      data += self.get_infracost(body, api_key)
    return data
