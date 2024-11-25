import json
import re

from json_repair import repair_json
from math_reasoning.prompt import MATH_EVALUATOR_STATE_UNC_0_PROMPT_TEMPLATE, MATH_GRADER_PROMPT_TEMPLATE
from src.models import ChatModel
from src.utils import extract_json
from stem.prompt import (
    STEM_GRADER_0_PRECISION_PROMPT_TEMPLATE,
    STEM_GRADER_0_PROMPT_TEMPLATE,
    STEM_GRADER_0_RECALL_PROMPT_TEMPLATE,
    STEM_GRADER_1_PRECISION_PROMPT_TEMPLATE,
    STEM_GRADER_1_PROMPT_TEMPLATE,
    STEM_GRADER_1_RECALL_PROMPT_TEMPLATE,
)


def grader_math(query, model_output, model="gpt-4o"):
    prompt = MATH_GRADER_PROMPT_TEMPLATE.format(
        question=query["revised_question"], answer=query["answer"], solution=query["solution"], history=model_output
    )
    if type(model) == str:
        grader = ChatModel.create_model(model)
    else:
        grader = model
    output = grader.invoke(prompt)
    return output


def grader_stem(query, history, model="gpt-4o", attempt=0, assessment=None, recall=False):
    if type(model) == str:
        grader = ChatModel.create_model(model)
    else:
        grader = model
    if recall:
        if attempt == 0:
            prompt = STEM_GRADER_0_RECALL_PROMPT_TEMPLATE.format(
                question=query["revised_question"], solution=query["solution_atom"], history=assessment
            )

            output = grader.invoke(prompt)
            return output
        else:
            prompt = STEM_GRADER_1_RECALL_PROMPT_TEMPLATE.format(
                question=query["revised_question"], feedback=history[-2], correction=history[-1], solution=assessment
            )

            output = grader.invoke(prompt)
            return output
    else:
        if attempt == 0:
            #     prompt = STEM_GRADER_0_PRECISION_PROMPT_TEMPLATE.format(question = query['revised_question'],
            #     solution = query['solution'],history = history[-1] )
            #     grader = ChatModel.create_model(model)
            #     output = grader.invoke(prompt)
            #     return output.content
            prompt = STEM_GRADER_0_PRECISION_PROMPT_TEMPLATE.format(
                question=query["revised_question"], solution=query["solution"], history=history[-1]
            )

            output = grader.invoke(prompt)
            return output
        else:
            prompt = STEM_GRADER_1_PRECISION_PROMPT_TEMPLATE.format(
                question=query["revised_question"],
                feedback=history[-2],
                correction=history[-1],
                solution=query["solution"],
                history=assessment,
            )

            output = grader.invoke(prompt)
            return output


