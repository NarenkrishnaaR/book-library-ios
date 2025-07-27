import os
from openai import OpenAI
import requests
import json

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
- 🚫 Avoid force unwrapping (`!`) — instead, use optional binding (`if let`, `guard let`) or nil coalescing (`??`)
- 🧱 Follow SwiftUI best practices:
  • Views should remain declarative and free of business logic
  • Avoid embedding conditional logic or side effects in the view body
  • Use computed properties or ViewModels to handle state and formatting
- 🧹 Apply MVVM principles — move formatting, business logic, and data transformations to ViewModel
- 🧼 Maintain clean, readable, and idiomatic Swift code
- 🧠 Follow Swift naming conventions:
  • Descriptive, camelCase for variables and functions
  • PascalCase for types (structs, classes, enums)
  • Avoid abbreviations unless well-known
- 📦 Use access control wisely (`private`, `internal`, `public`) to limit scope and improve encapsulation
- ♻️ Reuse UI components and modifiers where possible to reduce duplication
- 🧪 Ensure testability — logic should be easy to write unit tests for
- 🐛 Detect typos in:
  • Enum case names and raw values
  • String literals (especially user-facing)
  • Function/method names
  • Class, struct, protocol names
  • Variable/constant names
  • Documentation and inline comments
- ⚠️ Warn about unused code (e.g., variables, imports, functions)
- 📉 Highlight performance issues (e.g., complex views inside `body`, redundant modifiers)
- ✅ Ensure consistent formatting and indentation

Return only the JSON object. Avoid explanations outside the JSON.

Here is the code diff to review:
{diffs}
"""
print("🧠 Sending diff to GPT-4...")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an expert iOS code reviewer."},
        {"role": "user", "content": prompt},
    ],
)

review = response.choices[0].message.content.strip()
# 🔍 Remove Markdown formatting if GPT returns code block
if review.startswith("```json"):
    review = review.removeprefix("```json").strip()
if review.startswith("```"):  # fallback in case only triple-backtick is used
    review = review.removeprefix("```").strip()
if review.endswith("```"):
    review = review.removesuffix("```").strip()

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
review_comments = []
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
review_comments.append({
        "path": file_path,
        "position": 1,  # TEMP placeholder, GitHub requires a valid position
        "body": markdown_comment
    })

# Filter only valid positions (NOTE: better approach is to map line to position from patch)
if not review_comments:
    print("⚠️ No valid comments to post.")
    exit(0)

# Create review
review_payload = {
    "commit_id": commit_sha,
    "body": "AI Code Review Suggestions",
    "event": "COMMENT",
    "comments": review_comments
}

review_response = requests.post(
    f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews",
    headers=headers,
    json=review_payload
)

if review_response.status_code == 200:
    print("✅ Posted review with inline comments.")
else:
    print(
        f"❌ Failed to comment on {file_path}:{line_number} - {review_response.status_code} - {review_response.text}"
    )
