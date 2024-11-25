from random import randint

from src.utils import extract_json

from .prompt import (
    STEM_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE,
    STEM_EVALUATOR_STATE_EXP_PROMPT_TEMPLATE,
    STEM_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE,
    STEM_MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE,
    STEM_MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE,
)


def state_transition(state, action, threshold):
    if state == INIT:
        if action in ["paraphrasing", None]:
            state = EXP
            state.cnt = 0
        elif action in ["unclarifying"]:
            state = UNC
            state.cnt = 0
        elif action in ["query_finished"]:
            state = FIN_OVERALL
            state.cnt = 0
        else:
            state.cnt += 1
    elif state == UNC:

        if str(action).lower() == "complete":
            state = EXP
            state.cnt = 0
        else:
            state.cnt += 1
    elif state == EXP:
        if state.cnt == threshold:
            state = FAIL
            state.cnt = 0
        if str(action).lower() == "complete":
            state = SUCCESS
            state.cnt = 0

        else:
            state.cnt += 1
    elif state == FAIL:
        if str(action).lower() == "fail":
            state = FIN
            state.cnt = 0
    elif state == SUCCESS:
        if str(action).lower() == "complete-seed":
            state = FIN
            state.cnt = 0
        if str(action).lower() == "complete-":
            state = FIN
            state.cnt = 0
    elif state == INS:
        if state.cnt == threshold:
            state = FAIL
            state.cnt = 0
        if str(action).lower() == "complete":
            state = SUCCESS
            state.cnt = 0
        else:
            state.cnt += 1
    elif state == FIN:
        return INIT
    return state


class INIT:  # initial
    name = "INIT"
    cnt = 0

    def action():
        action_set = ["paraphrasing", "unclarifying", None]
        i = randint(0, 2)
        action = action_set[i]
        return action

    def prompt(solution, action, speaker=None):
        if action == "paraphrasing":
            prompt = MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE.format(
                question=solution["initial_question"]
                .replace("{", "")
                .replace("}", "")
                .replace('"', "'")
            )

        elif action == "unclarifying":
            prompt = MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE.format(
                question=solution["initial_question"]
                .replace("{", "")
                .replace("}", "")
                .replace('"', "'")
            )
        if speaker == "evaluatee":
            prompt = EVALUATEE_STATE_EXP_PROMPT_TEMPLATE.format(
                question=solution["revised_question"]
            )
        return prompt


class UNC:  # unclarify
    name = "UNC"
    cnt = 0

    def prompt(solution, session_history, action=None):
        prompt = EVALUATOR_STATE_UNC_PROMPT_TEMPLATE.format(
            initial_question=solution["initial_question"],
            revised_question=solution["revised_question"],
            deleted_information=solution["deleted_information"],
            Dialogue_History="\n".join(session_history),
        )
        return prompt

    def extract_message(message):
        message_json = extract_json(message)
        return message_json["answer"], message_json["status"]


class EXP:  # explore
    name = "EXP"
    cnt = 0

    def prompt(solution, session_history, action=None):
        prompt = EVALUATOR_STATE_EXP_PROMPT_TEMPLATE.format(
            question=solution["initial_question"],
            answer=solution["answer"],
            solution=solution["solution"],
            model_history="\n".join(session_history[-4:-1][-3000:]),
            model_output=session_history[-1],
        )
        return prompt

    def extract_message(message):
        message_json = extract_json(message)

        return message_json["feedback"], message_json["status"]


class INS:  # insight
    name = "INS"
    cnt = 0

    def prompt(solution, session_history, action=None):
        return str

    def extract_message(message):
        return str


class FAIL:  # action
    name = "ACT-FAIL"
    cnt = 0

    def extract_message(message):
        return (
            "I think this problem is difficult for you. Let's move on to the easy one",
            "fail",
        )


class SUCCESS:  # action
    name = "ACT-SUCCESS"
    cnt = 0

    def extract_message(message):
        return "You successfully solve the problem ! Good Job.", "complete-seed"


class FIN:  # fin
    name = "FIN"
    cnt = 0

    def extract_message(message):
        return "\n**Session Ends**\n", None


class FIN_OVERALL:  # fin
    name = "FIN_OVERALL"
    cnt = 0

    def prompt(solution, session_history, action=None):
        return "\n**Evaluation Ends**\n", None
