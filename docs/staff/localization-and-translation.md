# Localization and Translation

## Overview

Hypha offers translations into another language or translations into your organisation's vocabulary, or a combination of both. Hypha has functionalities for adopters to localize their own version with [Weblate](https://weblate.org/) or install another translation service if they prefer. Translations could also be implemented with a text editor.

## Getting Started on Localization

Translations of Hypha can be of two kinds. Translations in to another language or translations in to you organisations vocabulary, or a combination of both.

Our team is currently using [Weblate](https://weblate.org/) to manage translations of this project. Please visit Hypha's Weblate https://hosted.weblate.org/projects/hypha/ to start the translation process. You will need a Weblate account, and take it from there. [Weblate instructions and related documentation](https://docs.weblate.org/en/latest/user/basic.html) on translation is a great introductory resource. project on Weblate to contribute. If you are experiencing issues while you are working on translations, please open an issue on \[GitHub}.

Adopters could also consider installing another translation service or apps for Linux/Windows/macOS po-files. In the **How to Edit the .po file in hypha/locale** we describe how translators can edit directly with a text editor. All translations will eventually be stored as django.po files.

## Adding a language

If your language is not listed on packaging.python.org, click the button Start new translation at the bottom of the language list and add the language you want to translate.

![400cf55f15e65d40324564503d44e959ed4d271a](https://user-images.githubusercontent.com/20019656/162624460-b3cec361-14b7-402a-b506-d688665c00f2.png)

![0cb98ef6ae05630cb9db64ccc2cc35bc16f779f4](https://user-images.githubusercontent.com/20019656/162624457-bb52fb66-eda2-48fb-8aed-1ee9e88a7d8c.png)

## How to Edit the .po file in hypha/locale

Hypha has translations to common strings propagated across other components within it by default. This lightens the burden of repetitive and multi version translation. The translation propagation can be disabled per Component configuration using Allow translation propagation in case the translations should diverge.

Hypha's list of translatable strings is available here.

In cases where text strings are not yet translatable, a quick method to find out would be search in the .po file here. As an Adopter you could also edit “hypha/locale/en” and “hypha/locale/\[your\_lang\_code]” any way you like.
