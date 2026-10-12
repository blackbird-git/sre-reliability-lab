# GitHub Publishing and CI Lab

## Repository

Published the local repository to:

https://github.com/blackbird-git/sre-reliability-lab

Reviewed tracked files before publishing.

HTTPS password authentication failed because GitHub does not accept
account passwords for Git operations. Signed in through GitHub CLI's
browser login and configured Git authentication.

## Git workflow: commit, push, PR, and merge

These operations have different purposes:

| Operation | Purpose |
|---|---|
| Commit | Record changes in local Git history |
| Push | Upload commits and update a branch on GitHub |
| Pull request | Propose and review changes between branches |
| Merge | Integrate branch changes into another branch |
| Pull | Bring remote changes into the local repository |

Pushing a feature branch does not merge it into main.

Our workflow:

1. Create a local branch.
2. Make changes, review them, and commit locally.
3. Push the branch to GitHub.
4. Open a PR targeting main.
5. Review changes and CI results.
6. Merge the PR.
7. Update local main with git pull --ff-only.

Additional commits pushed to the same branch update its existing PR.

A local merge followed by pushing main is also possible if repository
rules allow it. A PR provides a shared review process.

## CI workflow

Created `.github/workflows/ci.yaml`.

The workflow runs on pushes and pull requests using a GitHub-hosted
Ubuntu runner.

Steps:

1. Check out the repository.
2. Set up Python 3.14.
3. Install dependencies from requirements.txt.
4. Run python -m pytest -v.
5. Build the Docker image.

The runner is separate from my local machine. It receives tracked repository
files, not my local virtual environment, so it must install dependencies.

`uses` invokes a reusable action.
`run` executes a shell command.

Tests and the Docker build passed on the feature branch and its PR.
Merged the workflow into main through GitHub.

This is CI: automated validation. It does not deploy the application,
publish the image, or verify container startup.

## Deliberate regression

Created branch lab/ci-regression.

Changed the APP_READY fallback from "true" to "false" without changing
the tests, then committed and pushed.

CI reported:

- test_ready_by_default: FAILED
- test_ready_if_false: PASSED
- test_healthz: PASSED
- pytest exit code: 1

The default test removes APP_READY, calls /readyz, and expects HTTP 200.
The altered application returned 503 instead.

A failed test step prevents the later Docker build step from running
under this workflow's default behavior.

## Correction

Restored the fallback to "true", verified tests locally, and pushed
a correction on the same branch.

The new CI run passed tests and built the image successfully.

The main branch was unaffected by the regression exercise.

## Operational takeaway

CI detects violations of tested behavior on a separate machine.
Passing checks do not prove all behavior is correct.

Repository protection rules are needed to require passing checks
before merging; a red CI result alone is not necessarily a merge block.