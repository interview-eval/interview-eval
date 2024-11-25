AGENT_DESCRIPTOR_SYSTEM_MESSAGE = "You can add detail to the description of the conversation participant."

AGENT_SPECIFIER_PROMPT_TEMPLATE = """{conversation_description}
Please reply with a creative description of {name}, in {word_limit} words or less. 
Speak directly to {name}.
Give them a point of view.
Do not add anything else. The initial role description is "{role_description}" """

SYSTEM_MESSAGE_TEMPLATE = """{conversation_description}

Your name is {name}.

Your description is as follows: {description}

Your goal is to persuade your conversation partner of your point of view.

Do not add anything else.

Stop speaking the moment you finish speaking from your perspective.
"""

TOPIC_SPECIFIER_SYSTEM_MESSAGE = "You can make a topic more specific."

TOPIC_SPECIFIER_PROMPT_TEMPLATE = """{topic}

You are the moderator.
Please make the topic more specific.
Please reply with the specified quest in {word_limit} words or less. 
Speak directly to the participants: {names}.
Do not add anything else."""

SESSION_SUMMARIZE_PROMPT = """The following is a conversation between {user_name} and {system_name}. Summarize the conversation. 
Instead of focusing on the specific details of the questions and answers, provide a summary that highlights the overall flow of the conversation and {system_name}'s problem-solving abilities.
Session_history : {session_history}
Summary :"""
