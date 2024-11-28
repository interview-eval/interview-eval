from typing import Dict, List

import yaml
from dotenv import load_dotenv
from interview_eval import Interviewee
from interview_eval.custom_interview_experimental import (
    AdaptiveInterviewer,
    AdaptiveInterviewRunner,
    Question,
)
from interview_eval.utils import console, load_config, setup_logging
from openai import OpenAI
from rich.panel import Panel


def load_question_bank(path: str) -> Dict[str, List[Question]]:
    """Load question bank from YAML file."""
    with open(path, "r") as f:
        raw_data = yaml.safe_load(f)

    question_bank = {}
    for topic, questions in raw_data.items():
        question_bank[topic] = [Question(**q) for q in questions]

    return question_bank


def main():
    """Main entry point for the Adaptive Interview System."""
    console.print(
        Panel(
            "[green]Adaptive Interview System[/green]\n"
            "[cyan]Use Ctrl+C to exit[/cyan]",
            border_style="green",
            padding=(1, 2),
        )
    )

    try:
        # Load environment variables
        load_dotenv()

        # Load configurations
        config_data = load_config("config.yaml")

        logger = setup_logging(config_data, verbose=True)

        # Load question bank
        question_bank = load_question_bank("questions.yaml")

        # Initialize agents
        interviewer = AdaptiveInterviewer(
            config=config_data, question_bank=question_bank, name="Interviewer"
        )

        interviewee = Interviewee(config=config_data, name="Student")

        # Initialize and run interview
        interview = AdaptiveInterviewRunner(
            config=config_data,
            interviewer=interviewer,
            interviewee=interviewee,
            logger=logger,
            console=console,
        )

        results = interview.run()

        # Display final results
        console.print(
            Panel(
                f"[green]Interview Complete![/green]\n"
                f"Final Score: {results['final_score']:.1f}/10\n"
                f"Topics Covered: {len(results['topics_covered'])}\n"
                f"Total Questions: {len(results['response_history'])}",
                border_style="green",
                padding=(1, 2),
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interview session interrupted by user[/yellow]")

    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        logger.exception("Unexpected error during interview")
        raise


if __name__ == "__main__":
    main()
