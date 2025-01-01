import click
from dotenv import load_dotenv
from interview_eval import Interviewee, Interviewer, InterviewRunner, InterviewReportManager
from interview_eval.utils import console, load_config, setup_logging
from rich.panel import Panel


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
            "[green]Automated Interview System[/green]\n"
            "[cyan]Use Ctrl+C to exit at any time[/cyan]",
            border_style="green",
            padding=(1, 2),
        )
    )
    existing_data = [
    {"question": "What is 5 + 7?", "solution": "12"},
    {"question": "Solve for x: 2x + 3 = 7", "solution": "x = 2"}
]
    try:

        config_data = load_config(config)
        interviewer = Interviewer(config=config_data, name="Interviewer")
        student = Interviewee(config=config_data, name="Student")
        report_manager = InterviewReportManager(config=config_data)
        for question in existing_data:
            logger, log_file_path = setup_logging(config_data, verbose)
            interviewer.seed_question = question['question']
            interviewer.seed_question_answer = question['solution']
            interview = InterviewRunner(interviewer, student, config_data, logger, log_file_path, console, report_manager)
            interview.run()
            report_manager.save_to_csv('test.csv')
        report_manager.generate_report(interviewer)
    except KeyboardInterrupt:
        console.print("\n[warning]Interview session interrupted by user[/warning]")
    except Exception as e:
        console.print(f"\n[error]Error: {str(e)}[/error]")
        raise


if __name__ == "__main__":
    main()
