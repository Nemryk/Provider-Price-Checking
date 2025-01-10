import os
import logging
from github import Github, GithubException
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfracostFetch:
    def __init__(self, token):
        self.github = Github(token)
        self.aws_data = self.fetch_provider_data("aws")
        self.azure_data = self.fetch_provider_data("azure")
        self.gcp_data = self.fetch_provider_data("gcp")
    
    def get_services(self, repo_name, path, branch='master'):
        try:
            logger.info(f"Accessing repository: {repo_name}")
            repo = self.github.get_repo(repo_name)
            logger.info(f"Fetching contents from path: {path} on branch: {branch}")
            contents = repo.get_contents(path, ref=branch)
            services = [
                content_file.path for content_file in contents 
                if content_file.type == 'file' 
                and not content_file.path.endswith('_test.go') 
                and not content_file.path.endswith('util.go') 
                and not content_file.path.endswith('util_test.go')
            ]
            logger.info(f"Fetched services: {services}")
            return services
        except GithubException as e:
            logger.error(f"Error fetching {path} from {repo_name}: {e.status} {e.data.get('message')}")
            return None

    def fetch_provider_data(self, provider):
        repo_name = "infracost/infracost"
        branch = 'master'
        if provider == 'gcp':
            path = "internal/resources/google"
        else:
            path = f"internal/resources/{provider}"
        
        services = self.get_services(repo_name, path, branch)
        if not services:
            logger.warning(f"No services found for provider: {provider}")
            return []
        
        provider_data = []
        for service in services:
            logger.info(f"Processing service: {service}")
            try:
                file_content = self.github.get_repo(repo_name).get_contents(service, ref=branch).decoded_content.decode()
                cost_components = parse_service_file(file_content, service)
                if not cost_components:
                    logger.warning(f"No data returned for service: {service}")
                    continue
                provider_data.append(cost_components)
            except GithubException as e:
                logger.error(f"Error fetching file {service}: {e.status} {e.data.get('message')}")
        return provider_data

def parse_service_file(file_content, service_path):
    """
    Parses the Go service file to extract the service name and assigns a dummy unit_cost.
    Enhances regex to handle multi-line patterns and varying whitespaces.
    """
    cost_components = {}
    
    pattern = r'func\s*\(\w+\s*\*\w+\)\s*CoreType\s*\(\)\s*string\s*\{\s*return\s+"([^"]+)"\s*\}'
    
    service_match = re.search(pattern, file_content, re.MULTILINE | re.DOTALL)
    if service_match:
        service_name = service_match.group(1)
        cost_components["service"] = service_name
        cost_components["unit_cost"] = 1.0
        logger.info(f"Extracted service name: {service_name} from {service_path}")
    else:
        logger.warning(f"Service name not found in the file: {service_path}")
        snippet = file_content[:200].replace('\n', ' ')
        logger.debug(f"File snippet for {service_path}: {snippet}")
        return {}
    
    return cost_components


def calculate_costs(cost_components, usage_metrics):
    """
    Calculates the total cost based on unit_cost and usage_metrics.
    """
    total_cost = 0.0
    for component in cost_components:
        service = component.get('service', 'Unknown')
        unit_cost = component.get('unit_cost', 0)
        usage = usage_metrics.get(service, 0)
        component_cost = unit_cost * usage
        total_cost += component_cost
        logger.info(f"{service}: {usage} * {unit_cost} = {component_cost}")
    logger.info(f"Total Cost: {total_cost}")
    return total_cost

def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GitHub token not found in environment variables.")
        return

    infracost_fetch = InfracostFetch(token)
    
    usage_metrics = {
    }

    for provider, data in [('aws', infracost_fetch.aws_data),
                           ('azure', infracost_fetch.azure_data),
                           ('gcp', infracost_fetch.gcp_data)]:
        for cost_component in data:
            calculate_costs([cost_component], usage_metrics)

if __name__ == "__main__":
    main()
