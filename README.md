# interview-swarm
Interview Process implemented in Swarm. Will be integrated with interview-eval in the future.


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