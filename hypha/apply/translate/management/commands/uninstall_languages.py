import argparse
from typing import List

import argostranslate.package
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Delete all drafts that haven't been modified in the specified time (in days)"
    )

    installed_packages = argostranslate.package.get_installed_packages()

    def __validate_language(self, value):
        """Used to validate `from_to_language` argument"""
        try:
            from_code, to_code = value.split("_")
        except ValueError:
            raise argparse.ArgumentTypeError(
                f'Invalid language package "{value}", expected "<from language>_<to language>" in ISO 639 format'
            ) from None

        package = next(
            filter(
                lambda x: x.from_code == from_code and x.to_code == to_code,
                self.installed_packages,
            ),
            None,
        )

        if not package:
            raise argparse.ArgumentTypeError(f'Package "{value}" is not installed')

        return package

    def add_arguments(self, parser):
        parser.add_argument(
            "languages",
            action="store",
            nargs="*",
            type=self.__validate_language,
            help='Language packages to uninstall in the format of "<from language>_<to language>" in ISO 639 format',
        )

        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do not prompt the user for confirmation",
            required=False,
        )

        parser.add_argument(
            "--all",
            action="store_true",
            help="Uninstall all installed language packages",
            required=False,
        )

    def __print_package_list(self, packages: List[argostranslate.package.Package]):
        for package in packages:
            self.stdout.write(f"{package.from_name} ➜ {package.to_name}")

    def handle(self, *args, **options):
        interactive = options["interactive"]
        packages = options["languages"]
        verbosity = options["verbosity"]

        # Require either languages or "--all" to be specified
        if not bool(packages) ^ bool(all):
            raise argparse.ArgumentTypeError("A language selection must be specified")

        if all:
            packages = self.installed_packages

        if verbosity > 1:
            self.stdout.write(
                f"The following package{'s' if len(packages) > 1 else ''} will be uninstalled:"
            )
            self.__print_package_list(packages)
        elif (
            interactive
        ):  # Only log what will be uninstalled if prompting the user to confirm
            self.stdout.write(
                f"{len(packages)} package{'s' if len(packages) > 1 else ''} will be uninstalled."
            )

        if interactive:
            confirm = input(
                "Are you sure you want to do this?\n\nType 'yes' to continue, or 'no' to cancel: "
            )
        else:
            confirm = "yes"

        if confirm == "yes":
            for package in packages:
                argostranslate.package.uninstall(package)

            successful_uninstalls = len(self.installed_packages) - len(
                argostranslate.package.get_installed_packages()
            )

            self.stdout.write(
                f"{successful_uninstalls} package{'s' if successful_uninstalls > 1 else ''} uninstalled."
            )
        else:
            self.stdout.write("Removal cancelled.")
