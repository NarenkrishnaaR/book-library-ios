import os
import openai
import requests

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
repo = os.getenv("REPO")
pr_number = os.getenv("PR_NUMBER")
token = os.getenv("GITHUB_TOKEN")

print(f"🔍 Repo: {repo}")
print(f"🔍 PR Number: {pr_number}")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}

# Get PR diff
diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
print(f"➡️  Fetching PR diff from: {diff_url}")

response = requests.get(diff_url, headers=headers)
print("📦 GitHub API response status:", response.status_code)

if response.status_code != 200:
    print("❌ Failed to fetch PR details:", response.text)
    exit(1)

try:
    files = response.json()
    if not files:
        print("⚠️ No files returned in the PR diff.")
    else:
        print("🧾 Files found in PR:")
        for f in files:
            print(f"• {f['filename']}")
except Exception as e:
    print("❌ Error parsing JSON:", e)
    print("Raw response text:", response.text)
    exit(1)

# Filter Swift files
diffs = ""
for file in files:
    if file["filename"].endswith(".swift"):
        patch = file.get("patch", "")
        if patch:
            diffs += f"\n---\nFile: {file['filename']}\n{patch}\n"

if not diffs:
    print("⚠️ No Swift file changes detected.")
    exit(0)

# Ask GPT-4 for code review
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

print("🧠 Sending diff to GPT-4...")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert iOS code reviewer."},
        {"role": "user", "content": prompt}
    ]
)

feedback = response.choices[0].message["content"]
print("✅ Review content generated.")

# Post feedback to PR as a comment
comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
payload = {"body": f"🧠 **AI Code Review Suggestions**:\n\n{feedback}"}

post_response = requests.post(comment_url, headers=headers, json=payload)
if post_response.status_code == 201:
    print("✅ Posted review comment to PR.")
else:
    print(f"❌ Failed to post comment: {post_response.status_code} - {post_response.text}")
