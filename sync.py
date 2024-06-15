import os
import json
import requests

GITHUB_USER = "{REPLACE_YOUR}"
RAINDROP_API_TOKEN = "{REPLACE_YOUR}"
GITHUB_TOKEN = "{REPLACE_YOUR}"
RAINDROP_COLLECTION_ID = {REPLACE_YOUR}


GITHUB_SYNC_LOCK = f"{os.path.expanduser('~')}/.github-sync-record.txt"
if not os.path.exists(GITHUB_SYNC_LOCK):
    try:
        with open(GITHUB_SYNC_LOCK, "w") as file:
            print(f"File '{GITHUB_SYNC_LOCK}' created.")
    except IOError as e:
        print(f"Error creating file: {e}")
else:
    print(f"GITHUB_SYNC_LOCK: '{GITHUB_SYNC_LOCK}'")


def append_to_file(line_to_append):
    with open(GITHUB_SYNC_LOCK, 'a') as file:
        file.write(line_to_append + '\n')


def contains_line(line_to_check):
    with open(GITHUB_SYNC_LOCK, 'r') as file:
        for existing_line in file:
            if existing_line.strip() == line_to_check.strip():
                return True
    return False


def post_to_raindrop(json_data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RAINDROP_API_TOKEN}"
    }
    response = requests.post("https://api.raindrop.io/rest/v1/raindrops", data=json.dumps({"items": json_data}),
                             headers=headers)
    response.raise_for_status()


print("Getting github stars")
github_repo = []
page = 1
json_data = ""
while True:
    url = f"https://api.github.com/users/{GITHUB_USER}/starred?per_page=100&page={page}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.star+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if not data:
        break
    for item in data:
        github_repo.append(item)
    page += 1
print()

print("Posting to raindrop")
to_push_item = []
for repo in github_repo:
    full_name = repo['repo']['full_name']
    if contains_line(full_name):
        continue
    print("-add:" + full_name)

    tags = ["github-star"]
    if repo['repo']['language']:
        language = "Lang-" + repo['repo']['language']
        tags.append(language)

    json_data = {
        "title": repo['repo']['name'],
        "excerpt": repo['repo']['description'],
        "tags": tags,
        "link": repo['repo']['html_url'],
        "created": repo['repo']['created_at'],
        "lastUpdate": repo['repo']['created_at'],
        "collection": {
            "$ref": "collections",
            "$id": RAINDROP_COLLECTION_ID,
            "oid": "-1"
        }
    }
    to_push_item.append(json_data)
    append_to_file(full_name)

    if len(to_push_item) == 100:
        post_to_raindrop(to_push_item)
        to_push_item = []

if len(to_push_item) > 0:
    post_to_raindrop(to_push_item)
    to_push_item = []

print()
print("Done!")
