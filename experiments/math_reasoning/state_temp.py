
from enum import Enum, auto
from typing import Any, Callable, Dict, Tuple

from src.utils import extract_json

from .prompt import (EVALUATEE_STATE_EXP_PROMPT_TEMPLATE,
                     EVALUATOR_STATE_EXP_PROMPT_TEMPLATE,
                     EVALUATOR_STATE_UNC_PROMPT_TEMPLATE,
                     MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE,
                     MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE)


class InterviewState(Enum):
    SESSION_START = auto()
    CLARIFICATION_NEEDED = auto()
    QUESTION_SOLVING = auto()
    FOLLOW_UP_QUESTION_SOLVING = auto()
    MOVING_TO_NEXT_QUESTION = auto()
    QUESTION_COMPLETE = auto()
    EVALUATION_COMPLETE = auto()
    SOLVE_FAIL = auto()
    SOLVE_SUCCESS = auto()


class InterviewType(Enum):
    MATH = auto()
    TEAM_FIT = auto()
    CODE = auto()


class StateMachine:
    def __init__(self, interview_type: InterviewType):
        self.state = InterviewState.SESSION_START
        self.interview_type = interview_type
        self.attempts = 0
        self.success = False
    def transition(self, action, threshold: int) -> None:
        if action:
            self.action = action

        if self.state == InterviewState.SESSION_START:
            if str(self.action) in ["paraphrasing", None]:
                self.state = InterviewState.QUESTION_SOLVING
                self.attempts = 0
            elif str(self.action) == "unclarifying":
                self.state = InterviewState.CLARIFICATION_NEEDED
                self.attempts = 0
            elif str(self.action) == "query_finished":
                self.state = InterviewState.EVALUATION_COMPLETE
                self.attempts = 0
            else:
                self.attempts += 1

        elif self.state == InterviewState.CLARIFICATION_NEEDED:
            if self.attempts == threshold:
                self.state = InterviewState.QUESTION_SOLVING
                self.attempts = 0
            elif str(self.action).lower() == "complete":
                self.state = InterviewState.QUESTION_SOLVING
                self.attempts = 0
            else:
                self.attempts += 1

        elif self.state == InterviewState.QUESTION_SOLVING:
            if self.attempts == threshold:
                self.state = InterviewState.SOLVE_FAIL
                self.attempts = 0
            elif str(self.action).lower() == "complete":
                self.state = InterviewState.SOLVE_SUCCESS
                self.success = True
                self.attempts = 0
            else:
                self.attempts += 1

        elif self.state == InterviewState.SOLVE_FAIL:
            if str(self.action).lower() in ["guess","misinterpret"]:
                self.state = InterviewState.FOLLOW_UP_QUESTION_SOLVING
                self.attempts = 0
            else:
                self.state = InterviewState.MOVING_TO_NEXT_QUESTION
                self.attempts += 1

        elif self.state == InterviewState.FOLLOW_UP_QUESTION_SOLVING:
            if self.attempts == threshold:
                self.state = InterviewState.MOVING_TO_NEXT_QUESTION
                self.attempts = 0
            elif str(self.action).lower() == "complete":
                self.state = InterviewState.MOVING_TO_NEXT_QUESTION
                self.attempts = 0
            else:
                self.attempts += 1

        elif self.state == InterviewState.MOVING_TO_NEXT_QUESTION:
            self.state = InterviewState.QUESTION_COMPLETE
        elif self.state == InterviewState.QUESTION_COMPLETE:
            self.state = InterviewState.SESSION_START
            self.attempts = 0

    def get_prompt(self, solution: Dict[str, Any], session_history: list) -> str:
        if self.interview_type == InterviewType.MATH:
            return self.get_math_prompt(solution, session_history)
        elif self.interview_type == InterviewType.TEAM_FIT:
            return self.get_team_fit_prompt(solution, session_history)
        elif self.interview_type == InterviewType.CODE:
            return self.get_code_prompt(solution, session_history)
        return "Default prompt"

    def get_math_prompt(self, solution: Dict[str, Any], session_history: list) -> str:
        # Implement math interview specific prompts
        # This logic could be extended to consider session history, the specific state, etc.
        if self.state == InterviewState.SESSION_START:
            if str(self.action) == "paraphrasing":
                prompt = MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE.format(
                    question=solution["initial_question"].replace("{", "").replace("}", "").replace('"', "'")
                )

            elif str(self.action) == "unclarifying":
                prompt = MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE.format(
                    question=solution["initial_question"].replace("{", "").replace("}", "").replace('"', "'")
                )
            # if speaker == "evaluatee":
            #     prompt = EVALUATEE_STATE_EXP_PROMPT_TEMPLATE.format(question=solution["revised_question"])
        elif self.state == InterviewState.CLARIFICATION_NEEDED:
            return EVALUATOR_STATE_UNC_PROMPT_TEMPLATE.format(
                initial_question=solution["initial_question"],
                revised_question=solution["revised_question"],
                deleted_information=solution["deleted_information"],
                Dialogue_History="\n".join(session_history),
            )
        elif self.state == InterviewState.QUESTION_SOLVING:
            if self.attempts == 0:
                prompt = EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE.format(
                    question=solution["initial_question"],
                    answer=solution["answer"],
                    solution=solution["solution"],
                    model_history="\n".join(session_history[-6:-1])[-3000:],
                    model_output=session_history[-1],
                )
            else:
                indices = [-2 * i - 2 for i in range(EXP.cnt + 1)]
                # Select the corresponding elements from session_history
                selected_history = [session_history[i] for i in indices if i >= -len(session_history)]

                prompt = EVALUATOR_STATE_EXP_1_PROMPT_TEMPLATE.format(
                    question=solution["initial_question"],
                    answer=solution["answer"],
                    solution=solution["solution"],
                    model_history="\n".join(selected_history)[-3000:],
                    model_output=session_history[-1],
                )
            return prompt
        elif self.state == InterviewState.FOLLOW_UP_QUESTION_SOLVING
            if str(self.action) == "guess":
                prompt = EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE.format(
                    question=session_history[-2],
                    Dialogue_History=session_history[-1],
                )
            elif str(self.action) == "misinterpret":
                prompt = EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE.format(
                initial_question=solution["initial_question"],
                solution=solution["solution"],
                Dialogue_History=session_history[-1],
            )
            return prompt
        elif self.state == SOLVE_FAIL:
            try:
                prompt = EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.format(
                    question=solution["initial_question"],
                    answer=solution["answer"],
                    solution=solution["solution"],
                    Dialogue_History="\n".join([session_history[-5], session_history[-3], session_history[-1]]),
                )
            except IndexError:
                prompt = EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.format(
                    question=solution["initial_question"],
                    answer=solution["answer"],
                    solution=solution["solution"],
                    Dialogue_History="\n".join([session_history[-3], session_history[-1]]),
                )
            except KeyError as e:
                raise ValueError(f"Missing key in solution dictionary: {e}")

    def get_team_fit_prompt(self, solution: Dict[str, Any], session_history: list, self.action: str = None) -> str:
        # Implement team fit interview specific prompts
        return "Team fit interview prompt"

    def get_code_prompt(self, solution: Dict[str, Any], session_history: list, self.action: str = None) -> str:
        # Implement code interview specific prompts
        return "Code interview prompt"

    def extract_message(self, solution: Dict[str, Any],message: str) -> Tuple[str, str]:
        if self.state == InterviewState.CLARIFICATION_NEEDED:
            message_json = extract_json(message)
            try:
                return message_json["feedback"], message_json["status"]
            except:
                fact = solution["revised_question"]
                return f"You need the fact that {fact}", "complete"
        elif self.state == InterviewState.QUESTION_SOLVING:
            message_json = extract_json(message)
            return message_json["feedback"], message_json["status"]
        elif self.state == InterviewState.MOVING_TO_NEXT_QUESTION:
            if self.success:
                return "You successfully solved the problem! Good job.", "complete-seed"
            else:
                return "This problem seems difficult. Let's move on to an easier one.", "fail"
        elif self.state == InterviewState.QUESTION_COMPLETE:
            return "\n**Question Complete**\n", None
        elif self.state == InterviewState.EVALUATION_COMPLETE:
            return "\n**Evaluation Complete**\n", None
        return "Default message", "default_status"


# Usage example
state_machine = StateMachine(InterviewType.MATH)
solution = {...}  # Your solution dictionary
session_history = [...]  # Your session history list

while state_machine.state != InterviewState.EVALUATION_COMPLETE:
    prompt = state_machine.get_prompt(solution, session_history)
    # Use the prompt to get a response
    response = get_response(prompt)  # Implement this function
    message, status = state_machine.extract_message(response)
    state_machine.transition(status, threshold=3)
    session_history.append(response)
