# Issue tracker: GitHub

Issues for this repository live in GitHub Issues at MuZiJin701/zen-computer-marketplace. Use the gh CLI from the repository root.

## Common operations

~~~powershell
gh issue list --state open
gh issue view <number> --comments
gh issue create --title "..." --body "..."
gh issue comment <number> --body "..."
gh issue edit <number> --add-label "..."
gh issue close <number> --comment "..."
~~~

When a skill says to publish a ticket, create a GitHub issue. When it says to fetch a ticket, run gh issue view <number> --comments.

Pull requests are not a triage request surface for this repository. Do not treat external PRs as incoming feature requests unless this policy is intentionally changed.
