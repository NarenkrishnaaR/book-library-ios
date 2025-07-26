import os
import openai
import requests

openai.api_key = os.getenv("OPENAI_API_KEY")
repo = os.getenv("REPO")
pr_number = os.getenv("PR_NUMBER")
token = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}

# Get PR diff
diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
response = requests.get(diff_url, headers=headers)
files = response.json().get("files", [])
diffs = ""

for file in files:
    if file["filename"].endswith(".swift"):
        patch = file.get("patch", "")
        if patch:
            diffs += f"\n---\nFile: {file['filename']}\n{patch}\n"

if not diffs:
    print("No Swift file changes detected.")
    exit(0)

# Ask GPT-4 for review
prompt = f"""You're an iOS expert. Focus on:
- Retain cycles
- Misuse of `weak self`
- UIKit/SwiftUI best practices
- Unsafe force unwraps
- Async/Await misuse
- Naming conventions
- MVVM architecture violations

{diffs}
"""

print("Sending diff to GPT-4...")

review = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert iOS code reviewer."},
        {"role": "user", "content": prompt}
    ]
)

feedback = review.choices[0].message["content"]

# Post feedback to the PR
comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
payload = {"body": f"🧠 **AI Code Review Suggestions**:\n\n{feedback}"}
r = requests.post(comment_url, headers=headers, json=payload)

if r.status_code == 201:
    print("Posted review to PR.")
else:
    print("Failed to post comment:", r.text)
