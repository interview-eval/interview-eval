import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from interview_eval.swarm import Agent, Result, Swarm

from .interview import Interviewee


@dataclass
class Response:
    messages: list
    agent: Agent
    context_variables: dict


EVAL_AGENT_INSTRUCTION = "Based on the grading rubirc, provide a critique that evaluates the response quality."
QUESTION_AGENT_INSTRUCTION = "Ask a follow up question based on the previous history."


class EvaluationAgent(Agent):
    def __init__(
        self,
        config: dict,
        name: Optional[str] = None,
    ):
        eval_config = config["evaluator"]
        name = name or eval_config["name"]
        client_kwargs = eval_config.get("client", None)
        client = OpenAI(**client_kwargs) if client_kwargs else OpenAI()

        instructions = EVAL_AGENT_INSTRUCTION + f"\nRubric:\n{eval_config['rubric']}"

        super().__init__(
            name=name,
            instructions=instructions,
            client=client,
        )


class QuestionAgent(Agent):
    def __init__(
        self,
        config: dict,
        name: Optional[str] = None,
    ):
        question_config = config["questioner"]
        name = name or question_config["name"]
        client_kwargs = question_config.get("client", None)
        client = OpenAI(**client_kwargs) if client_kwargs else OpenAI()

        instructions = (
            QUESTION_AGENT_INSTRUCTION
            + f"\nQuestion Strategy:\n{yaml.dump(question_config['strategy'], default_flow_style=False)}"
        )

        super().__init__(
            name=name,
            instructions=instructions,
            client=client,
        )
        self.seed_question = question_config["seed_question"]


class EnhancedInterviewRunner:
    def __init__(
        self,
        evaluator: EvaluationAgent,
        questioner: QuestionAgent,
        interviewee: Agent,
        config: dict,
        logger: logging.Logger,
        console: Console,
    ):
        self.client = Swarm()
        self.evaluator = evaluator
        self.questioner = questioner
        self.interviewee = interviewee
        self.config = config
        self.logger = logger
        self.console = console
        self.questions_count = 0
        self.max_questions = config["session"].get("max_questions", 10)

    def display_message(self, agent_name: str, content: str, message_type: str = "normal"):
        """Display a message with proper formatting."""
        style_map = {
            "evaluator": "yellow",
            "questioner": "blue",
            "interviewee": "green",
            "system": "white",
        }
        style = style_map.get(message_type, "white")

        panel = Panel(
            content,
            title=f"[{style}]{agent_name}[/{style}]",
            border_style=style,
            padding=(1, 2),
        )
        if self.logger:
            if self.logger.getEffectiveLevel() <= logging.INFO:
                self.console.print(panel)
            self.logger.info(f"{agent_name}: {content}")

    def run(self) -> Dict[str, Any]:
        """Run the enhanced interview process."""
        self.console.print("\n[info]Starting Enhanced Interview Session...[/info]\n")

        # Ask seed question
        self.questions_count += 1
        seed_question = self.questioner.seed_question
        self.display_message(self.questioner.name, seed_question, "questioner")

        evaluations = []
        interview_complete = False

        while not interview_complete and self.questions_count <= self.max_questions:
            # Get interviewee response
            interviewee_response = self._get_response(
                self.interviewee,
                [
                    {
                        "role": "user",
                        "content": (seed_question if self.questions_count == 1 else current_question),
                    }
                ],
                {},
            )
            self.display_message(
                self.interviewee.name,
                interviewee_response.messages[-1]["content"],
                "interviewee",
            )

            import pdb

            pdb.set_trace()
            # Get evaluation
            evaluation = self.evaluator.evaluate_response(interviewee_response.messages[-1]["content"])
            self.display_message(self.evaluator.name, evaluation.value, "evaluator")
            evaluations.append(evaluation.value)

            # Generate next question based on evaluation
            if self.questions_count < self.max_questions:
                question_result = self.questioner.generate_question(
                    interviewee_response.messages[-1]["content"],
                    evaluation.context_variables["evaluation"],
                )
                current_question = question_result.value
                self.questions_count += 1
                self.display_message(self.questioner.name, current_question, "questioner")
            else:
                interview_complete = True

        # Compile final results
        final_evaluation = self._get_response(
            self.evaluator,
            [
                {
                    "role": "user",
                    "content": "Provide final evaluation based on all responses: " + "\n".join(evaluations),
                }
            ],
            {},
        )

        results = {
            "evaluations": evaluations,
            "questions_asked": self.questions_count,
            "final_evaluation": final_evaluation.messages[-1]["content"],
        }

        self.display_results(results)
        return results

    def display_results(self, results: Dict[str, Any]):
        """Display interview results with formatting."""
        results_panel = Panel(
            f"\n[info]Questions Asked: {results['questions_asked']}[/info]\n\n"
            f"[white]Final Evaluation:[/white]\n{results['final_evaluation']}\n\n"
            f"[white]Individual Evaluations:[/white]\n" + "\n".join([f"- {eval}" for eval in results["evaluations"]]),
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
