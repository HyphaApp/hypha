# Hypha developer tips

## Git config

To avoid spurious merge commits use a rebase workflow when appropriate.

Set this to always use rebase when pulling in updates in a branch.

```shell
git config --global branch.autosetuprebase always
```

When updating a feature branch with new commits from the main branch use `rebase` and not `merge`

```shell
git switch feature-branch-name
git fetch origin
git rebase origin/main
```

## Postgres snapshots/restore

Hypha dev requirements contain the [dslr](https://github.com/mixxorz/DSLR) tool. Use this for fast snapshots and restores of the postgres database.

Perfekt when testing migrations and other times when you need to reset the database or switch between databases.

Take a snapshot, you can have as many as you like.

```shell
dslr snapshot name-of-the-snapshot
```

Restore the snapshot.

```shell
dslr restore name-of-the-snapshot
```

Delete a snapshot you no longer need.

```shell
dslr delete name-of-the-snapshot
```

List all your snapshots:

```shell
dslr list
```

## Commands in Makefile

This is the one stop place to find commands for runiing test, build resources and docs, linting and code style checks/fixes.

## Coding style and linting in pre-commit hook

Hypha's coding style is enforced by ruff and prettier and comes pre-configured with prettier.

Install pre-commit to auto-format the code before each commit:

```shell
pre-commit install
```

## Editor extensions

If you editor does not a Language Server Protocol (LSP) preinstalled make sure to add the plugin for it. Then add "LSP-ruff" for a fast Python linter and code transformation tool.

Your editor most likely have plugins for the other languages Hypha uses as well, css/scss, yaml and html. We recoment to install them as well.

