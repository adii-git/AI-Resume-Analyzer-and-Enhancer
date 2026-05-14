import requests

headers = {
    'Authorization': 'token ITsadi@1256',
    'Accept': 'application/vnd.github.v3+json'
}

data = {
    'name': 'AI-Resume-Enhancer',
    'description': 'AI Resume Analyzer and Enhancer',
    'private': False
}

response = requests.post('https://api.github.com/user/repos', json=data, headers=headers)

if response.status_code == 201:
    repo_data = response.json()
    print(f"✓ Repository created successfully!")
    print(f"Repository URL: {repo_data['clone_url']}")
    print(f"HTML URL: {repo_data['html_url']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
