from random import randint

from src.utils import extract_json

from .prompt import (
    EVALUATEE_STATE_EXP_PROMPT_TEMPLATE,
    EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE,
    EVALUATOR_STATE_EXP_1_PROMPT_TEMPLATE,
    EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE,
    EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE,
    EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE,
    EVALUATOR_STATE_UNC_PROMPT_TEMPLATE,
    MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE,
    MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE,
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
        if state.cnt == threshold:
            state = EXP
            state.cnt = 0
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

    elif state == INS_CONCEPT:

        if state.cnt == 1:
            if str(action).lower() == "complete":
                state = SUCCESS
            else:
                state = FAIL_INS
            state.cnt = 0
        if str(action).lower() == "complete":
            state = SUCCESS
            state.cnt = 0
        else:
            state = FAIL_INS
            state.cnt = 0
    elif state == INS_REASK:
        if state.cnt == 1:
            if str(action).lower() == "complete":
                state = SUCCESS
            else:
                state = FAIL_INS
            state.cnt = 0
        if str(action).lower() == "complete":
            state = SUCCESS
            state.cnt = 0
        else:
            state = FAIL_INS
            state.cnt = 0
    elif state == FAIL:
        if str(action).lower() in ["guess"]:
            state = INS_CONCEPT
            state.cnt = 0
        elif str(action).lower() in ["misinterpret"]:
            state = INS_REASK
            state.cnt = 0
        else:
            state = FIN
            state.cnt = 2
        # else:
        #     state = EXP
        #     state.cnt = 0
    elif state == FAIL_INS:

        state = FIN
        state.cnt = 0
    elif state == SUCCESS:
        if str(action).lower() == "complete":
            state = FIN
            state.cnt = 0

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
                question=solution["initial_question"].replace("{", "").replace("}", "").replace('"', "'")
            )

        elif action == "unclarifying":
            prompt = MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE.format(
                question=solution["initial_question"].replace("{", "").replace("}", "").replace('"', "'")
            )
        if speaker == "evaluatee":
            prompt = EVALUATEE_STATE_EXP_PROMPT_TEMPLATE.format(question=solution["revised_question"])
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

    def extract_message(message, solution=None, cnt=None):
        if cnt == 2:
            return message_json["feedback"], message_json["status"]
        message_json = extract_json(message)

        try:
            return message_json["feedback"], message_json["status"]
        except:
            fact = solution["revised_question"]
            return f"You need the fact that {fact}", "complete"


class EXP:  # explore
    name = "EXP"
    cnt = 0

    def prompt(solution, session_history, action=None):

        if EXP.cnt == 0:
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

    def extract_message(message, solution=None, cnt=None):
        message_json = extract_json(message)

        return message_json["feedback"], message_json["status"]


class INS_CONCEPT:  # insight
    name = "INS_CONCEPT"
    cnt = 0

    def prompt(solution, session_history, action=None):
        prompt = EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE.format(
            question=session_history[-2],
            Dialogue_History=session_history[-1],
        )
        return prompt

    def extract_message(message, solution=None, cnt=None):
        message_json = extract_json(message)
        return message_json["feedback"], message_json["status"]


class INS_REASK:  # insight
    name = "INS_REASK"
    cnt = 0

    def prompt(solution, session_history, action=None):
        prompt = EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE.format(
            initial_question=solution["initial_question"],
            solution=solution["solution"],
            Dialogue_History=session_history[-1],
        )
        return prompt

    def extract_message(message, solution=None, cnt=None):
        message_json = extract_json(message)
        return message_json["feedback"], message_json["status"]


class FAIL:  # action
    name = "ACT-FAIL"
    cnt = 0

    def prompt(solution, session_history, action=None):
        try:
            prompt = EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.format(
                question=solution["initial_question"],
                answer=solution["answer"],
                solution=solution["solution"],
                Dialogue_History="\n".join([session_history[-5], session_history[-3], session_history[-1]]),
            )
        except:
            prompt = EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.format(
                question=solution["initial_question"],
                answer=solution["answer"],
                solution=solution["solution"],
                Dialogue_History="\n".join([session_history[-3], session_history[-1]]),
            )
        return prompt

    def extract_message(message, solution=None, cnt=None):
        message_json = extract_json(message)
        return message_json["feedback"], message_json["error_type"]


class FAIL_INS:  # action
    name = "INS-FAIL"
    cnt = 0

    def extract_message(message, solution=None, cnt=None):
        return "I think this problem is difficult for you. Let's move on to the easy one", "fail"


class SUCCESS:  # action
    name = "ACT-SUCCESS"
    cnt = 0

    def extract_message(message, solution=None, cnt=None):
        return "You successfully solve the problem ! Good Job.", "complete"


class FIN:  # fin
    name = "FIN"
    cnt = 0

    def extract_message(message, solution=None, cnt=None):
        return "\n**Session Ends**\n", None


class FIN_OVERALL:  # fin
    name = "FIN_OVERALL"
    cnt = 0

    def prompt(solution, session_history, action=None):
        return "\n**Evaluation Ends**\n", None
