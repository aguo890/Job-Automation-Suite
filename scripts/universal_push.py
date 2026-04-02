import os
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    from openai import OpenAI
except ImportError:
    print("⚠️  Missing dependencies (openai, python-dotenv). Run 'make install'.")
    sys.exit(1)

# Configuration
# Order matters: pushing submodules first ensures the root repo sees the updated commit hash
REPOS_TO_PUSH = [
    "rendercv",
    "job-scraping-app",
    "."  # The root repo itself
]

ROOT_DIR = Path(__file__).parent.parent
DOTENV_PATH = ROOT_DIR / "job-scraping-app" / ".env"

# Load environment
if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)
else:
    print(f"⚠️  Warning: .env not found at {DOTENV_PATH}")

def run_git_cmd(args, cwd):
    return subprocess.run(
        ["git"] + args, 
        cwd=cwd, 
        capture_output=True, 
        text=True, 
        encoding='utf-8',
        errors='replace'
    )

def get_current_branch(repo_path):
    res = run_git_cmd(["branch", "--show-current"], repo_path)
    return res.stdout.strip()

def get_commit_message(diff_content):
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "wip: auto-commit (no api key)"
    
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Generate a concise Conventional Commit message (under 72 chars first line). Key details in bullets. No markdown."},
                {"role": "user", "content": f"Diff:\n{diff_context(diff_content)}"}
            ],
            temperature=0.4,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠️  AI generation failed: {e}")
        return "wip: auto-commit"

def diff_context(diff):
    if len(diff) > 10000:
        return diff[:10000] + "\n... (truncated)"
    return diff

def process_repo(repo_path_rel):
    repo_path = (ROOT_DIR / repo_path_rel).resolve()
    print(f"\n📂 Processing: {repo_path_rel if repo_path_rel != '.' else 'Root'}")
    
    if not (repo_path / ".git").exists():
        # Check if it's a submodule directory without .git (might happen if not initialized)
        if (repo_path).is_dir():
            print(f"  ⚠️  {repo_path.name} is a directory but not a git repo. Skipping.")
        else:
            print(f"  ❌ {repo_path.name} not found. Skipping.")
        return

    # 0. Branch Guardrail
    branch = get_current_branch(repo_path)
    if not branch:
        print(f"  ⚠️  Skipping: Repository is in a detached HEAD state.")
        print(f"     To push changes, cd into '{repo_path_rel}', checkout a branch (e.g., 'main'), and try again.")
        return

    print(f"  🌿 Branch: {branch}")

    # 1. Check for Uncommitted Changes
    status = run_git_cmd(["status", "--porcelain"], repo_path)
    if status.stdout.strip():
        print("  📝 Changes detected. Staging...")
        run_git_cmd(["add", "."], repo_path)
        
        # Determine Message
        diff = run_git_cmd(["diff", "--cached"], repo_path).stdout
        if not diff.strip():
            print("  ⚠️  Empty diff after add? Skipping commit.")
        else:
            msg = get_commit_message(diff)
            print(f"  🤖 Commit Msg: {msg.splitlines()[0]}...")
            
            res = run_git_cmd(["commit", "-m", msg], repo_path)
            if res.returncode == 0:
                print("  ✅ Committed.")
            else:
                # If commit failed (e.g. pre-commit hooks), we shouldn't continue to push
                print(f"  ❌ Commit failed: {res.stderr}")
                return

    # 1.5 Pull Rebase (Sync with remote to prevent non-fast-forward errors)
    print("  ⬇️  Pulling changes (rebase)...")
    pull_res = run_git_cmd(["pull", "--rebase"], repo_path)
    if pull_res.returncode != 0:
        print(f"  ⚠️  Pull rebase warning: {pull_res.stderr.strip()}")

    # 2. Check for Unpushed Commits
    status_sb = run_git_cmd(["status", "-sb"], repo_path).stdout
    if "ahead" in status_sb:
        print("  🚀 Local is ahead. Pushing...")
        push_res = run_git_cmd(["push"], repo_path)
        if push_res.returncode == 0:
            print("  ✅ Pushed!")
        else:
            print(f"  ❌ Push failed: {push_res.stderr.strip()}")
    else:
        print("  ✨ Everything up to date.")

def main():
    print("🔄 Job Automation Suite - Universal Push")
    print("========================================")
    
    for repo in REPOS_TO_PUSH:
        process_repo(repo)
    
    print("\n✅ Done.")

if __name__ == "__main__":
    main()
