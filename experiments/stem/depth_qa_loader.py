import json
from collections import defaultdict
from typing import Dict, List, Set

from datasets import load_dataset


class HFDepthQALoader:
    def __init__(self, hf_repo: str = "kaist-ai/DepthQA", split: str = "test"):
        self.hf_repo = hf_repo
        self.split = split
        self.questions: Dict[str, Dict] = {}  # qid -> question dict
        self.nodes: Dict[str, Dict] = {}  # nodeid -> node dict
        self.node_to_q: Dict[str, str] = {}  # nodeid -> qid
        self.q_to_node: Dict[str, Set[str]] = defaultdict(set)  # qid -> set of nodeids

    def load_data(self, except_questions: bool = False, remove_unused_columns: bool = True):
        print(f"Loading data from {self.hf_repo}...")
        if not except_questions:
            # Load questions
            questions_dataset = load_dataset(self.hf_repo, "questions", split=self.split)
            if remove_unused_columns:
                questions_dataset = questions_dataset.remove_columns(["tutoreval_data", "augmented"])
            self.questions = {item["qid"]: item for item in questions_dataset}

        # Load nodes
        nodes_dataset = load_dataset(self.hf_repo, "nodes", split=self.split)
        self.nodes = {item["nodeid"]: item for item in nodes_dataset}

        # Load node_to_q mappings
        node_to_q_dataset = load_dataset(self.hf_repo, "node_to_q", split=self.split)
        for item in node_to_q_dataset:
            self.node_to_q[item["nodeid"]] = item["qid"]
            self.q_to_node[item["qid"]].add(item["nodeid"])  # 1-to-n mapping

        return self.questions, self.nodes, self.node_to_q

    def check_integrity(self) -> None:
        print("Checking graph integrity...")

        errors = []

        def add_error(message):
            errors.append(message)

        # Check questions
        for qid in self.questions.keys():
            # Check q_to_node mapping
            if not self.q_to_node.get(qid):
                add_error(f"Question {qid} not found in q_to_node")

        # Check nodes
        for nodeid in self.nodes.keys():
            node = self.nodes[nodeid]
            depth = node["depth"]

            # Check group consistency
            group_nodeid = nodeid.split("_")[0]
            if node["group"] != group_nodeid:
                add_error(f"Inconsistent group in node {nodeid}")

            # Check direct_predecessors
            for predec_id in node["direct_predecessors"]:
                predec_node = self.nodes[predec_id]
                if not predec_node:
                    add_error(f"Predecessor node {predec_id} of {nodeid} not found")
                else:
                    predec_depth_nodeid = int(predec_id.split("_")[1][1:])
                    predec_depth = predec_node["depth"]
                    if predec_depth_nodeid != predec_depth:
                        add_error(
                            f"Inconsistent depth in predecessor {predec_id}: {predec_depth_nodeid} in nodeid while {predec_depth} in depth field"
                        )
                    if predec_depth != depth - 1:
                        add_error(f"Predecessor {predec_id} of {nodeid} has incorrect depth")
                    if nodeid not in predec_node["direct_successors"]:
                        add_error(f"Node {nodeid} not in direct_successors of its predecessor {predec_id}")

            # Check direct_successors
            for succ_id in node["direct_successors"]:
                succ_node = self.nodes[succ_id]
                if not succ_node:
                    add_error(f"Successor node {succ_id} of {nodeid} not found")
                else:
                    succ_depth_nodeid = int(succ_id.split("_")[1][1:])
                    succ_depth = succ_node["depth"]
                    if succ_depth_nodeid != succ_depth:
                        add_error(
                            f"Inconsistent depth in successor {succ_id}: {succ_depth_nodeid} in nodeid while {succ_depth} in depth field"
                        )
                    if succ_depth != depth + 1:
                        add_error(f"Successor {succ_id} of {nodeid} has incorrect depth")
                    if nodeid not in succ_node["direct_predecessors"]:
                        add_error(f"Node {nodeid} not in direct_predecessors of its successor {succ_id}")

            # Check node_to_q mapping
            if not self.node_to_q.get(nodeid):
                add_error(f"Node {nodeid} not found in node_to_q")

        # Check consistency between node_to_q, nodes, and questions
        for nodeid in self.node_to_q.keys():
            qid = self.node_to_q.get(nodeid)
            if not self.questions.get(qid):
                add_error(f"qid {qid} in node_to_q not found in questions")
            if not self.nodes.get(nodeid):
                add_error(f"nodeid {nodeid} in node_to_q not found in nodes")
            if nodeid not in self.q_to_node.get(qid):
                add_error(
                    f"Inconsistency: node_to_q[{nodeid}] = {qid}, but q_to_node[{qid}] = {self.q_to_node.get(qid)}"
                )

        if errors:
            raise ValueError("Graph integrity check failed:\n" + "\n".join(errors))
        else:
            print("Graph integrity check passed successfully.")

    def load_samples(self) -> List[Dict]:

        physics_ids = [2, 8, 10]

        samples = []
        for i in physics_ids:
            one_sample = defaultdict(list)

            for j in range(3):
                if j == 2:
                    nodeid = f"{i}_d{j+1}"
                else:
                    nodeid = f"{i}_d{j+1}_n1"
                qid = self.node_to_q[nodeid]
                question = self.questions[qid]["question"]
                one_sample[i + 1].append(
                    {
                        "nodeid": nodeid,
                        "qid": qid,
                        "question": question,
                        "level": j + 1,
                        "solution": self.questions[qid]["answer"],
                        "domain": self.questions[qid]["domain"],
                    }
                )
            samples.append(one_sample)

        return samples


if __name__ == "__main__":
    loader = HFDepthQALoader()
    loader.load_data()
    loader.check_integrity()

    samples = loader.load_samples()
    # Export the samples as jsonl
    samples_jsonl = "stem/depthqa_samples.jsonl"
    with open(samples_jsonl, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")
