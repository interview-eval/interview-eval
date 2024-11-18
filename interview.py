import logging
from typing import Any, Dict, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from swarm import Agent, Result, Swarm


class Interviewer(Agent):
    def __init__(
        self,
        config: dict,
        name: Optional[str] = None,
    ):
        interviewer_config = config["interviewer"]
        name = name or interviewer_config["name"]

        instructions = (
            interviewer_config["instructions"]
            + f"\nRubric:\n{interviewer_config['rubric']}\n"
            + f"\nStrategy:\n{yaml.dump(interviewer_config['strategy'], default_flow_style=False)}"
        )

        super().__init__(name=name, instructions=instructions, functions=[self.conclude_interview])

    def conclude_interview(self, score: int, comments: str) -> Result:
        """Conclude the interview with final score and comments."""
        return Result(
            value=f"Interview concluded. Score: {score}/10\nComments: {comments}",
            context_variables={
                "interview_complete": True,
                "score": score,
                "comments": comments,
            },
        )


class Interviewee(Agent):
    def __init__(
        self,
        config: dict,
        name: Optional[str] = None,
    ):
        interviewee_config = config["interviewee"]
        name = name or interviewee_config["name"]
        instructions = interviewee_config["instructions"]
        super().__init__(name=name, instructions=instructions)


class InterviewRunner:
    def __init__(
        self,
        interviewer: Agent,
        interviewee: Agent,
        config: dict,
        logger: logging.Logger,
        console: Console,
    ):
        self.client = Swarm()
        self.interviewer = interviewer
        self.interviewee = interviewee
        self.config = config
        self.logger = logger
        self.console = console
        self.questions_count = 0
        self.max_questions = config["session"].get("max_questions", 10)  # Default to 10 questions if not specified

    def display_message(self, agent_name: str, content: str):
        """Display a message with proper formatting."""
        style = "interviewer" if agent_name == self.interviewer.name else "interviewee"
        panel = Panel(
            content,
            title=f"[{style}]{agent_name}[/{style}]",
            border_style=style,
            padding=(1, 2),
        )
        # Only print to console if in verbose mode
        if self.logger.getEffectiveLevel() <= logging.INFO:
            self.console.print(panel)

        # Always log to file if file logging is enabled
        self.logger.info(f"{agent_name}: {content}")

    def display_results(self, results: Dict[str, Any]):
        """Display interview results with formatting."""
        score = results["score"]
        score_color = "success" if score >= 7 else "warning" if score >= 5 else "error"

        results_panel = Panel(
            f"\n[{score_color}]Final Score: {score}/10[/{score_color}]\n\n"
            f"[info]Questions Asked: {results['questions_asked']}[/info]\n\n"
            f"[white]Feedback:[/white]\n{results['feedback']}",
            title="[success]Interview Assessment Results[/success]",
            border_style="success",
            padding=(1, 2),
        )
        self.console.print("\n")
        self.console.print(results_panel)

    def run(self) -> Dict[str, Any]:
        """Run the interview and return results."""
        # Show starting message
        self.console.print("\n[info]Starting Interview Session...[/info]\n")

        messages = [
            {
                "role": "user",
                "content": self.config["session"]["initial_message"],
            }
        ]
        context = self.config["session"]["initial_context"]

        # Display initial message
        self.display_message(self.interviewer.name, messages[-1]["content"])

        # Start with interviewee
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing response...", total=None)
            response = self.client.run(agent=self.interviewee, messages=messages, context_variables=context)

        self.display_message(response.agent.name, response.messages[-1]["content"])

        while not response.context_variables.get("interview_complete", False):
            # Check if max questions limit has been reached
            messages = response.messages + [{"role": "user", "content": response.messages[-1]["content"]}]
            next_agent = self.interviewer if response.agent == self.interviewee else self.interviewee

            if next_agent == self.interviewer:
                self.questions_count += 1
                self.console.print(f"\n[info]Question {self.questions_count}[/info]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Processing response...", total=None)
                response = self.client.run(
                    agent=next_agent,
                    messages=messages,
                    context_variables=response.context_variables,
                )

            self.display_message(response.agent.name, response.messages[-1]["content"])

            if response.agent == self.interviewee and self.questions_count >= self.max_questions:
                # Force conclude the interview
                final_message = "Maximum number of questions reached. Concluding interview."
                self.console.print(f"\n[warning]{final_message}[/warning]")
                response = self.client.run(
                    agent=self.interviewer,
                    messages=messages + [{"role": "system", "content": response.messages[-1]["content"]}],
                    context_variables={"force_conclude": True},
                )
                self.display_message(response.agent.name, response.messages[-1]["content"])
                break

        results = {
            "score": response.context_variables["score"],
            "feedback": response.context_variables["comments"],
            "questions_asked": self.questions_count,
        }

        self.display_results(results)
        return results
