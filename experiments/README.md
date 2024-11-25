
# Test Cases and Model Evaluation

## TODO

- [ ] Add test cases with `pytest`
- [ ] Discuss PR conventions with the team
- [ ] Remove unused code in `libs/`
- [ ] Add OpenAI Swarm implementation under `libs/`
- [ ] Simplify the way to manage prompts


## Generating Test Cases
To generate test cases, execute the `test.sh` script, which will output:
- `test_case1.csv`: This file is created when the threshold is set to 3.
- `test_case2.csv`: This file is created when the threshold is set to 1.

## Testing Model & Data

### 1. Load Model
To load the model, use the following code:
```python
from src.models import ChatModel

Interviewer = ChatModel.create('math-interviewer')
Interviewee = ChatModel.create('interviewee')
```

### 2. Load Test Data
To load the test data, use:
```python
from data.data_loader import test_dataloader
seed_questions = test_dataloader()
```
