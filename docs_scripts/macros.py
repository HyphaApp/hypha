from pathlib import Path


def define_env(env):
    # `extra` is merged into template variables only after this runs,
    # so read it off the config instead of `env.variables`.
    versions = env.variables.get("versions") or env.conf["extra"]["versions"]

    versions["python"]["version"] = versions["python"]["version"] or (
        Path(".python-version").read_text().strip()
    )
    versions["node"]["version"] = versions["node"]["version"] or (
        Path(".nvmrc").read_text().strip().lstrip("v")
    )

    env.variables["versions"] = versions
