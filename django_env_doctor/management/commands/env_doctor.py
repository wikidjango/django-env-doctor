"""
Django management command: env_doctor

Usage:
    python manage.py env_doctor
    python manage.py env_doctor --export-example
    python manage.py env_doctor --no-color
    python manage.py env_doctor --show-values
    python manage.py env_doctor --ci
"""

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Validate environment variables and display a health report."

    def add_arguments(self, parser):
        parser.add_argument(
            "--export-example",
            action="store_true",
            default=False,
            help="Generate a .env.example file from the schema and exit.",
        )
        parser.add_argument(
            "--example-output",
            type=str,
            default=".env.example",
            metavar="PATH",
            help="Output path for the .env.example file (default: .env.example).",
        )
        parser.add_argument(
            "--show-values",
            action="store_true",
            default=False,
            help="Show actual variable values in the report (secrets always hidden).",
        )
        parser.add_argument(
            "--ci",
            action="store_true",
            default=False,
            help="CI mode: plain output with no color, exit code 1 on issues.",
        )

    def handle(self, *args, **options):
        # Try to get the DjangoEnv instance from Django settings
        env_instance = self._get_env_instance()

        if env_instance is None:
            self.stderr.write(
                self.style.ERROR(
                    "\ndjango-env-doctor: Could not find a DjangoEnv instance.\n"
                    "Make sure you have created one in your settings.py:\n\n"
                    "    from django_env_doctor import DjangoEnv\n"
                    "    env = DjangoEnv(schema={...})\n"
                )
            )
            sys.exit(1)

        use_color = not options["ci"] and not options.get("no_color", False)

        # Export example and exit
        if options["export_example"]:
            output_path = options["example_output"]
            env_instance.export_example(output_path=output_path)
            self.stdout.write(
                self.style.SUCCESS(f"Generated {output_path} from schema.")
            )
            return

        # Print the health report
        env_instance.report(
            use_color=use_color,
            show_values=options["show_values"],
            output=self.stdout,
        )

        # Exit with non-zero code if there are issues
        if not env_instance.is_valid:
            sys.exit(1)

    def _get_env_instance(self):
        """
        Attempt to retrieve the DjangoEnv instance from Django settings.

        Looks for a module-level variable named `env` that is a DjangoEnv instance,
        or for ENV_DOCTOR_INSTANCE if the user named it differently.
        """
        try:
            import importlib
            import os

            from django.conf import settings
            from django_env_doctor import DjangoEnv

            # Check for explicit registration
            if hasattr(settings, "ENV_DOCTOR_INSTANCE"):
                return settings.ENV_DOCTOR_INSTANCE

            # Walk the actual settings module looking for a DjangoEnv instance
            settings_module_path = os.environ.get("DJANGO_SETTINGS_MODULE", "")
            if not settings_module_path:
                return None

            settings_module = importlib.import_module(settings_module_path)
            for attr_name in dir(settings_module):
                attr = getattr(settings_module, attr_name, None)
                if isinstance(attr, DjangoEnv):
                    return attr
        except Exception:
            pass

        return None
