import logging
import yaml
from openai import OpenAI

# Import your classes here
from interview_eval import Interviewee
from interview_eval.custom_interview_experimental import (
    EvaluationAgent,
    QuestionAgent,
    EnhancedInterviewRunner,
)
from interview_eval.utils import console, load_config, setup_logging


def main():
    # Initialize console for rich output

    # Setup logging

    try:
        # Load configuration
        config = load_config("enhanced_config.yaml")
        logger = setup_logging(config, verbose=True)


        # Create agents
        evaluator = EvaluationAgent(config=config, name="Technical Evaluator")

        questioner = QuestionAgent(config=config, name="Technical Interviewer")

        interviewee = Interviewee(config=config, name="Candidate")

        # Create interview runner
        runner = EnhancedInterviewRunner(
            evaluator=evaluator,
            questioner=questioner,
            interviewee=interviewee,
            config=config,
            logger=logger,
            console=console,
        )

        # Run the interview
        console.print("[bold green]Starting Technical Interview Session[/bold green]")
        results = runner.run()

        # Save results to file
        with open("interview_results.yaml", "w") as f:
            yaml.dump(results, f)

        console.print(
            "[bold green]Interview session completed. Results saved to interview_results.yaml[/bold green]"
        )

    except Exception as e:
        console.print(f"[bold red]Error during interview: {str(e)}[/bold red]")
        raise e
        # logger.error(f"Interview error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
