import argparse
import os

import pandas as pd
from dotenv import load_dotenv
from dotmap import DotMap
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
    MATH_EVALUATOR_STATE_UNC_0_PROMPT_TEMPLATE,
    MATH_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE,
    MATH_GRADER_PROMPT_TEMPLATE,
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

load_dotenv("./.env")
os.environ["HF_HOME"] = os.getenv("HF_HOME")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
agents_model = {
    "azure": "azure_model_id",
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gpt-4o": "gpt-4o-2024-05-13",
    "gpt-3.5-turbo": "gpt-35-turbo-0125-v1",
    "phi-3-mini-4k-instruct": "microsoft/Phi-3-mini-4k-instruct",
    "llama-3.1-70b": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "llama-2-7b-chat-hf": "meta-llama/Llama-2-7b-chat-hf",
    "llama-3-8b-chat": "meta-llama/Meta-Llama-3-8B",
    "mixtral-8x7B-Instruct-v0.1": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistral-7B-Instruct-v0.1": "mistralai/Mistral-7B-Instruct-v0.1",
    "deepseek-math-7b-instruct": "deepseek-ai/deepseek-math-7b-instruct",
    "deepseek-coder-7b-instruct-v1.5": "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
    # olmoe-math
    "olmoe-math-1": "Muennighoff/mathtrain",
    "olmoe-math-2": "Muennighoff/mathtesthalf1",
    "olmoe-math-3": "Muennighoff/mathtest",
    "olmoe-math-4": "Muennighoff/mathtraingsm8k",
    "olmoe-math-5": "Muennighoff/mathtraintestrerun",
    "olmoe-math-6": "Muennighoff/mathgsm8k",
    "olmoe-math-7": "Muennighoff/mathtestinstruct",
    "olmoe-math-8": "Muennighoff/gsm8k",
    # olmoe-stem
    "olmoe-stem-1": "Muennighoff/stemtrain",
    "olmoe-stem-2": "Muennighoff/stemtesthalf1rerun",
    "olmoe-stem-3": "Muennighoff/stemtest",
    "olmoe-stem-5": "Muennighoff/stemtraintest",
    "olmoe-stem-7": "Muennighoff/stemtestinstruct",
    # zephyr-math
    "zephyr-math-1": "scottsuk0306/zephyr-7b-math-train",
    "zephyr-math-2": "scottsuk0306/zephyr-7b-math-test-half",
    "zephyr-math-3": "scottsuk0306/zephyr-7b-math-test",
    "zephyr-math-4": "scottsuk0306/zephyr-7b-math-case-4",
    "zephyr-math-5": "scottsuk0306/zephyr-7b-math-train-test",
    "zephyr-math-6": "scottsuk0306/zephyr-7b-math-case-6",
    "zephyr-math-7": "scottsuk0306/zephyr-7b-math-case-7",
    "zephyr-math-8": "scottsuk0306/zephyr-7b-math-case-8-fixed",
    # zephyr-stem
    "zephyr-stem-1": "scottsuk0306/zephyr-7b-stem-case-1",
    "zephyr-stem-2": "scottsuk0306/zephyr-7b-stem-case-2",
    "zephyr-stem-3": "scottsuk0306/zephyr-7b-stem-case-3",
    "zephyr-stem-5": "scottsuk0306/zephyr-7b-stem-case-5",
    "zephyr-stem-7": "scottsuk0306/zephyr-7b-stem-case-7",
    "stem-interviewer": "stem-interviewer",
    "math-interviewer": "math-interviewer",
    "interviewee": "interviewee",
    # add other models as needed
}

api_version = {
    "gpt-4o": "2024-02-01",
    "gpt-3.5-turbo": "2024-02-01",
}


