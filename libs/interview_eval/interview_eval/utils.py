import logging
import os
import re
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Custom theme for rich
custom_theme = Theme(
    {
        "interviewer": "green",
        "interviewee": "blue",
        "feedback agent": "magenta",
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
    }
)

console = Console(theme=custom_theme)


def setup_logging(config: dict, verbose: bool) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("interview")
    logger.setLevel(logging.INFO)

    # Create formatter for file logging only
    formatter = logging.Formatter("%(asctime)s - %(message)s")

    # Setup file handler if enabled
    try:
        if config["logging"]["save_to_file"]:
            output_dir = Path(config["logging"]["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = config["logging"]["filename_template"].format(
                timestamp=timestamp)
            file_handler = logging.FileHandler(output_dir / filename)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            log_file_path = file_handler.baseFilename
            logger.addHandler(file_handler)
    except KeyError:
        return None, None

    return logger, log_file_path


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file with environment variable support."""
    load_dotenv()

    with open(config_path, "r") as file:
        content = file.read()
        # Replace ${VAR} with environment variables
        env_vars = re.findall(r"\${([^}]+)}", content)
        for var in env_vars:
            env_value = os.getenv(var)
            if env_value:
                content = content.replace(f"${{{var}}}", env_value)
            else:
                raise ValueError(f"Environment variable {var} not set")

    return yaml.safe_load(content)


def get_json_prompt(key_description_dict: dict):
    """Get JSON prompt from key-description dictionary."""
    instruction = "Please output the information in the following json format:\n\n"
    prompt = []

    for key, description in key_description_dict.items():
        prompt.append(f'  "{key}": "{description}",\n')

    return instruction + "{\n" + "".join(prompt) + "}\n"


if __name__ == "__main__":
    # Test the functions
    json_prompt = get_json_prompt({"name": "Your name", "age": "Your age"})
    print(json_prompt)
