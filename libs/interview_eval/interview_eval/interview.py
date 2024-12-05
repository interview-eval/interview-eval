import logging

# import dataclass
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from interview_eval.swarm import Agent, Result, Swarm


@dataclass
class Response:
    messages: list
    agent: Agent
    context_variables: dict


class Interviewer(Agent):
    def __init__(
        self,
        config: dict,
        name: Optional[str] = None,
    ):
        interviewer_config = config["interviewer"]
        name = name or interviewer_config["name"]
        client_kwargs = interviewer_config.get("client", None)
        client = OpenAI(**client_kwargs) if client_kwargs else OpenAI()

        instructions = (
            interviewer_config["instructions"]
            + f"\nRubric:\n{interviewer_config['rubric']}\n"
            + f"\nStrategy:\n{yaml.dump(interviewer_config['strategy'], default_flow_style=False)}"
        )

        super().__init__(
            name=name,
            instructions=instructions,
            functions=[self.conclude_interview],
            client=client,
        )

        self.seed_question = interviewer_config.get("seed_question", "")

    def conclude_interview(self, score: int, comments: str) -> Result:
        """End interview with final assessment.

        Called when max questions reached, understanding established, or unable to progress further.
        Also called when forced to conclude interview.

        Args:
            score (int): Final score (0-10) based on rubric
            comments (str): Overall evaluation including strengths,
                weaknesses, and areas for improvement

        Returns:
            Result: Final assessment with score and detailed feedback
        """
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
        client_kwargs = interviewee_config.get("client", None)
        client = OpenAI(**client_kwargs) if client_kwargs else OpenAI()

        instructions = interviewee_config["instructions"]
        super().__init__(name=name, instructions=instructions, client=client)


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
        self.max_retries = config["session"].get("max_retries", 2)  # Default to 2 retries if not specified
        self.seed_question_used = False

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

    def _get_response(self, agent: Agent, messages: list, context: dict) -> Result:
        """Helper method to get response with progress spinner."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing response...", total=None)
            return self.client.run(agent=agent, messages=messages, context_variables=context)

    # TODO: Refactor this method to make it more readable
    def run(self) -> Dict[str, Any]:
        """Run the interview and return results."""
        self.console.print("\n[info]Starting Interview Session...[/info]\n")

        initial_message = self.config["session"]["initial_message"]
        interviewer_messages = [{"role": "assistant", "content": initial_message}]
        interviewee_messages = [{"role": "user", "content": initial_message}]
        context = self.config["session"]["initial_context"]

        self.display_message(self.interviewer.name, initial_message)

        response = self._get_response(self.interviewee, interviewee_messages, context)
        self.display_message(response.agent.name, response.messages[-1]["content"])

        while not response.context_variables.get("interview_complete", False):
            next_agent = self.interviewer if response.agent == self.interviewee else self.interviewee
            previous_response_content = response.messages[-1]["content"]

            if next_agent == self.interviewer:
                # Next speaker is interviewer
                self.questions_count += 1
                self.console.print(f"\n[info]Question {self.questions_count}[/info]")

                if (
                    not self.seed_question_used
                    and hasattr(self.interviewer, "seed_question")
                    and self.interviewer.seed_question
                ):
                    # Use the seed question for the first question
                    interviewer_messages.extend(
                        [
                            {"role": "user", "content": previous_response_content},
                        ]
                    )
                    interviewee_messages.extend(
                        [
                            {"role": "assistant", "content": previous_response_content},
                        ]
                    )

                    interviewer_response = Response(
                        messages=[{"role": "assistant", "content": self.interviewer.seed_question}],
                        agent=self.interviewer,
                        context_variables={},
                    )
                    self.seed_question_used = True
                else:
                    # Generate a question as usual
                    interviewer_messages.extend(
                        [
                            {"role": "user", "content": previous_response_content},
                        ]
                    )
                    interviewee_messages.extend(
                        [
                            {"role": "assistant", "content": previous_response_content},
                        ]
                    )
                    interviewer_response = self._get_response(
                        next_agent, interviewer_messages, response.context_variables
                    )

                response = interviewer_response
            else:
                # Next speaker is interviewee
                interviewer_messages.extend(
                    [
                        {"role": "assistant", "content": previous_response_content},
                    ]
                )
                interviewee_messages.extend(
                    [
                        {"role": "user", "content": previous_response_content},
                    ]
                )
                response = self._get_response(next_agent, interviewee_messages, response.context_variables)

            self.display_message(response.agent.name, response.messages[-1]["content"])

            if response.agent == self.interviewee:      
                last_msg_content = "Question: " + interviewee_messages[-1]["content"] + "\nResponse: "+ response.messages[-1]["content"]
                fmsg = [{"role": "user", "content": f"Provide a concise language critique in 2 sentences evaluating the response based the previous question. Provide rationale.\n{last_msg_content}"}]
                temp_msg = self._get_response(self.interviewer, fmsg, {})
                self.display_message("Feedback Agent", temp_msg.messages[-1]["content"])

            # 1. Check end conditions for the interview
            if response.agent == self.interviewee and self.questions_count >= self.max_questions:
                final_message = "Maximum number of questions reached. Concluding interview."
                self.console.print(f"\n[warning]{final_message}[/warning]")

                interviewer_messages.extend(
                    [
                        {
                            "role": "assistant",
                            "content": response.messages[-1]["content"],
                        },
                        {"role": "user", "content": final_message},
                    ]
                )

                response = self._get_response(self.interviewer, interviewer_messages, {"force_conclude": True})
                self.display_message(response.agent.name, response.messages[-1]["content"])
                break

        results = {
            "score": response.context_variables["score"],
            "feedback": response.context_variables["comments"],
            "questions_asked": self.questions_count,
        }

        self.display_results(results)
        return results