class Interviewer:
    def __init__(self, model_name):
        self.model_name = model_name
        self.cnt = 0

    def invoke(self, prompt):
        try:
            prompt = prompt[0].content
        except:
            pass
        if "math-interviewer" in self.model_name:
            if (
                prompt.split("{")[0]
                == MATH_MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE.split("{")[0]
            ):
                return "question"
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE.split("{")[0]
            ):  # .format(initial_question="init_query",revised_question="question",feedback='feedback',deleted_information='deleted_information',solution = 'solution',answer = 'answer',Dialogue_History='history',explanation = 'explanation'):
                return """{
    "deleted_information": "deleted_information",
    "explanation": "explanation",
    "revised_question": "revised_question"
    "feedback": "feedback",   
    "status": "complete"
}"""

            if "Summarize the conversation" in prompt:
                output = DotMap()
                output.content = "summary"
                return output
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE.split("{")[0]
            ):  # .format(
                #     question="question",
                #     solution='solution',
                #     answer ='None',
                #     evaluation = '''{ "explanation": "explanation","answer correctness": "False", "solving process correctness": "False", "error type":'concept'}''',
                #     model_history='User: Question: question',
                #     model_output='System: answer',
                # ):
                return """{
    "status": "incomplete",
    "feedback": "feeback"
}"""
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_EXP_1_PROMPT_TEMPLATE.split("{")[0]
            ):  # .format(question="question",solution='solution',answer ='None',evaluation =  '''{ "explanation": "explanation","answer correctness": "False", "solving process correctness": "False", "error type":'concept'}''',model_history='User: feeback\nUser: Question: question',model_output='System: answer'):

                return """{"feedback": "feedback","feedback_type": "feedback_type"}"""

            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_0_QUESTION_PROMPT_TEMPLATE.split(
                    "{"
                )[
                    0
                ]
            ):  # .format(
                #     initial_question="question",
                #     solution='solution',
                #     seed_answer = 'answer',
                #     Dialogue_History='history',
                #     answer = 'answer',
                #     question = 'question',
                #     model_output = 'answer',
                #     model_solution = 'solution'
                # ):
                return """{"status" : "incomplete","feedback": "feedback"}"""
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE.split(
                    "{"
                )[0]
            ):  # .format(question='User: feedback',answer= 'None',solution = 'solution', Dialogue_History='User: Question: question\nSystem: answer\nUser: feeback\nUser: feedback',response = 'System: answer'):
                return """{"status" : "incomplete","feedback": "feedback"}"""
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE.split(
                    "{"
                )[0]
            ):  # .format(initial_question='question',answer = 'None',solution='solution',Dialogue_History='User: You got a correct answer! Good Job.',response = '[\'System: answer\']') :
                return """{"status" : "incomplete","feedback": "feedback"}"""
            if (
                MATH_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE.split(
                    "{"
                )[0]
                in prompt.split("{")[0]
            ):  # .format(question='question',answer = 'None',solution='solution',error_type = 'concept',Dialogue_History='User: Question: question\nUser: feeback'):
                return """{"error_type" : "concept", "feedback" : "feedback"}"""
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_1_QUESTION_PROMPT_TEMPLATE.split(
                    "{"
                )[
                    0
                ]
            ):  # .format(initial_question='question',answer = 'None',solution='solution',model_solution='User: You got a correct answer! Good Job.', Dialogue_History= '[\'System: answer\']'):
                return """{"question" : "question","answer": "answer","type": "missing_step"}"""
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_0_QUESTION_PROMPT_TEMPLATE.split(
                    "{"
                )[
                    0
                ]
            ):  # .format(initial_question='question',question = 'User: question',model_solution='User: You got a correct answer! Good Job.',seed_answer = 'None',answer = 'answer: answer',solution='solution',model_output='System: answer', Dialogue_History= '[\'System: answer\']'):
                return """{"question" : "question","answer": "answer","type": "missing_step"}"""
            if (
                prompt.split("{")[0] == MATH_GRADER_PROMPT_TEMPLATE.split("{")[0]
            ):  # .format(question = "question",answer = 'None',solution = 'solution',history = 'System: answer'):
                if self.cnt == 2:
                    output = DotMap()
                    output.content = """{ "explanation": explanation","answer correctness": "True, "solving process correctness": "True" "error type":'concept'}"""
                    output.usage_metadata = "None"
                    return output
                else:
                    self.cnt += 1
                    output = DotMap()
                    output.content = """{ "explanation": "explanation","answer correctness": "False", "solving process correctness": "False", "error type":'concept'}"""
                    output.usage_metadata = "None"
                    return output
            if (
                prompt.split("{")[0]
                == MATH_EVALUATOR_STATE_UNC_0_PROMPT_TEMPLATE.split("{")[0]
            ):  # .format(initial_question='question',
                # revised_question='question',
                # deleted_information='question',
                # solution = 'solution',
                # answer = 'answer',
                # Dialogue_History='history',
                # explanation = 'explanation'):
                return """{'category':'category', 'explanation':'explanation'}"""
        elif "stem-interviewer" in self.model_name:
            return ""
        elif "interviewee" in self.model_name:

            return "answer"

        else:
            return "answer"


class ChatModel:

    def create_model(name):
        model_name = name.lower()
        assert model_name in agents_model.keys(), f"{model_name} is not supported"

        if "interview" in model_name:
            model = Interviewer(model_name)
        elif "gpt" in model_name:
            model = AzureChatOpenAI(
                azure_deployment=agents_model[model_name],
                api_version=api_version[model_name],
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                temperature=1,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # other params...
            )
        elif "gemini" in model_name:
            if "1.5" in model_name:
                api_key = os.getenv("GEMINI15_API_KEY")
            else:
                api_key = os.getenv("GEMINI_API_KEY")

            model = ChatGoogleGenerativeAI(
                api_key=os.getenv("GEMINI_API_KEY"),
                model=agents_model[model_name],
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # other params...
            )
        elif "openai" in model_name:
            model = ChatOpenAI(
                model=agents_model[model_name],
                temperature=0.2,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # other params...
            )
        elif "llama-3.1-70b" in model_name:
            model = ChatTogether(
                together_api_key=os.getenv("TOGETHER_API_KEY"),
                model=agents_model[model_name],
            )
        else:
            llm = HuggingFacePipeline.from_model_id(
                model_id=agents_model[model_name],
                task="text-generation",
                device=0,
                pipeline_kwargs=dict(
                    temperature=0.2,
                    max_new_tokens=512,
                    do_sample=True,
                    repetition_penalty=1.03,
                    return_full_text=False,
                ),
            )
            model = ChatHuggingFace(llm=llm)

        return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="")
    args = parser.parse_args()
    # gpt_model = ChatModel.create_model('gpt-4o')
    # gemini15_model = ChatModel.create_model("gemini-1.5-pro")
    # pi3 = ChatModel.create_model('Phi-3-mini-4k-instruct')
    # llama = ChatModel.create_model("olmoe-test")
    # llama = ChatModel.create_model("olmoe-train")
    llama = ChatModel.create_model(args.model)
    import pdb

    pdb.set_trace()
    # huggingface_model = create_model('huggingface')
