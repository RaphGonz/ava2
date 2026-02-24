"""Skills package — import all skill modules to register them at startup."""
# These imports trigger register() calls in each skill module.
# To add a new skill: create the module and add an import line here.
from app.services.skills import calendar_skill  # noqa: F401  registers calendar_add, calendar_view
from app.services.skills import research_skill  # noqa: F401  registers research
