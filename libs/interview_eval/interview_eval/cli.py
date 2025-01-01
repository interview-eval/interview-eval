import click
from dotenv import load_dotenv
from rich.panel import Panel

from interview_eval import Interviewee, Interviewer, InterviewRunner
from interview_eval.utils import console, load_config, setup_logging


@click.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to the configuration file",
    type=click.Path(exists=True),
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show all conversation utterances",
)
def main(config: str, verbose: bool):
    """Run an automated interview session."""
    # Show welcome message
    console.print(
        Panel(
            "[green]Automated Interview System[/green]\n" "[cyan]Use Ctrl+C to exit at any time[/cyan]",
            border_style="green",
            padding=(1, 2),
        )
    )

    try:
        config_data = load_config(config)
        logger, _ = setup_logging(config_data, verbose)

        interviewer = Interviewer(config=config_data, name="Interviewer")
        student = Interviewee(config=config_data, name="Student")

        interview = InterviewRunner(
            interviewer, student, config_data, logger, console)
        interview.run()

    except KeyboardInterrupt:
        console.print(
            "\n[warning]Interview session interrupted by user[/warning]")
    except Exception as e:
        console.print(f"\n[error]Error: {str(e)}[/error]")
        raise


if __name__ == "__main__":
    main()
