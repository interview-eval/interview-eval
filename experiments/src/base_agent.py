import time
from abc import ABC, abstractmethod
from random import randint
from typing import Dict, List, Optional, Tuple

from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from src.prompt import SESSION_SUMMARIZE_PROMPT
from src.utils import extract_json, select_queries


class BaseAgent(ABC):
    """
    An abstract base class for chat agents.

    This class defines the basic structure and interface for chat agents,
    including initialization, reset, send, and receive methods.

    Attributes:
        name (str): The name of the agent.
        system_message (SystemMessage): The system message for the agent.
        model (BaseChatModel): The chat model used by the agent.
        prefix (str): The prefix used for the agent's messages.
    """

    def __init__(
        self,
        name: str,
        system_message: str,
        model: BaseChatModel,
    ) -> None:
        """
        Initialize a new BaseAgent instance.

        Args:
            name (str): The name of the agent.
            system_message (str): The system message for the agent.
            model (BaseChatModel): The chat model to be used by the agent.
        """
        self.name = name
        self.system_message = SystemMessage(system_message) if system_message else ""
        self.model = model
        self.prefix = f"{self.name}: "
        self.cost = []
        self.reset()

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the agent's state.

        This method should be implemented by subclasses to reset any
        stateful attributes of the agent.
        """
        pass

    @abstractmethod
    def send(self) -> str:
        """
        Generate and send a message.

        This method should be implemented by subclasses to generate
        a message using the agent's model and return it.

        Returns:
            str: The generated message.
        """
        pass

    @abstractmethod
    def receive(self, name: str, message: str) -> None:
        """
        Receive and process a message from another agent.

        This method should be implemented by subclasses to handle
        incoming messages from other agents.

        Args:
            name (str): The name of the agent sending the message.
            message (str): The content of the received message.
        """
        pass


# DialogueAgent maintains a full conversation history and generates response based on the entire history
class DialogueAgent(BaseAgent):
    def reset(self) -> None:
        self.session_history: List[str] = []
        
    def omit_adjacent_indices(self):
        # Ensure the indices are in order and valid
    # Omit the two adjacent indices
        idx = len(self.session_history) //2
        self.session_history[idx:idx+2] = ["omitted for brevity."]
        


    def send(self) -> str:
        try:
            if self.system_message:

                message = self.model.invoke(
                    [
                        self.system_message,
                        HumanMessage(content="\n".join(self.session_history + [self.prefix])),
                    ]
                )
            else:
                message = self.model.invoke(
                    [
                        HumanMessage(content="\n".join(self.session_history + [self.prefix])),
                    ]
                )
            try:
                self.cost.append(message.usage_metadata)
                message_content = message.content
            except:
                message_content = message
            
            self.session_history.append(f"{self.name}: {message_content}")
            print(f"\n{self.name}: {message_content}")
            return message_content
        except:
            message_content = ""
            while message_content:
                
                self.omit_adjacent_indices()
                if self.system_message:

                    message = self.model.invoke(
                        [
                            self.system_message,
                            HumanMessage(content="\n".join(self.session_history + [self.prefix])),
                        ]
                    )
                else:
                    message = self.model.invoke(
                        [
                            HumanMessage(content="\n".join(self.session_history + [self.prefix])),
                        ]
                    )            

                
                try:
                    message_content = message.content
                    self.cost.append(message.usage_metadata)
                except:
                    message_content = message
                self.session_history.append(f"{self.name}: {message_content}")
                print(f"\n{self.name}: {message_content}")
                return message_content

    def receive(self, name: str, message: str) -> None:
        self.session_history.append(f"{name}: {message}")
        print(f"\n{name}: {message}")


# EvaluateAgent only keeps track of the last message and generates responses based only on the last received message
class EvaluateAgent(BaseAgent):
    def reset(self) -> None:
        self.last_message: str = ""
    def send(self) -> str:
        if self.last_message == "":
            return ""
        if self.system_message:

            message = self.model.invoke(
                [
                    self.system_message,
                    HumanMessage(content=self.last_message),
                ]
            )
        else:
            message = self.model.invoke(
                [
                    HumanMessage(content=self.last_message),
                ]
            )
        try:
            self.cost.append(message.usage_metadata)
            message_content = message.content
        except:
            message_content = message
        return message_content

    def receive(self, name: str, message: str) -> None:
        self.last_message = message
