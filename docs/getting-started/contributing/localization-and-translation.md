# Translate Hypha in to your own language

There are two resons organisations make use of translations. They need Hypha in another language, like Spanish or Chinese. Another common need is to translate Hypha to suit a organisations vocabulary.  A combination of both works as well of course.

Our team is currently using [Weblate](https://weblate.org/) to manage translations of this project. Please visit Hypha's Weblate https://hosted.weblate.org/projects/hypha/ to start the translation process. You will need a Weblate account, and take it from there. [Weblate instructions and related documentation](https://docs.weblate.org/en/latest/user/basic.html) on translation is a great introductory resource. project on Weblate to contribute. If you are experiencing issues while you are working on translations, please open an issue on \[GitHub}.

There is no requirement on using Weblate. An organisation can use any tool or service they see fit to translate the .po file.

## Adding a language on Weblate

If your language is not listed on packaging.python.org, click the button Start new translation at the bottom of the language list and add the language you want to translate.

![400cf55f15e65d40324564503d44e959ed4d271a](https://user-images.githubusercontent.com/20019656/162624460-b3cec361-14b7-402a-b506-d688665c00f2.png)

![0cb98ef6ae05630cb9db64ccc2cc35bc16f779f4](https://user-images.githubusercontent.com/20019656/162624457-bb52fb66-eda2-48fb-8aed-1ee9e88a7d8c.png)

## Find the translation files in Hypha

This is the "template" that gets loaded in to translations services/apps.

`hypha/locale/django.pot`

This is the example English .po file.

`hypha/locale/en/LC_MESSAGES/django.po`

## Django commands

To generate updated .po and .pot files for English (en) we use the following command:

```shell
python manage.py makemessages --locale en --ignore .venv --keep-pot
```

This is done fairly regular to keep the translations up to date.

You can use this command to generate a translation template for any language. Even if you are using weblate or another service to create the .po files this is a good way to start since you get the directory structure.

```shell
python manage.py makemessages --locale sv-SE --ignore .venv
```

This will create `hypha/locale/sv_SE/LC_MESSAGES/django.po`

It is the `django.po` file that contain all the translations. You can start to translate all the string in this file.

If you already have a translated version, replace that files with the generated one. Make sure the name and path stay the same.

It is then nessesery to complile the .po files in to binary .mo files. This command takes care of that.

```shell
python manage.py compilemessages --ignore .venv
```

If you update the .po files you will need to rerun the above command.

Set `LANGUAGE_CODE = "sv-SE"`

Restart your server to make it pick up the new translations files.
