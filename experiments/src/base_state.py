# base_states.py: Base class for all states

import os
from enum import Enum, auto
from random import randint
from typing import Any, Callable, Dict, Tuple

from math_reasoning.prompt import (
    MATH_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_EXP_1_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE,
    MATH_EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_0_QUESTION_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_1_QUESTION_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE,
    MATH_MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE,
    MATH_MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE,
)
from src.base_grader import acc_counter_stem, grader_math, grader_stem, uncer_math
from src.utils import extract_json
from stem.prompt import (
    STEM_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE,
    STEM_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE,
    STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_1_PROMPT_TEMPLATE,
    STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_2_PROMPT_TEMPLATE,
    STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_PROMPT_TEMPLATE,
    STEM_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE,
    STEM_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE,
    STEM_MODERATOR_STATE_INIT_ADDING_PROMPT_TEMPLATE,
    STEM_MODERATOR_STATE_INIT_MODIFYING_PROMPT_TEMPLATE,
    STEM_MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE,
)


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
    STEM = auto()
    CODE = auto()


class StateMachine:
    def __init__(self, interview_type: InterviewType):
        self.state = InterviewState.SESSION_START
        self.interview_type = interview_type
        self.attempts = 0
        self.success = []
        self.success_followup = []
        self.TF = []
        self.error_types = []
        self.feedback_types = []
        self.follow_up_types = [""]
        self.cost_grader = []
        self.recall = 0

    def init_action(self, init_action):
        if init_action != None:
            self.action = init_action
        else:
            if self.interview_type.name == "MATH":
                action_set = ["paraphrasing", "unclarifying", "None"]
                i = randint(0, 2)
                self.action = action_set[i]
            if self.interview_type.name == "STEM":
                action_set = ["paraphrasing", "modifying", "adding" "None"]
                i = randint(0, 2)
                self.action = action_set[i]
        print(self.action)

    def transition(self, action, threshold: int, followup_threshold: int, followup_flag: int) -> None:
        if action:
            self.action = action

        if self.state == InterviewState.SESSION_START:
            self.attempts += 1
            if str(self.action) in ["paraphrasing", "None", "modifying", "adding"]:
                self.state = InterviewState.QUESTION_SOLVING
                self.attempts = 0
            elif str(self.action) == "unclarifying":
                self.state = InterviewState.CLARIFICATION_NEEDED
                self.attempts = 0
            elif str(self.action) == "query_finished":
                self.state = InterviewState.EVALUATION_COMPLETE
                self.attempts = 0

        elif self.state == InterviewState.CLARIFICATION_NEEDED:
            self.attempts += 1
            if str(self.action).lower() == "complete":
                self.state = InterviewState.QUESTION_SOLVING
                self.attempts = 0
            elif self.attempts == threshold:
                self.state = InterviewState.QUESTION_SOLVING
                self.attempts = 0

        elif self.state == InterviewState.QUESTION_SOLVING:

            self.attempts += 1
            if self.interview_type.name == "MATH":
                if str(self.action).lower() == "complete":
                    self.state = InterviewState.SOLVE_SUCCESS
                    self.success.append(1)
                    self.attempts = 0
                elif self.attempts == threshold:
                    self.state = InterviewState.SOLVE_FAIL
                    self.success.append(0)
                    self.attempts = 0

            if self.interview_type.name == "STEM":

                if str(self.action).lower() == "complete":
                    self.state = InterviewState.SOLVE_SUCCESS
                    self.attempts = 0
                    self.success.append(1)
                elif self.attempts == threshold:
                    self.state = InterviewState.SOLVE_FAIL

                    self.attempts = 0

                # if self.interview_type.name == "MATH":
                #     if str(self.action).lower() in ["guess","misinterpret"]:
                #         self.state = InterviewState.FOLLOW_UP_QUESTION_SOLVING
                #         self.attempts = 0
                #     else:
                #         self.state = InterviewState.MOVING_TO_NEXT_QUESTION
                #         self.attempts = 0

        elif self.state == InterviewState.SOLVE_SUCCESS:

            if followup_flag:
                if self.interview_type.name == "MATH":
                    self.state = InterviewState.FOLLOW_UP_QUESTION_SOLVING
                elif self.interview_type.name == "STEM":
                    self.state = InterviewState.FOLLOW_UP_QUESTION_SOLVING

            else:
                self.state = InterviewState.QUESTION_COMPLETE
            self.attempts = 0
        elif self.state == InterviewState.SOLVE_FAIL:
            self.attempts += 1

            if followup_flag:
                if self.interview_type.name == "MATH":
                    self.success.append(0)
                    if str(self.action).lower() in ["concept", "misinterpret"]:
                        self.state = InterviewState.FOLLOW_UP_QUESTION_SOLVING
                    else:
                        self.state = InterviewState.QUESTION_COMPLETE

                elif self.interview_type.name == "STEM":
                    self.state = InterviewState.FOLLOW_UP_QUESTION_SOLVING

            else:
                self.state = InterviewState.QUESTION_COMPLETE
            self.attempts = 0

        elif self.state == InterviewState.FOLLOW_UP_QUESTION_SOLVING:
            self.attempts += 1
            # attempt_threshold = 2 if self.success[-1] else 1
            if self.interview_type.name == "MATH":
                if str(self.action).lower() == "complete":
                    self.success_followup.append(1)
                elif str(self.action).lower() == "partially_complete":
                    self.success_followup.append(0.5)
            if self.interview_type.name == "STEM":
                self.success_followup.append(self.action)
            if (self.attempts == followup_threshold) or (self.success_followup[-1] == 1):
                self.state = InterviewState.QUESTION_COMPLETE
                self.attempts = 0
        elif self.state == InterviewState.QUESTION_COMPLETE:

            self.state = InterviewState.SESSION_START
            self.attempts = 0
        return self.state

    def get_prompt(self, solution: Dict[str, Any], session_history: list, model="gpt-4o") -> str:
        if self.interview_type == InterviewType.MATH:
            return self.get_math_prompt(solution, session_history, model)
        elif self.interview_type == InterviewType.STEM:
            return self.get_stem_prompt(solution, session_history, model)

        return "Default prompt"

    def get_initial_prompt(self, solution: Dict[str, Any]) -> str:
        # initial prompt for evaluatee
        if self.interview_type == InterviewType.MATH:
            prompt = MATH_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE.format(question=f"""{solution['revised_question']}""")
        elif self.interview_type == InterviewType.STEM:
            prompt = STEM_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE.format(question=f"""{solution['revised_question']}""")
        return prompt

    def get_math_prompt(self, solution: Dict[str, Any], session_history: list, model) -> str:
        # Implement math interview specific prompts
        # This logic could be extended to consider session history, the specific state, etc.
        if self.state == InterviewState.SESSION_START:

            inital_question = f"""{solution['initial_question']}""".replace('"', "'")
            if str(self.action) == "paraphrasing":
                prompt = MATH_MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE.format(
                    question=f"'''{inital_question}'''"
                )

            elif str(self.action) == "unclarifying":
                prompt = MATH_MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE.format(
                    question=f"""{inital_question}""", solution=f"""{solution['solution']}"""
                )
            return prompt
            # if speaker == "evaluatee":
            #     prompt = EVALUATEE_STATE_EXP_PROMPT_TEMPLATE.format(question=f'''{solution['revised_question']}''')

        elif self.state == InterviewState.CLARIFICATION_NEEDED:
            evaluation = uncer_math(solution, session_history[-1], model)
            self.cost_grader.append(evaluation.usage_metadata)
            prompt = MATH_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE.format(
                initial_question=f"""{solution['initial_question']}""",
                revised_question=f"""{solution['revised_question']}""",
                feedback=evaluation.content,
                deleted_information=f"""{solution['deleted_information']}""",
                solution=f"""{solution['solution']}""",
                answer=f"""{solution['answer']}""",
                Dialogue_History=session_history[-1],
                explanation=f"""{solution['explanation']}""",
            )
            return prompt
        elif self.state == InterviewState.QUESTION_SOLVING:
            evaluation = grader_math(solution, session_history[-1], model)
            evaluation_json = extract_json(evaluation.content)
            self.cost_grader.append(evaluation.usage_metadata)
            if type(evaluation_json) == str:
                evaluation_json = extract_json(evaluation_json)

            try:
                self.TF.append(evaluation_json)
                TF_answer = evaluation_json["answer correctness"]
                TF_solution = evaluation_json["solving process correctness"]
                error_type = evaluation_json["error type"]
                self.error_types.append(error_type)
                explanation = evaluation_json["explanation"]
                del evaluation_json["error type"]
                if (TF_answer.lower() == "true") and (TF_solution.lower() == "true"):
                    self.action = "complete"
                else:
                    self.action = "incomplete"
            except:
                self.TF.append(evaluation.content)
                self.action = "incomplete"

            if self.attempts == 0:
                prompt = MATH_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE.format(
                    question=f"""{solution['initial_question']}""",
                    solution=f"""{solution['solution']}""",
                    answer=f"""{solution['answer']}""",
                    evaluation=evaluation.content,
                    model_history="\n".join(session_history[-6:-1])[-3000:],
                    model_output=session_history[-1],
                )
            else:
                indices = [-2 * i - 2 for i in range(self.attempts + 1)]
                # Select the corresponding elements from session_history
                selected_history = [session_history[i] for i in indices if i >= -len(session_history)]

                prompt = MATH_EVALUATOR_STATE_EXP_1_PROMPT_TEMPLATE.format(
                    question=f"""{solution['initial_question']}""",
                    answer=f"""{solution['answer']}""",
                    solution=f"""{solution['solution']}""",
                    model_history="\n".join(selected_history)[-3000:],
                    evaluation=evaluation.content,
                    model_output=session_history[-1],
                )
            return prompt
        elif self.state == InterviewState.FOLLOW_UP_QUESTION_SOLVING:
            if self.success[-1]:
                self.prev_action = self.action
                # if "answer" in str(self.action):

                prompt = MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_0_QUESTION_PROMPT_TEMPLATE.format(
                    initial_question=f"""{solution['initial_question']}""",
                    solution=f"""{solution['solution']}""",
                    seed_answer=f"""{solution['answer']}""",
                    Dialogue_History="\n".join(session_history[-6:-1])[-3000:],
                    answer=self.prev_action,
                    question=session_history[-2],
                    model_output=session_history[-1],
                    model_solution=session_history[-3],
                )
                # else:
                #     indices = [-2 * i - 2 for i in range(self.attempts + 1)]
                #     selected_history = [session_history[i] for i in indices if i >= -len(session_history)]
                #     prompt = MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_1_QUESTION_PROMPT_TEMPLATE.format(
                #         initial_question=f'''{solution['initial_question']}''',
                #         solution=f'''{solution['solution']}''',
                #         Dialogue_History=selected_history,
                #         model_solution = session_history[-1]
                #     )
            else:
                if str(self.action) == "concept":
                    self.prev_action = self.action
                    prompt = MATH_EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE.format(
                        question=session_history[-2],
                        answer=f"""{solution['answer']}""",
                        solution=f"""{solution['solution']}""",
                        Dialogue_History="\n".join(session_history[-6:-1])[-3000:],
                        response=session_history[-1],
                    )
                elif str(self.action) == "misinterpret":
                    self.prev_action = self.action
                    prompt = MATH_EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE.format(
                        initial_question=f"""{solution['initial_question']}""",
                        answer=f"""{solution['answer']}""",
                        solution=f"""{solution['solution']}""",
                        Dialogue_History="\n".join(session_history[-6:-1])[-3000:],
                        response=session_history[-1],
                    )
                else:
                    if str(self.prev_action) == "concept":
                        prompt = MATH_EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE.format(
                            question=session_history[-2],
                            answer=f"""{solution['answer']}""",
                            solution=f"""{solution['solution']}""",
                            Dialogue_History="\n".join(session_history[-6:-1])[-3000:],
                            response=session_history[-1],
                        )
                    elif str(self.prev_action) == "misinterpret":

                        prompt = MATH_EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE.format(
                            initial_question=f"""{solution['initial_question']}""",
                            answer=f"""{solution['answer']}""",
                            solution=f"""{solution['solution']}""",
                            Dialogue_History="\n".join(session_history[-6:-1])[-3000:],
                            response=session_history[-1],
                        )

            return prompt
        elif self.state == InterviewState.SOLVE_FAIL:

            try:
                prompt = MATH_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.format(
                    question=f"""{solution['initial_question']}""",
                    answer=f"""{solution['answer']}""",
                    solution=f"""{solution['solution']}""",
                    error_type=self.error_types[-1],
                    Dialogue_History="\n".join([session_history[-5], session_history[-3], session_history[-1]]),
                )
            except IndexError:
                prompt = MATH_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.format(
                    question=f"""{solution['initial_question']}""",
                    answer=f"""{solution['answer']}""",
                    solution=f"""{solution['solution']}""",
                    error_type=self.error_types[-1],
                    Dialogue_History="\n".join([session_history[-3], session_history[-1]]),
                )
            return prompt
        elif self.state == InterviewState.SOLVE_SUCCESS:
            indices = [-2 * i - 2 for i in range(self.attempts + 1)]
            selected_history = [session_history[i] for i in indices if i >= -len(session_history)]
            prompt = MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_1_QUESTION_PROMPT_TEMPLATE.format(
                initial_question=f"""{solution['initial_question']}""",
                answer=f"""{solution['answer']}""",
                solution=f"""{solution['solution']}""",
                Dialogue_History=selected_history,
                model_solution=session_history[-1],
            )
            return prompt
        return ""

    def get_stem_prompt(
        self, solution: Dict[str, Any], session_history: list, action: str = None, model="gpt-4o"
    ) -> str:
        if self.state == InterviewState.SESSION_START:
            inital_question = f"""{solution['initial_question']}""".replace('"', "'")
            if str(self.action) == "paraphrasing":
                prompt = STEM_MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE.format(
                    question=f"'''{inital_question}'''"
                )

            elif str(self.action) == "modifying":
                prompt = STEM_MODERATOR_STATE_INIT_MODIFYING_PROMPT_TEMPLATE.format(
                    question=f"""{inital_question}""", solution=f"""{solution['solution']}"""
                )

            elif str(self.action) == "adding":
                prompt = STEM_MODERATOR_STATE_INIT_ADDING_PROMPT_TEMPLATE.format(
                    question=f"""{inital_question}""", solution=f"""{solution['solution']}"""
                )
            return prompt
            # if speaker == "evaluatee":
            #     prompt = EVALUATEE_STATE_EXP_PROMPT_TEMPLATE.format(question=f'''{solution['revised_question']}''')

        elif self.state == InterviewState.QUESTION_SOLVING:
            if self.attempts == 0:
                evaluation = grader_stem(solution, session_history, attempt=self.attempts, recall=False, model=model)
                self.cost_grader.append(evaluation.usage_metadata)
            else:
                # if self.TF_answer:
                #     evaluation = grader_stem(solution,session_history, attempt=self.attempts,model_output = self.TF_answer,recall=True)
                # else:
                evaluation = grader_stem(
                    solution, session_history, attempt=self.attempts, assessment=self.TF[-1], recall=False, model=model
                )
                self.cost_grader.append(evaluation.usage_metadata)
            evaluation_json = extract_json(evaluation.content)
            if type(evaluation_json) == str:
                evaluation_json = extract_json(evaluation_json)
            try:
                self.TF.append(evaluation_json)
                # self.TF_answer = evaluation_json["model_atomic_facts"]
                # TF_solution = evaluation_json["assessment"]
                acc = acc_counter_stem(evaluation_json)

            except:
                self.TF.append(evaluation.content)
                self.TF_answer = evaluation
                acc = acc_counter_stem(evaluation_json)

            self.success.append(acc)
            print(acc)
            if acc[-1][0] == 1:
                self.action = "complete"
            else:
                self.action = "incomplete"
            prompt = STEM_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE.format(
                question=f"""{solution['revised_question']}""", solution=self.TF[-1], history=session_history[-1]
            )
            return prompt
        elif (self.state == InterviewState.SOLVE_FAIL) or (self.state == InterviewState.SOLVE_SUCCESS):
            grade_recall = grader_stem(
                solution, session_history, attempt=self.attempts, assessment=self.TF[-1], recall=True, model=model
            )
            self.cost_grader.append(grade_recall.usage_metadata)
            self.recall = acc_counter_stem(grade_recall.content, recall=True)
            if self.recall == 1:

                self.state = InterviewState.MOVING_TO_NEXT_QUESTION
                return ""
            else:
                prompt = STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_PROMPT_TEMPLATE.format(
                    question=solution["initial_question"], solution=grade_recall
                )
                return prompt
        elif self.state == InterviewState.FOLLOW_UP_QUESTION_SOLVING:

            #   grade_recall = grader_stem(solution,session_history, attempt=1,assessment = self.TF[-1],recall=True)
            # if acc_counter_stem(grade_recall) == 1:
            #     self.state = InterviewState.MOVING_TO_NEXT_QUESTION
            #     return ""
            if self.attempts == 0:

                prompt = STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_1_PROMPT_TEMPLATE.format(
                    question=solution["initial_question"],
                    solution=solution["solution"],
                    history=session_history[-1],
                    followup=self.folloup_question,
                )
                return prompt
            else:
                prompt = STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_2_PROMPT_TEMPLATE.format(
                    question=solution["initial_question"],
                    solution=solution["solution"],
                    correction=session_history[-1],
                    feedback=session_history[-2],
                    history=self.follow_up_types[-1],
                    followup=self.folloup_question,
                )

                return prompt
        return ""

    def get_code_prompt(self, solution: Dict[str, Any], session_history: list, action: str = None) -> str:
        # Implement code interview specific prompts
        return "Code interview prompt"

    def extract_message(self, solution: Dict[str, Any], message: list) -> str:
        if self.interview_type == InterviewType.MATH:
            return self.extract_math_message(solution, message)

        elif self.interview_type == InterviewType.STEM:
            return self.extract_stem_message(solution, message)
        elif self.interview_type == InterviewType.CODE:
            pass
        return "Default message", "default_status"

    def extract_math_message(self, solution: Dict[str, Any], message: str) -> Tuple[str, str]:
        if self.state == InterviewState.CLARIFICATION_NEEDED:
            message_json = extract_json(message)
            try:
                return message_json["feedback"], message_json["status"]
            except:
                fact = f"""{solution['deleted_information']}"""
                return (
                    f"You need the fact that {fact}, which leads to the question {solution['initial_question']}",
                    "complete",
                )
        elif self.state == InterviewState.QUESTION_SOLVING:
            if self.action == "complete":
                return "You got a correct answer! Good Job.", self.action
            else:
                message_json = extract_json(message)
                try:
                    self.feedback_types.append(message_json["feedback_type"])
                except:
                    pass
                try:
                    return message_json["feedback"], self.action
                except:
                    self.action = "incomplete"
                    return "try again!", self.action
        elif self.state == InterviewState.FOLLOW_UP_QUESTION_SOLVING:
            message_json = extract_json(message)
            try:
                self.follow_up_types.append(message_json["type"])
            except:
                pass
            if "question" in message_json.keys():
                question = message_json["question"]
                answer = message_json["answer"]
                return message_json["question"], f"answer: {answer}"
            else:
                return message_json["feedback"], message_json["status"]
        elif self.state == InterviewState.SOLVE_FAIL:
            message_json = extract_json(message)
            try:
                return message_json["feedback"], self.error_types[-1]
            except:
                return "", self.error_types[-1]

        elif self.state == InterviewState.SOLVE_SUCCESS:
            message_json = extract_json(message)
            try:
                question = message_json["question"]
                answer = message_json["answer"]
                return message_json["question"], f"answer: {answer}"
            except:
                pass

        elif self.state == InterviewState.MOVING_TO_NEXT_QUESTION:
            if self.success[-1]:
                return "You successfully solved the problem! Good job.", "complete-seed"
            else:
                return "This problem seems difficult. Let's move on to an easier one.", "fail"

        elif self.state == InterviewState.QUESTION_COMPLETE:
            return "\n**Question Complete**\n", None
        elif self.state == InterviewState.EVALUATION_COMPLETE:
            return "\n**Evaluation Complete**\n", None
        return "Default message", "default_status"

    def extract_stem_message(self, solution: Dict[str, Any], message: str) -> Tuple[str, str]:
        if self.state == InterviewState.QUESTION_SOLVING:
            if self.action == "complete":
                return "You got a correct explanation! Good Job.", self.action
            else:
                message_json = extract_json(message)
                try:
                    self.feedback_types.append(message_json["assessment"])
                except:
                    pass
                try:
                    return message_json["merged_feedback"], self.action
                except:
                    self.action = "incomplete"

                    return "Your answer contains incorrect explanation. Try it again!", self.action

        elif self.state == InterviewState.SOLVE_SUCCESS:
            message_json = extract_json(message)
            try:
                question = message_json["merged_question"]
                self.folloup_question = question
                return question, None
            except:
                self.folloup_question = None
                pass
        elif self.state == InterviewState.SOLVE_FAIL:

            message_json = extract_json(message)
            try:
                question = message_json["merged_question"]
                self.folloup_question = question
                return question, None
            except:
                self.folloup_question = None
                pass
        elif self.state == InterviewState.FOLLOW_UP_QUESTION_SOLVING:

            message_json = extract_json(message)

            self.action = acc_counter_stem(message_json, followup=True)
            try:
                question = message_json["feedback"]
                try:
                    self.follow_up_types.append(message_json["follow-up question"])
                except:
                    pass
                return question, self.action
            except:
                return "Overall Your explanation lacks depth. Can you explain a bit more?", None
        elif self.state == InterviewState.MOVING_TO_NEXT_QUESTION:
            if self.success[-1]:
                return "You successfully solved the problem! Good job.", "complete-seed"
            else:
                return "This problem seems difficult. Let's move on to an easier one.", "fail"

        elif self.state == InterviewState.QUESTION_COMPLETE:
            return "\n**Question Complete**\n", None
        elif self.state == InterviewState.EVALUATION_COMPLETE:
            return "\n**Evaluation Complete**\n", None
        return "Default message", "default_status"
