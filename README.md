# interview-swarm

An automated interview evaluation system that simulates technical interviews using AI agents. The system consists of an AI interviewer and interviewee, conducting structured conversations based on predefined rubrics and strategies.

## 📦 Installation

```bash
pip install interview-eval
```

## 🌟 Features

- AI-powered interviewer and interviewee agents
- Configurable interview parameters and evaluation rubrics
- Real-time conversation display with rich formatting
- Detailed scoring and feedback system
- Progress tracking and maximum question limits
- Customizable OpenAI client configuration

## 🚀 Quick Start

```python
from interview_eval import InterviewRunner, Interviewer, Interviewee
from rich.console import Console
import logging
import yaml

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Setup logging and console
logger = logging.getLogger("interview_eval")
console = Console()

# Initialize agents
interviewer = Interviewer(config)
interviewee = Interviewee(config)

# Create and run interview
runner = InterviewRunner(interviewer, interviewee, config, logger, console)
results = runner.run()
```

## ⚙️ Configuration

Create a YAML configuration file with the following structure:

```yaml
interviewer:
  name: "Technical Interviewer"
  instructions: "Your interview guidelines..."
  rubric: "Evaluation criteria..."
  strategy:
    key_areas: [...]
    scoring_criteria: [...]
  client:  # Optional OpenAI client configuration
    api_key: "your-api-key"

interviewee:
  name: "Candidate"
  instructions: "Interviewee behavior guidelines..."

session:
  initial_message: "Welcome to the interview..."
  max_questions: 10
  max_retries: 2
  initial_context: {}
```

## 📊 Results

The interview runner returns a dictionary containing:
- Final score (0-10)
- Detailed feedback and comments
- Number of questions asked


### Requirements & TODOs

- Modifying problem ✔️
  - Python function to modify the problem `modify_problem`
  - Supported strategies: `Unclarifying`, `Paraphrasing`, and `Modifying` (given seed question, create a new question)

- Feedback & Editing Loop
  - Proceed to next question if the response is graded as `Good`
  - 이전에 했던 feedback 주지 말기

- Followup Questions
  - Problem, Response, Feedback, Followup Question, Response, Feedback, Followup Question, ...

- Report Card
  - Per seed questions pool
  - Include information about the student's performance on each question that received different scores


- [ ] More strict loading of config.yaml (e.g. check if all required fields are present)
- [ ] Add documentation for the code
- [ ] Support interview_type: "base", "adaptive"
- [ ] Fix the organization for cli support
- [ ] Add tests
- [ ] Hide logging inside the Runner
- [ ] Add support for seed questions
- [ ] Release to PyPI