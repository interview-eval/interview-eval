from typing import List

from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.dialogue import DialogueAgent, DialogueSimulator, select_next_speaker
from src.prompt import (
    AGENT_DESCRIPTOR_SYSTEM_MESSAGE,
    AGENT_SPECIFIER_PROMPT_TEMPLATE,
    SYSTEM_MESSAGE_TEMPLATE,
    TOPIC_SPECIFIER_PROMPT_TEMPLATE,
    TOPIC_SPECIFIER_SYSTEM_MESSAGE,
)


def generate_agent_description(name, conversation_description, word_limit):
    agent_descriptor_system_message = SystemMessage(content=AGENT_DESCRIPTOR_SYSTEM_MESSAGE)
    agent_specifier_prompt = [
        agent_descriptor_system_message,
        HumanMessage(
            content=AGENT_SPECIFIER_PROMPT_TEMPLATE.format(
                conversation_description=conversation_description,
                name=name,
                word_limit=word_limit,
            )
        ),
    ]
    agent_description = ChatOpenAI(temperature=1.0).invoke(agent_specifier_prompt).content
    return agent_description


def generate_system_message(name, description, conversation_description):
    return SYSTEM_MESSAGE_TEMPLATE.format(
        conversation_description=conversation_description,
        name=name,
        description=description,
    )


if __name__ == "__main__":
    load_dotenv()

    names = ["AI accelerationist", "AI alarmist"]
    topic = "The current impact of automation and artificial intelligence on employment"
    word_limit = 50

    conversation_description = f"""Here is the topic of conversation: {topic}
The participants are: {', '.join(names)}"""

    agent_descriptions = {
        name: generate_agent_description(name, conversation_description, word_limit) for name in names
    }

    agent_system_messages = {
        name: generate_system_message(name, description, conversation_description)
        for name, description in agent_descriptions.items()
    }

    agents = [
        DialogueAgent(
            name=name,
            system_message=SystemMessage(content=system_message),
            model=ChatOpenAI(model="gpt-4", temperature=0.2),
        )
        for name, system_message in agent_system_messages.items()
    ]

    topic_specifier_prompt = [
        SystemMessage(content=TOPIC_SPECIFIER_SYSTEM_MESSAGE),
        HumanMessage(
            content=TOPIC_SPECIFIER_PROMPT_TEMPLATE.format(topic=topic, word_limit=word_limit, names=", ".join(names))
        ),
    ]
    specified_topic = ChatOpenAI(temperature=1.0).invoke(topic_specifier_prompt).content

    max_iters = 6
    simulator = DialogueSimulator(agents=agents, selection_function=select_next_speaker)
    simulator.reset()
    simulator.inject("Moderator", specified_topic)
    print(f"(Moderator): {specified_topic}\n")

    for _ in range(max_iters):
        name, message = simulator.step()
        print(f"({name}): {message}\n")
