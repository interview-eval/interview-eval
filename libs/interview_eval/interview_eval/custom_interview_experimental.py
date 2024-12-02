# TODO: Reimplement EVERY STATES as a separate agent in swarm
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import yaml
from openai import OpenAI
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from interview_eval.swarm import Agent, Result, Swarm


class InterviewState(str, Enum):
    INITIAL = "initial"
    QUESTION = "question"
    EVALUATE = "evaluate"
    DEEP_DIVE = "deep_dive"
    CHALLENGE = "challenge"
    NEXT_QUESTION = "next_question"
    CONCLUDE = "conclude"


class Question(BaseModel):
    text: str
    topic: str
    difficulty: float
    expected_concepts: List[str]
    follow_ups: List[str]


class ResponseEvaluation(BaseModel):
    concepts_demonstrated: List[str] = Field(default_factory=list)
    concepts_missing: List[str] = Field(default_factory=list)
    understanding_level: float = Field(ge=0, le=1)
    confidence_level: float = Field(ge=0, le=1)
    answer_quality: float = Field(ge=0, le=1)
    needs_clarification: bool = False
    needs_depth: bool = False
    feedback: str


class InterviewContext(BaseModel):
    current_state: InterviewState = InterviewState.INITIAL
    current_topic: str = ""
    current_question: Optional[Question] = None
    difficulty_level: float = 0.5
    topics_covered: Dict[str, float] = Field(default_factory=dict)
    concepts_demonstrated: Dict[str, float] = Field(default_factory=dict)
    response_history: List[ResponseEvaluation] = Field(default_factory=list)
    consecutive_good_responses: int = 0
    consecutive_weak_responses: int = 0
    interview_complete: bool = False


