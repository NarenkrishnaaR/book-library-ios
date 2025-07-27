import os
from openai import OpenAI
import requests

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
repo = os.getenv("REPO")
pr_number = os.getenv("PR_NUMBER")
token = os.getenv("GITHUB_TOKEN")

print(f"🔍 Repo: {repo}")
print(f"🔍 PR Number: {pr_number}")

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}

# Fetch PR files
diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
print(f"➡️  Fetching PR diff from: {diff_url}")
response = requests.get(diff_url, headers=headers)
print("📦 GitHub API response status:", response.status_code)

if response.status_code != 200:
    print("❌ Failed to fetch PR details:", response.text)
    exit(1)

files = response.json()
if not files:
    print("⚠️ No files returned in the PR diff.")
    exit(0)

print("🧾 Files found in PR:")
for f in files:
    print(f"• {f['filename']}")

diffs = ""
for file in files:
    if file["filename"].endswith(".swift"):
        patch = file.get("patch", "")
    if patch:
        diffs += f"\n---\nFile: {file['filename']}\n{patch}\n"

if not diffs:
    print("⚠️ No Swift file changes detected.")
    exit(0)

# Prompt GPT to return structured review
prompt = f"""You're an expert iOS code reviewer. Analyze the following Swift code diff and return feedback in this **JSON format**:

{{
  "summary": "<brief summary of overall issues and improvements>",
  "comments": [
    {{
      "file": "<filename>",
      "line": <line_number>,
      "comment": "<explanation of why this line needs improvement>",
      "suggestion": "<Swift code suggestion to resolve the issue>"
    }}
  ]
}}

🔍 Review focus areas:
- Avoid force unwrapping (`!`) – use optional binding (`if let`, `guard let`) or `??`
- Apply SwiftUI best practices: views should not contain business logic
- Follow MVVM: move formatting/logic to ViewModel
- Keep SwiftUI views clean and declarative
- Maintain safe, readable, and idiomatic Swift code

Return only the JSON object. Avoid explanations outside the JSON.

Here is the code diff to review:
{diffs}
"""
print("🧠 Sending diff to GPT-4...")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are an expert iOS code reviewer."},
        {"role": "user", "content": prompt},
    ],
)

review = response.choices[0].message.content
import json

try:
    review_data = json.loads(review)
except Exception as e:
    print("❌ Failed to parse GPT response as JSON:", e)
    print("Raw:", review)
    exit(1)

# Step 1: Post summary
summary = review_data.get("summary", "")
comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
# Step 2: Get latest commit SHA
pr_info = requests.get(
    f"https://api.github.com/repos/{repo}/pulls/{pr_number}", headers=headers
).json()
commit_sha = pr_info.get("head", {}).get("sha")
author = pr_info.get("user", {}).get("login", "author")
payload = {
    "body": f"""**AI Code Review Summary**  
Hi @{author}, here's an automated review of your PR:

---

### 📝 Summary

{summary}

---
> **Note:** This is an AI-generated review. Please verify suggestions before applying.🤖"""
}
summary_post = requests.post(comment_url, headers=headers, json=payload)
if summary_post.status_code == 201:
    print("✅ Posted summary.")
else:
    print("❌ Failed to post summary:", summary_post.text)

if not commit_sha:
    print("❌ Could not get commit SHA.")
    exit(1)

# Step 3: Post inline comments
for c in review_data.get("comments", []):
    file_path = c["file"]
    line_number = c["line"]
    comment_text = c["comment"]
    suggestion = c.get("suggestion", "").strip()
markdown_comment = f"""**AI Suggestion**  
**Line {line_number}**:  
{comment_text}

```swift
// Suggested Change:
{c.get("suggestion", "// <your_code_suggestion_here>")}
```
"""

payload = {
    "body": markdown_comment,
    "commit_id": commit_sha,
    "path": file_path,
    "side": "RIGHT",
    "line": line_number,
}

r = requests.post(
    f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments",
    headers=headers,
    json=payload,
)

if r.status_code == 201:
    print(f"💬 Commented on {file_path}:{line_number}")
else:
    print(
        f"❌ Failed to comment on {file_path}:{line_number} - {r.status_code} - {r.text}"
    )
