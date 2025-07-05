# Machine translations

Hypha has the ability to utilize [argostranslate](https://github.com/argosopentech/argos-translate) for machine translations of submitted application content. This is disabled by default and the dependencies are not installed to prevent unneeded bloat due to [PyTorch](https://pytorch.org/)'s large language models.


## Installing dependencies

As referenced in the [production deployment guide](../deployment/production/stand-alone.md), it is required to install the dependencies needed for machine translation dependencies via

```bash
python3 -m pip install -r requirements/translate.txt
```

or, if you are on a platform that does not support GPU processing:

```bash
python3 -m pip install -r requirements/translate-cpu.txt
```


This requirements file will specifically attempt to install the CPU version of [PyTorch](https://pytorch.org/) if available on the detected platform to play better with heroku (doesn't support GPU processing) and to minimize package bloat (CPU package is ~300MB less than the normal GPU). Depending on your use case, you may want to adjust this.


## Installing languages

Argostranslate handles translations via its own packages—e.g., Arabic → English translation is one package, while English → Arabic is another.

You can install/uninstall these packages using the management commands `install_languages` and `uninstall_languages`, respectively. The format for specifying a package is `<from language code>_<to language code>`. For example, to install the Arabic → English and French → English packages:

```bash
python3 manage.py install_languages ar_en fr_en
```

### Additional options

The `install_languages` command supports several options for flexibility:

- **Install all available packages:**
  ```bash
  python3 manage.py install_languages --all
  ```
  > ⚠️ This may install many packages and consume significant disk space.

- **Interactively select packages:**
  ```bash
  python3 manage.py install_languages --select
  ```
  This will present a numbered list of available language packages for you to choose from.

- **Skip confirmation prompts:**
  ```bash
  python3 manage.py install_languages ar_en --noinput
  ```
  This will install the specified packages without asking for confirmation.

You can combine these options as needed. For example, to interactively select packages and skip confirmation:

```bash
python3 manage.py install_languages --select --noinput
```

## Enabling on the system

To enable machine translations on an instance, the proper configuration variables need to be set. These can be found in the [configuration options](configuration.md#hypha-custom-settings)
