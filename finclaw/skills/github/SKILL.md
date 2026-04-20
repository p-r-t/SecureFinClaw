---
name: github
description: >
  Interact with GitHub repositories using the `gh` CLI. Use this skill for: creating or reviewing
  pull requests, checking CI/CD pipeline status, viewing workflow run logs, listing or searching
  issues, viewing/cloning repos, and making GitHub API queries. Trigger for phrases like "check
  the CI", "is the PR green?", "open an issue", "list failing tests", "show me recent commits", or
  any GitHub-related action.
metadata: {"finclaw":{"emoji":"🐙","requires":{"bins":["gh"]},"install":[{"id":"brew","kind":"brew","formula":"gh","bins":["gh"],"label":"Install GitHub CLI (brew)"},{"id":"apt","kind":"apt","package":"gh","bins":["gh"],"label":"Install GitHub CLI (apt)"}]}}
---

# GitHub Skill

Use the `gh` CLI to interact with GitHub. Always include `--repo owner/repo` when outside a git
directory, or pass URLs directly. Check auth first if commands fail unexpectedly: `gh auth status`.

## Pull Requests

```bash
# List open PRs
gh pr list --repo owner/repo

# Check CI status on a PR
gh pr checks 55 --repo owner/repo

# Review PR diff
gh pr diff 55 --repo owner/repo

# Merge (squash)
gh pr merge 55 --repo owner/repo --squash
```

## CI / Workflow Runs

```bash
# List recent runs
gh run list --repo owner/repo --limit 10

# View run summary (shows which jobs failed)
gh run view <run-id> --repo owner/repo

# Stream logs for failed steps only
gh run view <run-id> --repo owner/repo --log-failed
```

## Issues

```bash
# List open issues (with label filter)
gh issue list --repo owner/repo --label "bug" --limit 20

# Create an issue
gh issue create --repo owner/repo --title "Title" --body "Body" --label "bug"

# Close an issue
gh issue close <number> --repo owner/repo
```

## Repos

```bash
# Clone
gh repo clone owner/repo

# View repo details
gh repo view owner/repo

# List releases
gh release list --repo owner/repo --limit 5
```

## Advanced API Queries

```bash
# Fetch PR with specific fields
gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'

# Search issues across org
gh api "search/issues?q=repo:owner/repo+is:issue+is:open+label:bug" --jq '.items[].title'

# Get workflow IDs
gh api repos/owner/repo/actions/workflows --jq '.workflows[] | "\(.id): \(.name)"'
```

## JSON + jq

Most commands support `--json field1,field2` and `--jq` for filtering:

```bash
gh issue list --repo owner/repo --json number,title,labels \
  --jq '.[] | "\(.number): \(.title)"'

gh run list --repo owner/repo --json databaseId,status,conclusion \
  --jq '.[] | select(.conclusion=="failure") | .databaseId'
```

## Tips

- `gh auth status` — verify authentication before debugging errors
- `gh config set pager cat` — disable paging if output is truncated
- All commands support `--help` for full option reference
