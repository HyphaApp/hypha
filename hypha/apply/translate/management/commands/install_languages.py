import argparse
from typing import List

import argostranslate.package
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Django management command to install language packages for offline translation support.

    This command provides multiple ways to install Argos Translate language packages:
    - Install specific packages by specifying language codes
    - Install all available packages with --all flag
    - Interactively select packages with --select flag

    Language packages are specified in the format "<from_language>_<to_language>"
    using ISO 639 language codes (e.g., "en_es" for English to Spanish).
    """

    help = "Install language packages for offline translation support"

    available_packages = argostranslate.package.get_available_packages()
    installed_packages = argostranslate.package.get_installed_packages()

    def __validate_language(self, value):
        """
        Validate language package format and availability.

        Args:
            value (str): Language package string in format "<from_code>_<to_code>"

        Returns:
            argostranslate.package.Package: The validated package object

        Raises:
            argparse.ArgumentTypeError: If format is invalid or package not available
        """
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
        """
        Add command line arguments for the management command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to add arguments to
        """
        parser.add_argument(
            "languages",
            action="store",
            nargs="*",
            type=self.__validate_language,
            help=(
                'Language packages to install in the format "<from_language>_<to_language>" '
                'using ISO 639 language codes. Examples: "en_es" (English to Spanish), '
                '"fr_en" (French to English). Multiple packages can be specified.'
            ),
        )

        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Skip confirmation prompts and install packages automatically",
            required=False,
        )

        parser.add_argument(
            "--all",
            action="store_true",
            help="Install all available language packages (use with caution - this may install many packages)",
            required=False,
        )

        parser.add_argument(
            "--select",
            action="store_true",
            help="Interactively select language packages from a numbered list of available packages",
            required=False,
        )

    def __print_package_list(self, packages: List[argostranslate.package.Package]):
        """
        Print a formatted list of language packages.

        Args:
            packages (List[argostranslate.package.Package]): List of packages to display
        """
        for package in packages:
            self.stdout.write(f"{package.from_name} ➜ {package.to_name}")

    def __select_packages(self):
        """
        Interactively select packages from available packages.

        Returns:
            List[argostranslate.package.Package]: List of selected packages

        Raises:
            argparse.ArgumentTypeError: If user input is invalid
        """
        self.stdout.write("Available language packages:")
        for i, package in enumerate(self.available_packages):
            self.stdout.write(f"{i + 1}. {package.from_name} ➜ {package.to_name}")

        selections = input("\nEnter package numbers (comma-separated) to install: ")
        try:
            indices = [int(x.strip()) - 1 for x in selections.split(",")]
            return [
                self.available_packages[i]
                for i in indices
                if 0 <= i < len(self.available_packages)
            ]
        except (ValueError, IndexError) as e:
            raise argparse.ArgumentTypeError("Invalid package selection") from e

    def handle(self, *args, **options):
        """
        Main command execution logic.

        Handles the installation of language packages based on the provided options.
        Supports three modes of operation:
        1. Install specific packages by language codes
        2. Install all available packages with --all
        3. Interactive selection with --select

        Args:
            *args: Variable length argument list (unused)
            **options: Keyword arguments containing parsed command line options
        """
        interactive = options["interactive"]
        packages = options["languages"]
        verbosity = options["verbosity"]
        all = options["all"]
        select = options["select"]

        # Determine which packages to install based on command options
        if select:
            packages = self.__select_packages()
        elif not bool(packages) ^ bool(all):
            raise argparse.ArgumentTypeError("A language selection must be specified")

        if all:
            packages = self.available_packages

        # Separate packages into already installed and pending installation
        existing_packages = [
            lang for lang in packages if lang in self.installed_packages
        ]
        pending_packages = [
            lang for lang in packages if lang not in self.installed_packages
        ]

        # Report on packages that are already installed
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

        # Exit early if no packages need installation
        if not pending_packages:
            return

        # Handle confirmation and installation of pending packages
        confirm = "no"
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

            # Get user confirmation if in interactive mode
            if interactive:
                confirm = input("Are you sure you want to do this (y/N)?:  ")
            else:
                confirm = "yes"

        # Proceed with installation if confirmed
        if confirm.lower() in ["yes", "y"]:
            for package in pending_packages:
                argostranslate.package.install_from_path(package.download())

            # Calculate and report successful installations
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
