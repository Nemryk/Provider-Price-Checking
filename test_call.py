from github import Github, GithubException
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfracostFetch:
    def __init__(self, token):
        self.github = Github(token)
    
    def get_services(self, repo_name, path, provider, branch='master'):
        try:
            repo = self.github.get_repo(repo_name)
            full_path = f"{path}/{provider}"
            contents = repo.get_contents(full_path, ref=branch)
            services = [content_file.path for content_file in contents]
            logger.info(f"Fetched services: {services}")
            return services
        except GithubException as e:
            logger.error(f"Error fetching {path}/{provider} from {repo_name}: {e.status} {e.data.get('message')}")
            return None

def main():
    token = "token"
    if not token:
        logger.error("GitHub token not found in environment variables.")
        return

    infracost_fetch = InfracostFetch(token)
    services = infracost_fetch.get_services("infracost/infracost", "internal/resources", "aws")
    if services is not None:
        for service in services:
            logger.info(f"Service: {service}")

if __name__ == "__main__":
    main()
