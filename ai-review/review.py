import os
from openai import OpenAI
import requests
import json
import re
from typing import Dict, List, Optional, Tuple

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


def get_line_numbers_from_patch(patch: str) -> List[int]:
    """
    Extract line numbers where comments can be placed.
    Includes added lines and context lines around changes.
    """
    line_numbers = []
    current_line = 0
    in_change_context = False
    context_lines = []

    lines = patch.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("@@"):
            # Parse hunk header like @@ -1,4 +1,6 @@
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if match:
                current_line = int(match.group(1)) - 1
            in_change_context = True
            context_lines = []
        elif line.startswith("+"):
            # Added line
            current_line += 1
            line_numbers.append(current_line)
            in_change_context = True
        elif line.startswith("-"):
            # Removed line - add context lines around it for commenting
            if in_change_context:
                # Add previous context lines
                line_numbers.extend(context_lines)
                context_lines = []
                # Add next context line if available
                next_line_idx = i + 1
                if next_line_idx < len(lines) and lines[next_line_idx].startswith(" "):
                    current_line += (
                        1  # This will be incremented below for the context line
                    )
        elif line.startswith(" "):
            # Context line
            current_line += 1
            if in_change_context:
                context_lines.append(current_line)
                # Keep only last 2 context lines to avoid too many comments
                context_lines = context_lines[-2:]

    # Remove duplicates and sort
    return sorted(list(set(line_numbers)))


def create_single_comment(
    file_path: str,
    line_number: int,
    comment_text: str,
    commit_sha: str,
    suggestion: str = "",
    severity: str = "minor",
) -> bool:
    """
    Create a single inline comment using GitHub's single comment API.
    This is simpler than the review API and uses line numbers directly.
    """
    severity_emoji = {"critical": "🚨", "major": "⚠️", "minor": "💡", "style": "🎨"}.get(
        severity, "💡"
    )

    markdown_comment = f"""{severity_emoji} **{severity.title()} Issue**

{comment_text}"""

    if suggestion:
        markdown_comment += f"""

**Suggested fix:**
```swift
{suggestion}
```"""

    # Use the single comment API instead of review API
    comment_payload = {
        "body": markdown_comment,
        "commit_id": commit_sha,
        "path": file_path,
        "line": line_number,
        "side": "RIGHT",  # Comment on the new version of the file
    }

    response = requests.post(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}/comments",
        headers=headers,
        json=comment_payload,
    )

    return response.status_code in [201, 200]


def get_file_content(file_path: str, ref: str = None) -> Optional[str]:
    """Fetch the full content of a file from GitHub."""
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    if ref:
        url += f"?ref={ref}"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content_data = response.json()
        if content_data.get("encoding") == "base64":
            import base64

            return base64.b64decode(content_data["content"]).decode("utf-8")
    return None


def analyze_full_file_context(
    files: List[dict], pr_info: dict
) -> Tuple[str, Dict[str, List[int]]]:
    """
    Analyze files with full context and extract valid line numbers for comments.
    Returns the combined diff text and valid line numbers for each file.
    """
    diffs = ""
    file_line_numbers = {}

    for file in files:
        filename = file["filename"]

        # Skip non-Swift files and certain file types
        if not (
            filename.endswith((".swift", ".h", ".m"))
            or any(
                filename.endswith(ext) for ext in [".kt", ".java", ".py", ".js", ".ts"]
            )
        ):
            continue

        patch = file.get("patch", "")
        if not patch:
            continue

        # Get valid line numbers for this file
        file_line_numbers[filename] = get_line_numbers_from_patch(patch)

        # Get full file content for better context
        file_content = get_file_content(filename, pr_info.get("head", {}).get("sha"))

        # Add file info to diff with full context
        diffs += f"\n---\nFile: {filename}\n"
        diffs += f"Status: {file.get('status', 'modified')}\n"
        diffs += f"Changes: +{file.get('additions', 0)} -{file.get('deletions', 0)}\n"
        diffs += f"Valid comment lines: {file_line_numbers[filename]}\n"
        diffs += f"\nPatch:\n{patch}\n"

        # If we have the full file content, add relevant context
        if (
            file_content and len(file_content.split("\n")) < 200
        ):  # Only for smaller files
            diffs += f"\nFull file content for context:\n{file_content}\n"

    return diffs, file_line_numbers


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
    print(f"• {f['filename']} (+{f.get('additions', 0)} -{f.get('deletions', 0)})")

# Get PR info for commit SHA
pr_info = requests.get(
    f"https://api.github.com/repos/{repo}/pulls/{pr_number}", headers=headers
).json()

diffs, file_line_numbers = analyze_full_file_context(files, pr_info)

if not diffs:
    print("⚠️ No relevant file changes detected.")
    exit(0)

