import json

from src import BASE_DIR


class MTBench101DataLoader:
    def __init__(self):
        self.file_path = BASE_DIR / "data" / "mtbench101.jsonl"
        self.data = []

    def load_data(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            for line in file:
                self.data.append(json.loads(line.strip()))

    def get_data(self):
        return self.data

    def get_task(self, index):
        return self.data[index]["task"]

    def get_id(self, index):
        return self.data[index]["id"]

    def get_history(self, index):
        return self.data[index]["history"]

    def get_conversation(self, index):
        history = self.get_history(index)
        conversation = []
        for entry in history:
            conversation.append(("user", entry["user"]))
            conversation.append(("bot", entry["bot"]))
        return conversation

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]


if __name__ == "__main__":

    loader = MTBench101DataLoader()
    loader.load_data()

    print(f"Number of entries: {len(loader)}")
    print(f"First entry: {loader[0]}")
    print(f"Task of second entry: {loader.get_task(1)}")
    print(f"ID of third entry: {loader.get_id(2)}")
    print(f"Conversation of first entry:")
    for speaker, text in loader.get_conversation(0):
        print(f"{speaker}: {text}")