class AdaptiveInterviewer(Agent):

    def __init__(
        self,
        config: dict,
        question_bank: Dict[str, List[Question]],
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

        state_functions = [
            self.evaluate_response,
            self.generate_deep_dive,
            self.challenge_response,
            self.next_question,
            self.conclude_interview,
        ]

        super().__init__(
            name=name,
            instructions=instructions,
            functions=state_functions,
            client=client,
        )

        self.question_bank = question_bank
        self.config = interviewer_config
        self.state_functions = state_functions

    def evaluate_response(
        self,
        concepts_demonstrated: List[str],
        concepts_missing: List[str],
        understanding_level: float,
        confidence_level: float,
        answer_quality: float,
        feedback: str,
    ) -> Result:
        """
        Evaluate the candidate's response and determine next state.
        """
        evaluation = ResponseEvaluation(
            concepts_demonstrated=concepts_demonstrated,
            concepts_missing=concepts_missing,
            understanding_level=understanding_level,
            confidence_level=confidence_level,
            answer_quality=answer_quality,
            needs_clarification=confidence_level < 0.7,
            needs_depth=understanding_level < 0.7,
            feedback=feedback,
        )

        # Determine next state based on evaluation
        next_state = InterviewState.NEXT_QUESTION
        if evaluation.needs_depth:
            next_state = InterviewState.DEEP_DIVE
        elif evaluation.needs_clarification:
            next_state = InterviewState.CHALLENGE
        elif understanding_level > 0.9 and confidence_level > 0.9:
            next_state = InterviewState.CONCLUDE

        context_updates = {
            "response_history": lambda x: x + [evaluation],
            "consecutive_good_responses": lambda x: (x + 1 if answer_quality > 0.8 else 0),
            "consecutive_weak_responses": lambda x: (x + 1 if answer_quality < 0.6 else 0),
            "current_state": next_state,
        }

        # Adjust difficulty based on performance
        if answer_quality > 0.8:
            context_updates["difficulty_level"] = lambda x: min(1.0, x + 0.1)
        elif answer_quality < 0.6:
            context_updates["difficulty_level"] = lambda x: max(0.0, x - 0.1)

        return Result(value=feedback, context_variables=context_updates)

    def generate_deep_dive(self, concept: str, current_understanding: str, probe_question: str) -> Result:
        """
        Generate a technical deep-dive question.
        """
        message = (
            f"I'd like to explore your understanding of {concept} further.\n"
            f"Based on your explanation that {current_understanding},\n"
            f"{probe_question}"
        )

        return Result(value=message, context_variables={"current_state": InterviewState.QUESTION})

    def challenge_response(self, assumption: str, edge_case: str, challenge_question: str) -> Result:
        """
        Challenge the candidate's assumptions.
        """
        message = (
            f"Regarding your assumption about {assumption},\n"
            f"Consider this edge case: {edge_case}\n"
            f"{challenge_question}"
        )

        return Result(value=message, context_variables={"current_state": InterviewState.QUESTION})

    def next_question(self) -> Result:
        """
        Select and present the next question based on performance.
        """

        def select_question(context: Dict[str, Any]) -> Question:
            target_difficulty = context["difficulty_level"]
            topic_weights = self._calculate_topic_weights(context)

            # Select topic based on weights
            selected_topic = max(topic_weights.items(), key=lambda x: x[1])[0]

            # Filter questions by topic and find closest difficulty
            topic_questions = self.question_bank[selected_topic]
            selected_question = min(topic_questions, key=lambda q: abs(q.difficulty - target_difficulty))

            return selected_question

        return Result(
            value="question_selection",
            context_variables={
                "current_state": InterviewState.QUESTION,
                "current_question": select_question,
            },
        )

    def conclude_interview(
        self,
        final_score: float,
        strengths: List[str],
        areas_for_improvement: List[str],
        detailed_feedback: Dict[str, str],
    ) -> Result:
        """
        Conclude the interview with final assessment.
        """
        message = (
            f"Interview Score: {final_score:.1f}/10\n\n"
            "Key Strengths:\n"
            f"{chr(10).join(f'• {s}' for s in strengths)}\n\n"
            "Areas for Improvement:\n"
            f"{chr(10).join(f'• {a}' for a in areas_for_improvement)}\n\n"
            "Detailed Feedback:\n"
        )

        for topic, feedback in detailed_feedback.items():
            message += f"\n{topic}:\n{feedback}\n"

        return Result(
            value=message,
            context_variables={
                "interview_complete": True,
                "final_score": final_score,
                "detailed_feedback": detailed_feedback,
            },
        )

    def _calculate_topic_weights(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Calculate weights for topic selection based on coverage and performance."""
        weights = {}
        for topic in self.question_bank.keys():
            # Base weight - inverse of coverage
            coverage = context["topics_covered"].get(topic, 0)
            weight = 1.0 - coverage

            # Adjust weight based on performance in related topics
            related_concepts = set()
            for question in self.question_bank[topic]:
                related_concepts.update(question.expected_concepts)

            concept_performance = []
            for concept in related_concepts:
                if concept in context["concepts_demonstrated"]:
                    concept_performance.append(context["concepts_demonstrated"][concept])

            if concept_performance:
                avg_performance = sum(concept_performance) / len(concept_performance)
                # Increase weight for topics where related concept performance is weak
                weight *= 1.0 + (1.0 - avg_performance)

            weights[topic] = weight

        return weights


class AdaptiveInterviewRunner:
    def __init__(
        self,
        config: dict,
        interviewer: AdaptiveInterviewer,
        interviewee: Agent,
        logger: logging.Logger,
        console: Console,
    ):
        self.client = Swarm()
        self.config = config
        self.interviewer = interviewer
        self.interviewee = interviewee
        self.logger = logger
        self.console = console
        self.context = InterviewContext()

    def run(self) -> Dict[str, Any]:
        """Run the adaptive interview process."""
        self.console.print("\n[info]Starting Adaptive Interview Session...[/info]\n")

        messages = []
        current_agent = self.interviewer

        while not self.context.interview_complete:
            # Get next message/action from current agent
            response = self._get_response(current_agent, messages, self.context.dict())
            self._handle_state_transition(response)

            # Display response
            if response.messages[-1]["content"]:
                self.display_message(current_agent.name, response.messages[-1]["content"])

            # Switch agents
            messages.extend(response.messages)
            current_agent = self.interviewee if current_agent == self.interviewer else self.interviewer

            # Check for early termination conditions
            if self._should_terminate():
                conclude_response = self._get_response(
                    self.interviewer,
                    messages,
                    {**self.context.dict(), "force_conclude": True},
                )
                self.display_message(self.interviewer.name, conclude_response.messages[-1]["content"])
                break

        return self._prepare_results()

    def _get_response(self, agent: Agent, messages: list, context: dict) -> Result:
        """Get response with progress spinner."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Getting {agent.name}'s response...", total=None)
            return self.client.run(agent=agent, messages=messages, context_variables=context)

    def _handle_state_transition(self, response: Result) -> None:
        """Update context based on response."""

        print("handle_state_transition: ", response)
        if not response.context_variables:
            return

        for key, value in response.context_variables.items():
            if hasattr(self.context, key):
                if callable(value):
                    current_value = getattr(self.context, key)
                    setattr(self.context, key, value(current_value))
                else:
                    setattr(self.context, key, value)

    def _should_terminate(self) -> bool:
        """Check if interview should terminate early."""
        return (
            self.context.consecutive_good_responses >= 3
            or self.context.consecutive_weak_responses >= 3
            or len(self.context.response_history)
            >= self.config["session"].get("max_questions", 10)  # Default to 10 questions if not specified
        )

    def _prepare_results(self) -> Dict[str, Any]:
        """Prepare final interview results."""
        return {
            "final_score": getattr(self.context, "final_score", 0),
            "topics_covered": self.context.topics_covered,
            "concepts_demonstrated": self.context.concepts_demonstrated,
            "response_history": [r.dict() for r in self.context.response_history],
            "difficulty_progression": [r.answer_quality for r in self.context.response_history],
        }

    def display_message(self, agent_name: str, content: str):
        """Display a message with proper formatting."""
        style = "interviewer" if agent_name == self.interviewer.name else "interviewee"
        panel = Panel(
            content,
            title=f"[{style}]{agent_name}[/{style}]",
            border_style=style,
            padding=(1, 2),
        )

        if self.logger.getEffectiveLevel() <= logging.INFO:
            self.console.print(panel)

        self.logger.info(f"{agent_name}: {content}")