# Enhanced prompt with better instructions
prompt = f"""You're an expert code reviewer. Analyze the following code diff and return feedback in this **JSON format**:

{{
  "summary": "<brief summary of overall issues and improvements>",
  "comments": [
    {{
      "file": "<filename>",
      "line": <exact_line_number_from_patch>,
      "comment": "<explanation of why this line needs improvement>",
      "suggestion": "<code suggestion to resolve the issue>",
      "severity": "<critical|major|minor|style>"
    }}
  ]
}}

🔍 **IMPORTANT**: 
- The `line` field must be the EXACT line number where the issue occurs in the NEW version of the file (after changes)
- Look at the patch carefully - lines starting with '+' are additions, lines with '-' are deletions
- Focus on lines that are actually changed (+ or modified context)
- Report ALL issues you find, don't skip any

🔍 Review focus areas:
- 🚫 **Critical**: Force unwrapping (`!`), memory leaks, crash-prone code
- 🧱 **Major**: SwiftUI/architecture violations, business logic in views, missing error handling
- 🧹 **Major**: MVVM violations, non-testable code, performance issues
- 🧼 **Minor**: Code style, naming conventions, unused code
- 🐛 **Minor**: Typos in names, strings, comments
- 📦 **Style**: Access control, formatting, consistency

**For Swift/iOS specifically:**
- Avoid force unwrapping - use optional binding or nil coalescing
- SwiftUI views should be declarative, move logic to ViewModels
- Follow Swift naming conventions (camelCase, PascalCase)
- Use proper access control (private, internal, public)
- Ensure thread safety for UI updates
- Check for retain cycles in closures
- Warn about unused code (e.g., variables, imports, functions)
- Detect typos in:
  • Enum case names and raw values
  • String literals (especially user-facing)
  • Function/method names
  • Class, struct, protocol names
  • Variable/constant names
  • Documentation and inline comments


**Be thorough** - examine every changed line and surrounding context. Don't miss issues.

Here is the code diff to review:
{diffs}
"""

print("🧠 Sending diff to GPT-4...")

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert code reviewer. Be thorough and examine every line of changed code. Don't skip any issues you find.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,  # Lower temperature for more consistent output
        max_tokens=4000,
    )

    review = response.choices[0].message.content.strip()
except Exception as e:
    print(f"❌ Failed to get GPT response: {e}")
    exit(1)

# Clean up the response
if review.startswith("```json"):
    review = review.removeprefix("```json").strip()
if review.startswith("```"):
    review = review.removeprefix("```").strip()
if review.endswith("```"):
    review = review.removesuffix("```").strip()

try:
    review_data = json.loads(review)
except Exception as e:
    print("❌ Failed to parse GPT response as JSON:", e)
    print("Raw response:", review)
    exit(1)

print(f"📊 Found {len(review_data.get('comments', []))} comments to post")

# Get commit SHA and author info
commit_sha = pr_info.get("head", {}).get("sha")
author = pr_info.get("user", {}).get("login", "author")

if not commit_sha:
    print("❌ Could not get commit SHA.")
    exit(1)

# Step 1: Post summary comment
summary = review_data.get("summary", "No summary provided")
comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

# Check if summary already exists
existing_comments = requests.get(comment_url, headers=headers).json()
ai_summary_exists = any(
    "AI Code Review Summary" in c.get("body", "")
    and c.get("user", {}).get("login") == "github-actions[bot]"
    for c in existing_comments
)

if not ai_summary_exists:
    severity_counts = {}
    for comment in review_data.get("comments", []):
        severity = comment.get("severity", "minor")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    severity_summary = " | ".join(
        [f"{sev.title()}: {count}" for sev, count in severity_counts.items()]
    )

    payload = {
        "body": f"""## 🤖 AI Code Review Summary

Hi @{author}! Here's an automated review of your PR:

### 📊 Issues Found
{severity_summary if severity_counts else "No issues found"}

### 📝 Summary
{summary}

---
*This is an AI-generated review. Please verify suggestions before applying them.*"""
    }

    summary_response = requests.post(comment_url, headers=headers, json=payload)
    if summary_response.status_code == 201:
        print("✅ Posted summary comment")
    else:
        print(
            f"❌ Failed to post summary: {summary_response.status_code} - {summary_response.text}"
        )

# Step 2: Post inline comments using single comment API
successful_comments = 0
failed_comments = 0

for comment_data in review_data.get("comments", []):
    file_path = comment_data["file"]
    line_number = comment_data["line"]
    comment_text = comment_data["comment"]
    suggestion = comment_data.get("suggestion", "").strip()
    severity = comment_data.get("severity", "minor")

    # Check if this line number is valid for commenting
    if file_path not in file_line_numbers:
        print(f"⚠️ No line numbers found for {file_path}")
        failed_comments += 1
        continue

    valid_lines = file_line_numbers[file_path]
    if line_number not in valid_lines:
        print(f"⚠️ Line {line_number} not valid for commenting in {file_path}")
        print(f"   Valid lines: {valid_lines}")
        # Try to find the closest valid line
        if valid_lines:
            closest_line = min(valid_lines, key=lambda x: abs(x - line_number))
            print(
                f"📍 Using closest valid line {closest_line} instead of {line_number}"
            )
            line_number = closest_line
        else:
            failed_comments += 1
            continue

    # Create the comment using single comment API
    if create_single_comment(
        file_path, line_number, comment_text, commit_sha, suggestion, severity
    ):
        successful_comments += 1
        print(f"✅ Posted comment on {file_path}:{line_number}")
    else:
        failed_comments += 1
        print(f"❌ Failed to post comment on {file_path}:{line_number}")

print(f"📝 Posted {successful_comments} comments, {failed_comments} failed")

print("🎉 Review process completed!")
