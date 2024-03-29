import github.GithubException
from github import Github
import p_requests
from functions import language_bytes_to_percentage, get_first_line, \
    mine_feature_data, append_to_dataset


test = True
token = get_first_line("token.txt")
g = Github(token)


# gets every repo in the org
org = g.get_organization('bbd-test-research')
forks = org.get_repos()
# forks = [g.get_repo("AutomationPanda/behavior-driven-python")]

# filters out selected repos that aren't in the spreadsheet
repos_to_exclude = ['Docker-Environments', 'BDD-Repo-Miner', 'Data-Mining']


for repo in forks:
    if repo.name in repos_to_exclude:
        continue
    repo = repo.parent
    print(f"Mining repo: {repo.full_name}")
    for attempt in range(3):
        repo_info = {
            'basic repo info': {
                'name': '',
                'description': '',
                'languages': dict(),
                'license': '',
                'topics': [],
                'created_at': {
                    'day': 0,
                    'month': 0,
                    'year': 0
                },
                'pushed_at': {
                    'day': 0,
                    'month': 0,
                    'year': 0
                }
                # 'about':, about project section
                # 'summary':, chatgpt generated summary from readme and about section

            },
            'feature data': {
                'total_features': 0,
                'scenario_keywords': 0,
                'scenario_outline_keywords': 0,
                'examples_keywords': 0,
                'example_keywords': 0,
                'total_examples_tables': 0,
            },
            'github stats': {
                'commits': 0,
                'watchers': 0,
                'forks': 0,
                'stars': 0,
                'issues': 0,
                'pull_requests': 0,
                'branches': 0,
                'contributors': 0,
                'bugs': {
                    'open': 0,
                    'closed': 0,
                    'average_closing_time_seconds': 0
                },

            },
            "interval statistics": {
                "average_interval_between_commits_seconds": 0,
                "average_interval_between_issue_closings_seconds": 0,
            }
        }
        basic_repo_info = repo_info['basic repo info']
        github_stats = repo_info['github stats']
        created_at = basic_repo_info['created_at']
        pushed_at = basic_repo_info['pushed_at']
        interval_statistics = repo_info['interval statistics']

        try:
            basic_repo_info['license'] = p_requests.get_repo_license(repo, g).license.spdx_id
            basic_repo_info['name'] = repo.full_name
            basic_repo_info['languages'] = language_bytes_to_percentage(p_requests.get_repo_languages(repo, g))
            basic_repo_info['topics'] = repo.topics
            basic_repo_info['description'] = repo.description
            created_at['day'] = repo.created_at.day
            created_at['month'] = repo.created_at.month
            created_at['year'] = repo.created_at.year

            pushed_at['day'] = repo.pushed_at.day
            pushed_at['month'] = repo.pushed_at.month
            pushed_at['year'] = repo.pushed_at.year

            interval_statistics['average_interval_between_commits_seconds'] = p_requests.get_average_commit_interval(repo, g)
            interval_statistics['average_interval_between_issue_closings_seconds'] = p_requests.get_average_issue_closing_time(repo, g)

            github_stats['commits'] = p_requests.get_repo_commit_count(repo, g)
            github_stats['branches'] = p_requests.get_branches(repo, g).totalCount
            github_stats['watchers'] = repo.subscribers_count
            github_stats['forks'] = repo.forks_count
            github_stats['stars'] = repo.stargazers_count
            github_stats['issues'] = repo.open_issues
            github_stats['pull_requests'] = p_requests.get_repo_pull_request_count(repo, github=g)
            github_stats['contributors'] = p_requests.get_contributor_count(repo, g)
            # open_issues by default counts pull_requests, so we subtract to reflect the actual
            # issues count on the GitHub website
            closed_bugs, open_bugs, average_closing_time = p_requests.get_bug_info(repo, g)
            github_stats['bugs']['open'] = open_bugs
            github_stats['bugs']['closed'] = closed_bugs
            github_stats['bugs']['average_closing_time_seconds'] = average_closing_time

            github_stats['issues'] = repo.open_issues - github_stats['pull_requests']
            features = p_requests.get_repo_features(f'extension:feature repo:{repo.full_name}', g)
            mine_feature_data(features, repo_info['feature data'], g)
            append_to_dataset(repo_info)
            break
        except github.UnknownObjectException as e:
            print(f"Some object was not found, 404 error")
            print(e)
        except github.RateLimitExceededException:
            p_requests.check_limit(github=g)
            print(f"ERROR: Github api limit reached. (retrying to mine repository {repo.full_name}: attempt {attempt})")
        except Exception as e:
            print(e)
            raise(e)
            print(f"ERROR when processing repository (retrying to mine repository {repo.full_name}: attempt {attempt})")
            append_to_dataset(repo_info, "trash.json")
