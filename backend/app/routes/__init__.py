"""Routes package initializer.

Imports route modules and registers their Flask blueprints.
"""

import importlib
from typing import Iterable


def register_blueprints(app, modules: Iterable[str] = None):

    if modules is None:
        modules = [
            "admin",
            "auth",
            "calendar",
            "face",
            "performance",
            "reports",
            "teachers",
            "hod",
            "student",
            "recruiter",
            "notices",
            "notifications",
            "timetable",
        ]

    for mod_name in modules:

        try:

            mod = importlib.import_module(
                f".{mod_name}",
                package=__package__
            )

            print(
                f"[ROUTES] Imported {mod_name} from:",
                getattr(mod, "__file__", "unknown")
            )

        except Exception as e:

            print(
                f"[ROUTES ERROR] Failed to import {mod_name}: {e}"
            )

            continue


        bp = (
            getattr(mod, "bp", None)
            or getattr(mod, "blueprint", None)
        )


        if bp is None:

            print(
                f"[ROUTES WARNING] No blueprint found in {mod_name}"
            )

            continue


        try:

            app.register_blueprint(bp)

            print(
                f"[ROUTES] Registered blueprint: {mod_name}"
            )

        except Exception as e:

            print(
                f"[ROUTES ERROR] Failed to register {mod_name}: {e}"
            )