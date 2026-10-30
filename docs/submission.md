# Submission guide

Submissions for **THE FINAL COMMIT** are GitHub pull requests against this repository. Read [`docs/requirements.md`](requirements.md) before you start; it is the behavioral contract your branch is evaluated against.

## Rules

- **One submission per team. One shot.** There are no follow-up PRs, revisions, or re-submissions after evaluation begins.
- **PRs are never merged.** A pull request is an evaluation artifact, not a merge candidate. Do not wait for review or a merge.
- **Open only when the fix is complete.** Everything you want evaluated must be in the PR when it is opened. Among passing PRs, the earliest opened wins.
- **Work on a branch in your fork** and open the pull request against `main` in this repository.
- **Keep the branch reproducible.** A fresh clone must run using the steps in the [README](../README.md). Do not commit database files, secrets, virtual environments, or generated artifacts.
- **Do not modify the visible tests or `docs/requirements.md`.** Hidden tests run against your branch. Weakening, skipping, or deleting visible tests does not help and counts against the submission.
- **The PR description is the deliverable.** Fill in every section of the template.

## What a complete submission contains

1. **Bug inventory.** Every defect your team found, major and minor — including ones you chose not to fix. For each entry: severity, observable symptom, root cause, location (file/function), the fix, and how you verified it.
2. **Defects not fixed.** Anything you found but left alone, with the reason.
3. **Verification.** The commands you ran, the visible suite result, and a before/after reproduction for each fixed defect.

Be specific. "Fixed checkout" or a copied incident summary is not an inventory. Your description should let a reviewer connect each claimed defect to a change in the diff and to evidence that the behavior is now correct.

## How evaluation works

Your branch is checked out fresh, dependencies are installed from `requirements.txt`, and hidden API tests exercise the contract in `docs/requirements.md`. A submission passes when every hidden test passes.

Passing PRs are ranked by when they were opened; the earliest complete, passing submission wins, and the next one is runner-up. Because the PR is never merged, the branch itself is what gets evaluated — open it when it is ready.
