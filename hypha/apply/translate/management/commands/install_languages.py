import argparse
from typing import List

import argostranslate.package
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Delete all drafts that haven't been modified in the specified time (in days)"
    )

    available_packages = argostranslate.package.get_available_packages()
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
                self.available_packages,
            ),
            None,
        )

        if not package:
            raise argparse.ArgumentTypeError(
                f'Package "{value}" is not available for install'
            )

        return package

    def add_arguments(self, parser):
        parser.add_argument(
            "languages",
            action="store",
            nargs="*",
            type=self.__validate_language,
            help='Language packages to install in the format of "<from language>_<to language>" in ISO 639 format',
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
            help="Install all available language packages",
            required=False,
        )

    def __print_package_list(self, packages: List[argostranslate.package.Package]):
        for package in packages:
            self.stdout.write(f"{package.from_name} ➜ {package.to_name}")

    def handle(self, *args, **options):
        interactive = options["interactive"]
        packages = options["languages"]
        verbosity = options["verbosity"]
        all = options["all"]

        # Require either languages or "--all" to be specified
        if not bool(packages) ^ bool(all):
            raise argparse.ArgumentTypeError("A language selection must be specified")

        if all:
            packages = self.available_packages

        existing_packages = [
            lang for lang in packages if lang in self.installed_packages
        ]
        pending_packages = [
            lang for lang in packages if lang not in self.installed_packages
        ]

        if existing_packages:
            if verbosity > 1:
                self.stdout.write(
                    f"The following package{'s are' if len(existing_packages) > 1 else ' is'} already installed:"
                )
                self.__print_package_list(existing_packages)
            elif (
                not pending_packages
            ):  # Only notify the user if no packages will be installed
                self.stdout.write(
                    f"The specified package{'s are' if len(existing_packages) > 1 else ' is'} already installed."
                )

        if not pending_packages:
            return

        if pending_packages:
            if verbosity > 1:
                self.stdout.write(
                    f"The following package{'s' if len(pending_packages) > 1 else ''} will be installed:"
                )
                self.__print_package_list(pending_packages)
            elif (
                interactive
            ):  # Only log what will be installed if prompting the user to confirm
                self.stdout.write(
                    f"{len(pending_packages)} package{'s' if len(pending_packages) > 1 else ''} will be installed."
                )

            if interactive:
                confirm = input(
                    "Are you sure you want to do this?\n\nType 'yes' to continue, or 'no' to cancel: "
                )
            else:
                confirm = "yes"

        if confirm == "yes":
            for package in pending_packages:
                argostranslate.package.install_from_path(package.download())

            successful_installs = len(
                argostranslate.package.get_installed_packages()
            ) - len(self.installed_packages)

            success_msg = f"{successful_installs} new package{'s' if successful_installs > 1 else ''} installed"

            if existing_packages:
                success_msg = f"{success_msg}, while {len(existing_packages)} package{'s were' if len(existing_packages) > 1 else ' was'} already installed."
            else:
                success_msg = f"{success_msg}."

            self.stdout.write(success_msg)
        else:
            self.stdout.write("Installation cancelled.")
