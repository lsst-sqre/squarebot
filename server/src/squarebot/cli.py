"""Administrative command-line interface."""

from __future__ import annotations

import click
import uvicorn
from safir.click import display_help


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """SQuaRE Bot.

    Administrative command-line interface for SQuaRE Bot.
    """


@main.command()
@click.argument("topic", default=None, required=False, nargs=1)
@click.argument("subtopic", default=None, required=False, nargs=1)
@click.pass_context
def help(ctx: click.Context, topic: str | None, subtopic: str | None) -> None:
    """Show help for any command."""
    display_help(main, ctx, topic, subtopic)


@main.command()
@click.option(
    "--port", default=8080, type=int, help="Port to run the application on."
)
def develop(port: int) -> None:
    """Run the application with live reloading (for development only)."""
    uvicorn.run(
        "squarebot.main:app", port=port, reload=True, reload_dirs=["src"]
    )
