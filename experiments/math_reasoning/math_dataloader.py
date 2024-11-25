import json
from collections import defaultdict
from typing import Dict, List, Set

from datasets import load_dataset
import pandas as pd

class HFMATHLoader:
    def __init__(self, hf_repo: str = "lighteval/MATH", split: str = "test", category : str = "algebra"):
        self.hf_repo = hf_repo
        self.split = split
        self.category = category
        
        

    def load_data(self, except_questions: bool = False, remove_unused_columns: bool = True):
        print(f"Loading data from {self.hf_repo}...")
        self.ds = pd.DataFrame(load_dataset(self.hf_repo,self.category)[self.split])
        self.ds = self.ds.rename(columns={"problem": "initial_question"})
        return self.ds


    def load_samples(self, N):
        # Ensure the 'level' column has no leading/trailing whitespace
        self.ds['level'] = self.ds['level'].str.strip()

        # Group by 'level' column
        grouped = self.ds.groupby('level')

        # Calculate how many samples to take from each group
        samples_per_group = N // len(grouped)

        # Initialize a list to hold selected samples
        selected_samples = []

        # First, select as many samples as possible from each group
        for name, group in grouped:
            selected = group.sample(min(len(group), samples_per_group), random_state=1)
            selected_samples.append(selected)

        # Concatenate all selected samples
        selected_samples = pd.concat(selected_samples)

        # Calculate how many more samples are needed to reach N
        remaining_samples_needed = N - len(selected_samples)

        if remaining_samples_needed > 0:
            # Get the remaining samples (ensure there are enough samples left)
            remaining_pool = self.ds[~self.ds.index.isin(selected_samples.index)]

            # If the remaining pool is smaller than needed, adjust the sample size
            remaining_samples_needed = min(remaining_samples_needed, len(remaining_pool))

            if remaining_samples_needed > 0:
                # Randomly or deterministically select the remaining samples
                remaining_samples = remaining_pool.sample(remaining_samples_needed, random_state=1)
                # Append the remaining samples
                selected_samples = pd.concat([selected_samples, remaining_samples])

        # Sort the selected samples by 'level'
        selected_samples = selected_samples.sort_values(by='level')

        return selected_samples




if __name__ == "__main__":
    loader_test_algebra = HFMATHLoader(split= "test", category = "algebra")
    loader_test_intermediate_algebra = HFMATHLoader(split= "test", category = "intermediate_algebra")
    loader_test_prealgebra = HFMATHLoader(split= "test", category = "prealgebra")

    loader_train_algebra = HFMATHLoader(split ="train", category = "algebra")
    loader_train_intermediate_algebra = HFMATHLoader(split ="train", category = "intermediate_algebra")
    loader_train_prealgebra = HFMATHLoader(split= "train", category = "prealgebra")

    loader_test_algebra.load_data()
    loader_test_intermediate_algebra.load_data()
    loader_test_prealgebra.load_data()
    loader_train_algebra.load_data()
    loader_train_intermediate_algebra.load_data()
    loader_train_prealgebra.load_data()


    samples_1 = pd.DataFrame(loader_test_algebra.load_samples(1000))
    samples_2 = pd.DataFrame(loader_test_intermediate_algebra.load_samples(900))
    samples_2_1 = pd.DataFrame(loader_test_prealgebra.load_samples(100))
    
    samples_3 = pd.DataFrame(loader_train_algebra.load_samples(1000))
    samples_4 = pd.DataFrame(loader_train_intermediate_algebra.load_samples(900))
    samples_4_1 = pd.DataFrame(loader_train_prealgebra.load_samples(100))


    samples_1 = samples_1.to_dict(orient='records')
    samples_2 = samples_2.to_dict(orient='records')
    samples_2_1 = samples_2_1.to_dict(orient='records')

    samples_3 = samples_3.to_dict(orient='records')
    samples_4 = samples_4.to_dict(orient='records')
    samples_4_1 = samples_4_1.to_dict(orient='records')

    # Export the samples as jsonl
    samples_jsonl = "data/math_algebra_test.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_1))
    samples_jsonl = "data/math_algebra_inter_test.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_2))
    samples_jsonl = "data/math_algebra_pre_test.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_2_1))
    
    samples_jsonl = "data/math_algebra_train.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_3))

    samples_jsonl = "data/math_algebra_inter_train.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_4))
    
    samples_jsonl = "data/math_algebra_pre_train.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_4_1))

    
