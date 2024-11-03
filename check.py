import requests
import csv
import time

GITHUB_TOKEN = "you_did_not_expect_to_find_my_token_here_did_you?"  # Replace with your own GitHub token
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

def check_rate_limit():
    response = requests.get("https://api.github.com/rate_limit", headers=HEADERS)
    data = response.json()
    remaining = data['rate']['remaining']
    reset_time = data['rate']['reset']
    print(f"API calls remaining: {remaining}")
    if remaining == 0:
        print(f"Rate limit exceeded. Resets at {reset_time}")
        return False
    return True

def get_users_in_basel():
    users = []
    query = "location:Mumbai+followers:>50"
    page = 1
    per_page = 50  # Reduced per_page size to minimize issues
    total_users = 0

    while True:
        if not check_rate_limit():
            print("Waiting for rate limit reset...")
            time.sleep(60)  # Wait 1 minute before retrying
            continue

        url = f"https://api.github.com/search/users?q={query}&per_page={per_page}&page={page}"
        response = requests.get(url, headers=HEADERS, timeout=10)  # Set timeout to 10 seconds
        print(f"Fetching page {page}...")

        if response.status_code != 200:
            print("Error fetching data:", response.json())
            break

        data = response.json()
        users.extend(data['items'])
        total_users += len(data['items'])
        print(f"Page {page} fetched: Added {len(data['items'])} users. Total users so far: {total_users}")

        if len(data['items']) < per_page:
            break

        page += 1

    detailed_users = []
    for i, user in enumerate(users, start=1):  # 'start=1' to begin count at 1
        if 'login' in user:  # Ensure 'login' field exists
            user_info = get_user_details(user['login'])
            print(f"Adding user {i}: {user_info['login']}")
            detailed_users.append(user_info)
        else:
            print(f"Skipping user {i} with missing login information")


    return detailed_users

def get_user_details(username):
    user_url = f"https://api.github.com/users/{username}"
    user_data = requests.get(user_url, headers=HEADERS, timeout=10).json()  # Set timeout to 10 seconds

    return {
        'login': user_data.get('login'),
        'name': user_data.get('name'),
        'company': clean_company_name(user_data.get('company')),
        'location': user_data.get('location'),
        'email': user_data.get('email'),
        'hireable': user_data.get('hireable'),
        'bio': user_data.get('bio'),
        'public_repos': user_data.get('public_repos'),
        'followers': user_data.get('followers'),
        'following': user_data.get('following'),
        'created_at': user_data.get('created_at'),
    }

def clean_company_name(company):
    if company:
        company = company.strip().upper()
        if company.startswith('@'):
            company = company[1:]
    return company

def get_user_repos(username):
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=500"
    response = requests.get(repos_url, headers=HEADERS, timeout=10)  # Set timeout to 10 seconds
    repos_data = response.json()

    repos = []
    for repo in repos_data:
        repos.append({
            'login': username,
            'full_name': repo['full_name'],
            'created_at': repo['created_at'],
            'stargazers_count': repo['stargazers_count'],
            'watchers_count': repo['watchers_count'],
            'language': repo['language'],
            'has_projects': repo['has_projects'],
            'has_wiki': repo['has_wiki'],
            'license_name': repo['license']['key'] if repo['license'] else None,
        })
        print(f"Added repository: {repo['full_name']}")

    return repos

def save_users_to_csv(users):
    with open('users.csv', mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['login', 'name', 'company', 'location', 'email', 'hireable', 'bio', 'public_repos', 'followers', 'following', 'created_at'])
        writer.writeheader()
        writer.writerows(users)

def save_repos_to_csv(repos):
    with open('repositories.csv', mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['login', 'full_name', 'created_at', 'stargazers_count', 'watchers_count', 'language', 'has_projects', 'has_wiki', 'license_name'])
        writer.writeheader()
        writer.writerows(repos)

if __name__ == "__main__":
    users = get_users_in_basel()
    save_users_to_csv(users)

    all_repos = []
    for user in users:
        repos = get_user_repos(user['login'])
        all_repos.extend(repos)

    save_repos_to_csv(all_repos)
    print("Done")

