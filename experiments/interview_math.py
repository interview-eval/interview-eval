import argparse
import getpass
import os
from typing import Dict, List

import pandas as pd
from datasets import load_dataset
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from math_reasoning.temp_data import MATH_GEO_LEVEL_2, MATH_GEO_LEVEL_3, MATH_GEO_LEVEL_4, MATH_GEO_LEVEL_5
from src.base_agent import DialogueAgent, EvaluateAgent
from src.base_state import InterviewState, InterviewType
from src.dialogue import DialogueSimulator, Moderator, select_next_speaker
from src.models import ChatModel
from src.prompt import AGENT_DESCRIPTOR_SYSTEM_MESSAGE, AGENT_SPECIFIER_PROMPT_TEMPLATE, SYSTEM_MESSAGE_TEMPLATE
from src.utils import extract_boxed_str, load_jsonl_file

load_dotenv()
os.environ["HF_HOME"] = os.getenv("HF_HOME")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_evaluator", type=str, default="gpt-4-1106-preview")
    parser.add_argument("--model_moderator", type=str, default="gpt-4")
    parser.add_argument("--model_evaluatee", type=str, default="gpt-3.5-turbo")
    parser.add_argument("--names", type=int, default=0)
    parser.add_argument("--state_threshold", type=int, default=3)
    parser.add_argument(
        "--start_query_index", type=int, default=0
    )  # , choices=["start", "middle", "end"], default="middle")
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--init_action", type=str, default="None")
    parser.add_argument("--task", type=str, default="math")
    return parser.parse_args()


def generate_agent_description(name: str, conversation_description: str, word_limit: int) -> str:

    role_description = (
        "an Evaluator that assess the System's ability"
        if name in ["Evaluator", "User"]
        else "an AI assistant solving a problem"
    )
    agent_specifier_prompt = [
        SystemMessage(content=AGENT_DESCRIPTOR_SYSTEM_MESSAGE),
        HumanMessage(
            content=AGENT_SPECIFIER_PROMPT_TEMPLATE.format(
                conversation_description=conversation_description,
                name=name,
                role_description=role_description,
                word_limit=word_limit,
            )
        ),
    ]
    return ChatOpenAI(temperature=1.0, model="gpt-4o-2024-05-13").invoke(agent_specifier_prompt).content


def generate_system_message(name: str, description: str, conversation_description: str) -> str:
    return SYSTEM_MESSAGE_TEMPLATE.format(
        conversation_description=conversation_description,
        name=name,
        description=description,
    )


def seed_question(N):

    # Load the entire dataset
    dataset = load_dataset("EunsuKim/MATH")
    data_1 = dataset["test_half1"]
    data_2 = dataset["test_half2"]
    df_1 = pd.DataFrame(data_1)
    # make the column of "domain" and add the value of "test_half1"
    df_1["domain"] = ["test_half1" for i in range(len(df_1))]
    df_2 = pd.DataFrame(data_2)
    df_2["domain"] = ["test_half2" for i in range(len(df_2))]
    n_samples_per_level = N
    uniform_samples_1 = (
        df_1.groupby("level")
        .apply(lambda x: x.sample(n=min(len(x), n_samples_per_level), random_state=42))
        .reset_index(drop=True)
    )
    uniform_samples_2 = (
        df_2.groupby("level")
        .apply(lambda x: x.sample(n=min(len(x), n_samples_per_level), random_state=42))
        .reset_index(drop=True)
    )

    uniform_samples = pd.concat([uniform_samples_1, uniform_samples_2], axis=0)
    return uniform_samples


def create_agents(
    names: List[str], agent_system_messages: Dict[str, str], agents_model: Dict[str, str]
) -> Dict[str, DialogueAgent]:
    agents = {}
    for name in names:
        agent_class = EvaluateAgent if name.lower() in ["evaluator", "user"] else DialogueAgent

        model = ChatModel.create_model(agents_model[name.lower()])
        agents[name] = agent_class(
            name=name,
            system_message="",
            model=model,
        )
    return agents


def main():
    args = parse_arguments()
    load_dotenv()

    # Interview Settings
    topic = "Math problem solving"
    # seed_questions = load_jsonl_file("./data/math_samples.jsonl")
    seed_questions = seed_question(10)  # ,seed_question(10)[50:70]])

    if args.task == "math":
        seed_questions = seed_questions.apply(lambda x: extract_boxed_str(x), axis=1)
        seed_questions = seed_questions.reset_index(drop=True)
    if os.path.exists(args.output_path):
        df = pd.read_csv(args.output_path)
        start_query_index = df["idx"].iloc[-1]
    else:
        start_query_index = args.start_query_index
    word_limit = 50
    names_list = [["System", "User"], ["Evaluatee", "Evaluator"]]
    names = names_list[args.names]
    conversation_description = f"Here is the scenario: {topic}\nThe participants are: {', '.join(names)}"
    # Moderator Setting
    moderator = Moderator(
        model=ChatOpenAI(model=args.model_moderator, temperature=0.2).bind(response_format={"type": "json_object"}),
        summarizer=ChatOpenAI(model=args.model_moderator, temperature=0.2),
        system_message=SystemMessage(content=""),
        queries=seed_questions,
        references=None,
        store_session=True,
        agents_name=names,
        start_query_index=start_query_index,
        state_threshold=args.state_threshold,
        init_action=args.init_action,
    )
    # Agents Setting
    # agent_descriptions = {
    #     name: generate_agent_description(name, conversation_description, word_limit) for name in names
    # }
    # agent_system_messages = {
    #     name: generate_system_message(name, description, conversation_description)
    #     for name, description in agent_descriptions.items()
    # }
    agents_model = {
        "evaluator": args.model_evaluator,
        "user": args.model_evaluator,
        "evaluatee": args.model_evaluatee,
        "system": args.model_evaluatee,
    }
    agents = create_agents(names, [], agents_model)

    # Simulation
    simulator = DialogueSimulator(
        agents=agents,
        moderator=moderator,
        selection_function=select_next_speaker,
        task_type=InterviewType.MATH,
        output_path=args.output_path,
    )
    simulator.reset()

    while simulator.moderator.state != InterviewState.EVALUATION_COMPLETE:
        simulator.step()

    # simulator.moderator.save_attributes_to_file(file_path=args.output_path)


if __name__ == "__main__":
    main()