def acc_counter_stem(query, recall=False, followup=False):

    if type(query) == str:
        query = repair_json(query)
        try:
            query = json.loads(query)
        except:
            query = extract_json(query)
    fine_scores = 0
    if recall:
        if type(query) == dict:
            try:
                total_facts = len(query["reference_facts"])
                correct_facts = sum(1 for fact in query["reference_facts"].values() if fact["label"] == "supported")
                correct_facts += sum(
                    0.5 for fact in query["reference_facts"].values() if fact["label"] == "partially supported"
                )
                # base_rubric = {'high':1,'middle':0,'low':-1}
                # redun_rubric = {'low':1,'middle':0,'high':-1}

                # for i in query['assessment']:
                #     if i != 'redundancy':
                #         score =  base_rubric[query['assessment'][i]['label']]
                #         fine_scores += score
                #     if i == 'redundancy':
                #         score =  redun_rubric[query['assessment'][i]['label']]
                #         fine_scores += score
                return correct_facts / total_facts  # , fine_scores/len(query['assessment'])]
            except:

                return 0

    if followup:
        if type(query) == dict:
            try:
                total_facts = len(query["follow-up question"])
                correct_facts = sum(
                    1 for fact in query["follow-up question"].values() if fact["correctness"] == "correct"
                )
                correct_facts += sum(
                    0.5 for fact in query["follow-up question"].values() if fact["correctness"] == "partially correct"
                )
                # base_rubric = {'high':1,'middle':0,'low':-1}
                # redun_rubric = {'low':1,'middle':0,'high':-1}

                # for i in query['assessment']:
                #     if i != 'redundancy':
                #         score =  base_rubric[query['assessment'][i]['label']]
                #         fine_scores += score
                #     if i == 'redundancy':
                #         score =  redun_rubric[query['assessment'][i]['label']]
                #         fine_scores += score
                return correct_facts / total_facts  # , fine_scores/len(query['assessment'])]
            except:

                return 0

        pass
    else:
        if type(query) == list:
            query = query[0]
        if type(query) == dict:
            try:
                total_facts = len(query["model_atomic_facts"])

                correct_facts = sum(1 for fact in query["model_atomic_facts"] if fact["correctness"] == "correct")
                try:
                    supported_facts = sum(
                        1 for fact in query["model_atomic_facts"] if fact["reference solution coverage"] == "supported"
                    )
                except:
                    try:
                        supported_facts = sum(
                            1
                            for fact in query["model_atomic_facts"]
                            if fact["reference_solution_coverage"] == "supported"
                        )
                    except:
                        supported_facts = 0
                base_rubric = {"high": 1, "middle": 0, "low": -1}
                redun_rubric = {"low": 1, "middle": 0, "high": -1}

                for i in query["assessment"]:
                    if i != "redundancy":
                        score = base_rubric[query["assessment"][i]["label"]]
                        fine_scores += score
                    if i == "redundancy":
                        score = redun_rubric[query["assessment"][i]["label"]]
                        fine_scores += score
                return total_facts, [correct_facts / total_facts, fine_scores / len(query["assessment"])]
            except:
                return 0, [0]
        elif type(query) == str:
            query = query.replace("'", '"')
            total_facts = len(re.findall(r'"fact_number":\s*\d+', query))
            # Count correct atomic facts (by counting occurrences of "decision": "correct")
            correct_facts = len(re.findall(r'"correctness":\s*"correct"', query))
            correct_facts += len(re.findall(r'"correctness":\s*"partially correct"', query))
            supported_facts = len(re.findall(r'"reference solution coverage":\s*"supported"', query))
            supported_facts += len(re.findall(r'"reference solution coverage":\s*"partially supported"', query))
            supported_facts = len(re.findall(r'"reference_solution_coverage":\s*"supported"', query))
            supported_facts += len(re.findall(r'"reference_solution_coverage":\s*"partially supported"', query))
            labels = re.findall(r"'(completeness|redundancy|readability|depth)':\s*\{'label':\s*'(\w+)'", str(query))
            try:
                for i in labels:
                    if i[0] != "redundancy":
                        score = base_rubric[i[1]]
                        fine_scores += score
                    if i[0] == "redundancy":
                        score = redun_rubric[i[1]]
                        fine_scores += score

                return total_facts, [correct_facts / total_facts]  # ,fine_scores/4]
            except:
                try:
                    return total_facts, correct_facts / total_facts  # ,0
                except:
                    return 0, [0]
    return 0


def uncer_math(solution, model_output, model="gpt-4o"):
    prompt = MATH_EVALUATOR_STATE_UNC_0_PROMPT_TEMPLATE.format(
        initial_question=f"""{solution['initial_question']}""",
        revised_question=f"""{solution['revised_question']}""",
        deleted_information=f"""{solution['deleted_information']}""",
        solution=f"""{solution['solution']}""",
        answer=f"""{solution['answer']}""",
        Dialogue_History=model_output,
        explanation=f"""{solution['explanation']}""",
    )
    uncer = ChatModel.create_model(model)
    output = uncer.invoke(prompt)
    return output
