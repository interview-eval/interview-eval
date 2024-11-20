from dotenv import load_dotenv
from rich.panel import Panel
from interview_eval.custom_interview_experimental import StateMachineInterviewer, Interviewee, StateMachineRunner
from interview_eval.utils import console, load_config, setup_logging


def main():
    console.print(
        Panel(
            "[green]Automated Interview System[/green]\n[cyan]Use Ctrl+C to exit[/cyan]",
            border_style="green",
            padding=(1, 2),
        )
    )

    try:
        load_dotenv()
        config_data = load_config("config.yaml")
        logger = setup_logging(config_data, verbose=True)

        interviewer = StateMachineInterviewer(config=config_data, name="Teacher")
        student = Interviewee(config=config_data, name="Student")
        interview = StateMachineRunner(
            interviewer, student, config_data, logger, console
        )
        interview.run()

    except KeyboardInterrupt:
        console.print("\n[warning]Interview session interrupted[/warning]")
    except Exception as e:
        console.print(f"\n[error]Error: {str(e)}[/error]")
        raise


if __name__ == "__main__":
    main()
