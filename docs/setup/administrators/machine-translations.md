# Machine translations

Hypha has the ability to utilize [argostranslate](https://github.com/argosopentech/argos-translate) for machine translations of submitted application content. This is disabled by default and the dependencies are not installed to prevent unneeded bloat due to [PyTorch](https://pytorch.org/)'s large language models.


## Installing dependencies

As referenced in the [production deployment guide](../deployment/production/stand-alone.md), it is required to install the dependencies needed for machine translation dependencies via

```bash
python3 -m pip install -r requirements/translate.txt
```

This requirements file will specifically attempt to install the CPU version of [PyTorch](https://pytorch.org/) if available on the detected platform to play better with heroku (doesn't support GPU processing) and to minimize package bloat (CPU package is ~300MB less than the normal GPU). Depending on your use case, you may want to adjust this.


## Installing languages

Argostranslate handles translations via it's own packages - ie. Arabic -> English translation would be one package, while English -> Arabic would be another.

Installing/uninstalling these packages can be done with the management commands `install_languages`/`uninstall_languages` respectively, utilizing the format of <from language code>_<to language code>. For example, installing the Arabic -> English & French -> English packages would look like:

```bash
python3 manage.py install_languages ar_en fr_en
```

## Enabling on the system

To enable machine translations on an instance, the proper configuration variables need to be set. These can be found in the [configuration options](configuration.md#hypha-custom-settings)
