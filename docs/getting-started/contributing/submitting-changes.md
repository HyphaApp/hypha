# Submitting Changes

We use pull requests for all changes. No commits are done directly in to the main branches. The "master" branch is protected and only maintainers can merge to it.

1. **Use descriptive branch names** - We commonly use `fix/*`, `enhancement/*`, `feature/*`, `bug/*` and `updates/*` as base for the branch names. A good idea is to include the GitHub issue number in the format "`*/gh-1234-*`".

2. **Use descriptive commit messages** - Write it so other developers, and your future self, can understand what was changes and why.

3. **Rebase your branch before creating the PR** - A rebase makes sure the PR is up to date and has no merge conflicts. Please do a rebase and not just a merge, this gives a clean and readable commit history.

4. **Link the PR to the corresponding issue** - A common way is to add "Fixes \#1234" at the top of the PR description. See [Linking a pull request to an issue](https://help.github.com/en/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword)

5. **Add a reviewer** - If nothing else has been agreed upon add Fredrik Jonsson [@frjo](https://github.com/frjo).

## Git command examples

### Creating a new branch from master

First check out master and do a git pull ot get all the latest updates.

Then create a new branch and do a checkout of it.

```shell
git checkout master
git pull
git checkout -b fix/gh-1234-fixing-thing-a
```

### Adding commits

```shell
git add
git commit -m "A good commit message."
```

### Pushing branch first time to GitHub

First make sure we are in the correct branch. Then push the branch to origin, i.e. GitHub in this case.

(Pushing to `HEAD` is equivalent to pushing to a remote branch having the same name as your current branch.)

```shell
git checkout fix/gh-1234-fixing-thing-a
git push -u origin HEAD
```

The message in the Terminal will contain the URL to create an PR. On most systems you can Command/CTRL click that to open it directly in your default browser.

### Rebase branch if needed

Checkout master and update it. Checkout the branch you are working on and issue the command to rebase it from master. If that resulted in any changes you will then need to do a force push to GitHub.

```shell
git checkout master
git pull
git checkout fix/gh-1234-fixing-thing-a
git rebase master
git push --force
```

Read more about [Git rebase](https://www.atlassian.com/git/tutorials/rewriting-history/git-rebase).

