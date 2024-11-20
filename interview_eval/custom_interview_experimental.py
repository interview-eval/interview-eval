from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Any
import logging
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from interview_eval.interview import Interviewer, Interviewee, Result, InterviewRunner


class State(Enum):
    INITIAL = auto()
    QUESTION = auto()
    EVALUATE_RESPONSE = auto()
    DEEP_DIVE = auto()
    CHALLENGE = auto()
    NEXT_TOPIC = auto()
    CONCLUDE = auto()


@dataclass
class StateContext:
    current_state: State
    conversation_history: List[dict]
    topic_coverage: Dict[str, float]
    understanding_level: float = 0.0
    questions_asked: int = 0
    max_questions: int = 10


class StateMachineInterviewer(Interviewer):
    def __init__(self, config: dict, name: Optional[str] = None):
        super().__init__(config, name)
        self.state_handlers = {
            State.INITIAL: self.handle_initial,
            State.QUESTION: self.handle_question,
            State.EVALUATE_RESPONSE: self.handle_evaluate,
            State.DEEP_DIVE: self.handle_deep_dive,
            State.CHALLENGE: self.handle_challenge,
            State.NEXT_TOPIC: self.handle_next_topic,
            State.CONCLUDE: self.handle_conclude,
        }
        
    def handle_initial(self, topics: list) -> Result:
        """Generate initial interview greeting and overview.

        Args:
            topics (list): List of topics to be covered

        Returns:
            Result: Initial greeting with context
        """
        return Result(
            value=f"Welcome to the technical interview. We'll be covering: {', '.join(topics)}",
            context_variables={"state": State.QUESTION}
        )

    def handle_question(self, topic: str, previous_responses: list = None, is_followup: bool = False) -> Result:
        """Generate interview question.

        Args:
            topic (str): Current topic being assessed
            previous_responses (list, optional): Previous conversation exchanges
            is_followup (bool): Whether this is a follow-up question

        Returns:
            Result: Question with context
        """
        return Result(
            value=f"For {topic}, please explain..." if not is_followup else "Could you elaborate on...",
            context_variables={
                "state": State.EVALUATE_RESPONSE,
                "current_topic": topic
            }
        )

    def handle_evaluate(self, response: str, current_topic: str) -> Result:
        """Evaluate candidate response.

        Args:
            response (str): Candidate's answer
            current_topic (str): Topic being evaluated

        Returns:
            Result: Evaluation with next state
        """
        return Result(
            value="Thank you for your response.",
            context_variables={
                "technical_accuracy": 0.8,
                "clarity": 0.7,
                "depth": 0.9,
                "state": State.NEXT_TOPIC
            }
        )

    def handle_deep_dive(self, previous_response: str) -> Result:
        """Generate technical deep-dive question.

        Args:
            previous_response (str): Previous answer to follow up on

        Returns:
            Result: Deep-dive question with context
        """
        return Result(
            value="Let's explore that concept further. How would you...",
            context_variables={"state": State.EVALUATE_RESPONSE}
        )

    def handle_challenge(self, previous_response: str) -> Result:
        """Generate challenging follow-up question.

        Args:
            previous_response (str): Response to challenge

        Returns:
            Result: Challenge question with context
        """
        return Result(
            value="That's interesting, but what if we consider...",
            context_variables={"state": State.EVALUATE_RESPONSE}
        )

    def handle_next_topic(self, topic_coverage: Dict[str, float]) -> Result:
        """Generate transition to next topic.

        Args:
            topic_coverage (Dict[str, float]): Coverage of each topic

        Returns:
            Result: Topic transition with context
        """
        return Result(
            value="Let's move on to the next topic.",
            context_variables={"state": State.QUESTION}
        )

    def handle_conclude(self, understanding_level: float, history: List[dict]) -> Result:
        """Conclude interview with assessment.

        Args:
            understanding_level (float): Overall understanding (0-1)
            history (List[dict]): Full conversation history

        Returns:
            Result: Final assessment with score and feedback
        """
        score = int(understanding_level * 10)
        comments = "Demonstrated strong technical knowledge..."
        
        return Result(
            value=f"Interview concluded. Score: {score}/10\nComments: {comments}",
            context_variables={
                "interview_complete": True,
                "score": score,
                "comments": comments
            }
        )

    def process_message(self, message: str, context: StateContext) -> Result:
        evaluation = self._evaluate_response(context, message)
        next_state = self._determine_next_state(context, evaluation)
        response = self._generate_response(next_state, context, evaluation)

        return Result(
            value=response,
            context_variables={"next_state": next_state.name, **evaluation},
        )

    def _determine_next_state(self, context: StateContext, evaluation: dict) -> State:
        messages = [
            {
                "role": "system",
                "content": "Determine next interview state based on context and evaluation.",
            },
            {
                "role": "user",
                "content": f"""
            Current: {context.current_state}
            Understanding: {context.understanding_level:.2f}
            Questions: {context.questions_asked}/{context.max_questions}
            Topics: {context.topic_coverage}
            Eval: {evaluation}""",
            },
        ]
        response = self.client.chat.completions.create(model="gpt-4", messages=messages)
        return State[response.choices[0].message.content.strip()]

    def _evaluate_response(self, context: StateContext, message: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": "Evaluate response with technical_accuracy, clarity, depth (0-1)",
            },
            {"role": "user", "content": message},
        ]
        return (
            self.client.chat.completions.create(model="gpt-4", messages=messages)
            .choices[0]
            .message.content
        )


class StateMachineRunner(InterviewRunner):
    def __init__(
        self,
        interviewer: StateMachineInterviewer,
        interviewee: Interviewee,
        config: dict,
        logger: logging.Logger,
        console: Console,
    ):
        super().__init__(interviewer, interviewee, config, logger, console)
        self.context = StateContext(
            current_state=State.INITIAL,
            conversation_history=[],
            topic_coverage={topic: 0.0 for topic in config["topics"]},
            max_questions=config["session"]["max_questions"],
        )

    def run(self) -> Dict[str, Any]:
        self.console.print("\n[info]Starting State Machine Interview...[/info]\n")

        while True:
            # Get interviewer response
            response = self.interviewer.process_message(
                (
                    self.context.conversation_history[-1]["content"]
                    if self.context.conversation_history
                    else ""
                ),
                self.context,
            )
            self.display_message(self.interviewer.name, response.value)

            # Update state
            self.context.current_state = State[response.context_variables["next_state"]]
            if self.context.current_state == State.CONCLUDE:
                break

            # Get interviewee response
            interviewee_response = self.interviewee.process_message(
                response.value, self.context.conversation_history
            )
            self.display_message(self.interviewee.name, interviewee_response.value)

            self.context.questions_asked += 1
            self.context.conversation_history.extend(
                [
                    {"role": "interviewer", "content": response.value},
                    {"role": "interviewee", "content": interviewee_response.value},
                ]
            )

        return {
            "score": int(self.context.understanding_level * 10),
            "feedback": response.context_variables.get("feedback", ""),
            "questions_asked": self.context.questions_asked,
        }


def create_interview_session(config: dict) -> StateMachineRunner:
    logger = logging.getLogger(__name__)
    console = Console()

    interviewer = StateMachineInterviewer(config)
    interviewee = Interviewee(config)

    return StateMachineRunner(
        interviewer=interviewer,
        interviewee=interviewee,
        config=config,
        logger=logger,
        console=console,
    )
