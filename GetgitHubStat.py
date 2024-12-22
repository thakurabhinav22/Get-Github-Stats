import datetime
from dateutil import relativedelta
import requests
from xml.dom import minidom

# Directly assigning the access token and username
ACCESS_TOKEN = 'AccessToken'
USER_NAME = 'UserName'

# GitHub API headers
HEADERS = {'authorization': f'token {ACCESS_TOKEN}'}

# Query count for debugging
QUERY_COUNT = {'user_getter': 0, 'follower_getter': 0, 'graph_repos_stars': 0, 'recursive_loc': 0, 'graph_commits': 0, 'loc_query': 0}

def daily_readme(birthday):
    """Calculate age in years, months, and days since the given date."""
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years),
        diff.months, 'month' + format_plural(diff.months),
        diff.days, 'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '')

def format_plural(unit):
    """Return 's' for plural or empty string for singular."""
    return 's' if unit != 1 else ''

def simple_request(func_name, query, variables):
    """Send a GraphQL query request."""
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=HEADERS)
    if request.status_code == 200:
        return request
    elif request.status_code == 401:
        raise Exception(f"Unauthorized: Please check your API token. {request.text}")
    elif request.status_code == 403:
        raise Exception(f"Forbidden: API rate limit exceeded. {request.text}")
    else:
        raise Exception(f"{func_name} has failed with status code {request.status_code}: {request.text}")

def graph_commits(start_date, end_date):
    """Fetch total commits between two dates."""
    query = '''
    query($start_date: DateTime!, $end_date: DateTime!, $login: String!) {
        user(login: $login) {
            contributionsCollection(from: $start_date, to: $end_date) {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }'''
    variables = {'start_date': start_date, 'end_date': end_date, 'login': USER_NAME}
    request = simple_request('graph_commits', query, variables)
    return int(request.json()['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])

def graph_repos_stars(count_type, owner_affiliation, cursor=None):
    """Fetch repository count or stars."""
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
                totalCount
                edges {
                    node {
                        nameWithOwner
                        stargazers {
                            totalCount
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }'''
    variables = {'owner_affiliation': owner_affiliation, 'login': USER_NAME, 'cursor': cursor}
    request = simple_request('graph_repos_stars', query, variables)
    if count_type == 'repos':
        return request.json()['data']['user']['repositories']['totalCount']
    elif count_type == 'stars':
        return stars_counter(request.json()['data']['user']['repositories']['edges'])

def stars_counter(data):
    """Count total stars from the repository edges."""
    return sum(node['node']['stargazers']['totalCount'] for node in data)

def user_getter(username):
    """Fetch user details such as ID and creation date."""
    query = '''
    query($login: String!){
        user(login: $login) {
            id
            createdAt
        }
    }'''
    variables = {'login': username}
    request = simple_request('user_getter', query, variables)
    return {'id': request.json()['data']['user']['id']}, request.json()['data']['user']['createdAt']

def follower_getter(username):
    """Fetch the total number of followers."""
    query = '''
    query($login: String!){
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }'''
    request = simple_request('follower_getter', query, {'login': username})
    return int(request.json()['data']['user']['followers']['totalCount'])

# Main Execution
if __name__ == "__main__":
    try:
        user_data, created_at = user_getter(USER_NAME)
        age_data = daily_readme(datetime.datetime.fromisoformat(created_at.rstrip("Z")))

        repo_count = graph_repos_stars("repos", ["OWNER"])
        stars = graph_repos_stars("stars", ["OWNER"])
        follower_count = follower_getter(USER_NAME)

        commit_count = graph_commits(
            start_date=(datetime.datetime.today() - datetime.timedelta(days=365)).isoformat(),
            end_date=datetime.datetime.today().isoformat()
        )

        # Placeholder for contributions and LOC (Lines of Code)
        contributions = 0  # Replace with actual logic
        loc_data = (0, 0, 0)  # Replace with actual logic for LOC

        # Display data in the console
        print(f"User Age: {age_data}")
        print(f"Repository Count: {repo_count}")
        print(f"Total Stars: {stars}")
        print(f"Follower Count: {follower_count}")
        print(f"Commits (Last Year): {commit_count}")
        print(f"Contributions: {contributions}")
        print(f"Lines of Code (LOC): {loc_data}")

    except Exception as e:
        print(f"An error occurred: {e}")
