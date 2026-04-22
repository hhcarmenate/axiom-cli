import typer

from axiom_cli.commands import doctor, init, install, new, status, update

app = typer.Typer(
    name="axiom",
    help="Orchestrate the axiom ecosystem: continuum + axiom-team + axiom-skills.",
    no_args_is_help=True,
    add_completion=False,
)

app.command("init")(init.command)
app.command("new")(new.command)
app.command("install")(install.command)
app.command("status")(status.command)
app.command("update")(update.command)
app.command("doctor")(doctor.command)


if __name__ == "__main__":
    app()
