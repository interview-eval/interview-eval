import argparse
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_openai import AzureChatOpenAI
from langchain_together import ChatTogether
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
from tokenizers.pre_tokenizers import Whitespace


class Interviewer:
    def __init__(self, model_name):
        self.model_name = model_name

    def invoke(self, prompt):
        prompt = prompt[0].content
        import pdb

        pdb.set_trace()
        if "math-interviewer" in self.model_name:
            if prompt == MATH_MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE.format(
                question="question"
            ):
                return "Question: modified question"
            if prompt == MATH_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE.format(
                initial_question="init_query",
                revised_question="Question: modified question",
                feedback="feedback",
                deleted_information="deleted_information",
                solution="solution",
                answer="answer",
                Dialogue_History="history",
                explanation="explanation",
            ):
                return """{
    "deleted_information": "deleted_information",
    "explanation": "explanation",
    "revised_question": "revised_question"
    "feedback": "feedback",   
    "status": "complete"
}"""
            if prompt == MATH_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE.format(
                question="Question: modified question",
                solution="solution",
                answer="answer",
                evaluation="evaluation",
                model_history="history",
                model_output="answer",
            ):
                return """{
    "status": "incomplete",
    "feedback": "feeback"
}"""
            if prompt == MATH_EVALUATOR_STATE_EXP_1_PROMPT_TEMPLATE.format(
                question="Question: modified question",
                solution="solution",
                answer="answer",
                evaluation="evaluation",
                model_history="history",
                model_output="answer",
            ):
                return """{"feedback": "feedback","feedback_type": "feedback_type"}"""

            if (
                prompt
                == MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_0_QUESTION_PROMPT_TEMPLATE.format(
                    initial_question="Question: modified question",
                    solution="solution",
                    seed_answer="answer",
                    Dialogue_History="history",
                    answer="answer",
                    question="question",
                    model_output="answer",
                    model_solution="solution",
                )
            ):
                return """{"status" : "incomplete","feedback": "feedback"}"""
            if (
                prompt
                == MATH_EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE.format(
                    question="question",
                    answer="answer",
                    solution="solution",
                    Dialogue_History="history",
                    response="answer",
                )
            ):
                return """{"status" : "incomplete","feedback": "feedback"}"""
            if (
                prompt
                == MATH_EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE.format(
                    initial_question="question",
                    answer="answer",
                    solution="solution",
                    Dialogue_History="history",
                    response="answer",
                )
            ):
                return """{"status" : "incomplete","feedback": "feedback"}"""
            if (
                prompt
                == MATH_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.format(
                    question="question",
                    answer="answer",
                    solution="solution",
                    error_type="concept",
                    Dialogue_History="history",
                )
            ):
                return """{"error_type" : "concept", "feedback" : "feedback"}"""
            if (
                prompt
                == MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_1_QUESTION_PROMPT_TEMPLATE.format(
                    initial_question="question",
                    answer="answer",
                    solution="solution",
                    Dialogue_History="history",
                    model_solution="answer",
                )
            ):
                return """{"question" : "question","answer": "answer","type": "missing_step"}"""

        elif "stem-interviewer" in self.model_name:
            return ""
        elif "interviewee" in self.model_name:
            return "answer"

        else:
            return "answer"


class ChatModel:

    def create_model(model_name):
        return Interviewer(model_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="")
    args = parser.parse_args()
    # gpt_model = ChatModel.create_model('gpt-4o')
    # gemini15_model = ChatModel.create_model("gemini-1.5-pro")
    # pi3 = ChatModel.create_model('Phi-3-mini-4k-instruct')
    # llama = ChatModel.create_model("olmoe-test")
    # llama = ChatModel.create_model("olmoe-train")
