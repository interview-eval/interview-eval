# interview-swarm

Interview Process implemented in Swarm. Will be integrated with interview-eval in the future.

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

### Managing submodules

```bash
# Add a submodule to your repository
git submodule add <repository-url> [path]

# Initialize submodules after cloning a project with submodules
git submodule init

# Update submodules to their latest commits
git submodule update

# Clone a repository and its submodules at the same time
git clone --recurse-submodules <repository-url>

# Pull changes including submodules
git pull --recurse-submodules

# Update all submodules to latest commits
git submodule update --remote --merge

# Remove a submodule
git submodule deinit <path>
git rm <path>
rm -rf .git/modules/<path>
```

Common workflow when working with submodules:
1. Add submodule: `git submodule add <url>`
2. Commit the change: `git commit -m "Added submodule"`
3. Push changes: `git push`