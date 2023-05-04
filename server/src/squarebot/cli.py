"""Administrative command-line interface."""

from __future__ import annotations

from typing import Optional

import click
import uvicorn


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(message="%(version)s")
def main() -> None:
    """SQuaRE Bot.

    Administrative command-line interface for SQuaRE Bot.
    """
    pass


@main.command()
@click.argument("topic", default=None, required=False, nargs=1)
@click.pass_context
def help(ctx: click.Context, topic: Optional[str]) -> None:
    """Show help for any command."""
    # The help command implementation is taken from
    # https://www.burgundywall.com/post/having-click-help-subcommand
    if topic:
        if topic in main.commands:
            click.echo(main.commands[topic].get_help(ctx))
        else:
            raise click.UsageError(f"Unknown help topic {topic}", ctx)
    else:
        assert ctx.parent
        click.echo(ctx.parent.get_help())


@main.command()
@click.option(
    "--port", default=8080, type=int, help="Port to run the application on."
)
def develop(port: int) -> None:
    """Run the application with live reloading (for development only)."""
    uvicorn.run(
        "squarebot.main:app", port=port, reload=True, reload_dirs=["src"]
    )
