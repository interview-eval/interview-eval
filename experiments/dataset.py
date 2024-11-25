
import csv
import json
import random
import numpy as np
import pandas as pd

from collections import defaultdict
def stat_unique(data: pd.DataFrame, key):
    if key is None:
        print('Total length: {}'.format(len(data)))
    elif isinstance(key, str):
        print('Number of unique {}: {}'.format(key, len(data[key].unique())))
        return len(data[key].unique())
    elif isinstance(key, list):
        print('Number of unique [{}]: {}'.format(','.join(key), len(data.drop_duplicates(key, keep='first'))))
        return len(data.drop_duplicates(key, keep='first'))
raw_data = pd.read_csv('../../data/assistment/assistment2009.csv', encoding = 'utf-8', dtype={'skill_id': str})
raw_data.head()

raw_data = raw_data.rename(columns={'user_id': 'student_id',
                                    'problem_id': 'question_id',
                                    'skill_id': 'knowledge_id',
                                    'skill_name': 'knowledge_name',
                                    })
all_data = raw_data.loc[:, ['student_id', 'question_id', 'knowledge_id', 'knowledge_name', 'correct']].dropna()
stat_unique(all_data, None)
a=stat_unique(all_data, ['student_id', 'question_id'])
b=stat_unique(all_data, 'student_id')
c=stat_unique(all_data, 'question_id')
d=stat_unique(all_data, 'knowledge_id')

selected_data = all_data
# filter questions
n_students = selected_data.groupby('question_id')['student_id'].count()
question_filter = n_students[n_students < 50].index.tolist()
print(f'filter {len(question_filter)} questions')
selected_data = selected_data[~selected_data['question_id'].isin(question_filter)]

# filter students
n_questions = selected_data.groupby('student_id')['question_id'].count()
student_filter = n_questions[n_questions < 20].index.tolist()
print(f'filter {len(student_filter)} students')
selected_data = selected_data[~selected_data['student_id'].isin(student_filter)]

# get question to knowledge map
q2k = {}
table = selected_data.loc[:, ['question_id', 'knowledge_id']].drop_duplicates()
for i, row in table.iterrows():
    q = row['question_id']
    q2k[q] = set(map(int, str(int(float(row['knowledge_id']))).split('_')))
    
# get knowledge to question map
k2q = {}
for q, ks in q2k.items():
    for k in ks:
        k2q.setdefault(k, set())
        k2q[k].add(q)
# filter knowledges
#selected_knowledges = { k for k, q in k2q.items()}
selected_knowledges = { k for k, q in k2q.items() if len(q) >= 10}
print(f'filter {len(k2q) - len(selected_knowledges)} knowledges')

# update maps
q2k = {q : ks for q, ks in q2k.items() if ks & selected_knowledges}
k2q = {}
for q, ks in q2k.items():
    for k in ks:
        k2q.setdefault(k, set())
        k2q[k].add(q)
# update data
selected_data = selected_data[selected_data.apply(lambda x: x['question_id'] in q2k, axis=1)]
# renumber the students
s2n = {}
cnt = 0
for i, row in selected_data.iterrows():
    if row.student_id not in s2n:
        s2n[row.student_id] = cnt
        cnt += 1
selected_data.loc[:, 'student_id'] = selected_data.loc[:, 'student_id'].apply(lambda x: s2n[x])
# renumber the questions
q2n = {}
cnt = 0
for i, row in selected_data.iterrows():
    if row.question_id not in q2n:
        q2n[row.question_id] = cnt
        cnt += 1
selected_data.loc[:, 'question_id'] = selected_data.loc[:, 'question_id'].apply(lambda x: q2n[x])
# renumber the knowledges
k2n = {}
cnt = 0
for i, row in selected_data.iterrows():
    for k in str(row.knowledge_id).split('_'):
        if int(float(k)) not in k2n:
            k2n[int(float(k))] = cnt
            cnt += 1
selected_data.loc[:, 'knowledge_id'] = selected_data.loc[:, 'knowledge_id'].apply(lambda x: '_'.join(map(lambda y: str(k2n[int(float(y))]), str(x).split('_'))))
stat_unique(selected_data, None)
a=stat_unique(selected_data, ['student_id', 'question_id'])
b=stat_unique(selected_data, 'student_id')
c=stat_unique(selected_data, 'question_id')
d=stat_unique(selected_data, 'knowledge_id')
print('Average #questions per knowledge: {}'.format((len(q2k) / len(k2q))))

selected_data.to_csv('selected_data.csv', index=False)
# save concept map
q2k = {}
table = selected_data.loc[:, ['question_id', 'knowledge_id']].drop_duplicates()
for i, row in table.iterrows():
    q = str(row['question_id'])
    q2k[q] = list(map(int, str(row['knowledge_id']).split('_')))
with open('concept_map.json', 'w') as f:
    json.dump(q2k, f)

def parse_data(data):
    """ 

    Args:
        data: list of triplets (sid, qid, score)
        
    Returns:
        student based datasets: defaultdict {sid: {qid: score}}
        question based datasets: defaultdict {qid: {sid: score}}
    """
    stu_data = defaultdict(lambda: defaultdict(dict))
    ques_data = defaultdict(lambda: defaultdict(dict))
    for i, row in data.iterrows():
        sid = row.student_id
        qid = row.question_id
        correct = row.correct
        stu_data[sid][qid] = correct
        ques_data[qid][sid] = correct
    return stu_data, ques_data
data = []
for i, row in selected_data.iterrows():
    data.append([row.student_id, row.question_id, row.correct])
stu_data, ques_data = parse_data(selected_data)
test_size = 0.2
least_test_length=150
n_students = len(stu_data)
if isinstance(test_size, float):
    test_size = int(n_students * test_size)
train_size = n_students - test_size
assert(train_size > 0 and test_size > 0)

students = list(range(n_students))
random.shuffle(students)
if least_test_length is not None:
    student_lens = defaultdict(int)
    for t in data:
        student_lens[t[0]] += 1
    students = [student for student in students
                if student_lens[student] >= least_test_length]
test_students = set(students[:test_size])

train_data = [record for record in data if record[0] not in test_students]
test_data = [record for record in data if record[0] in test_students]
def renumber_student_id(data):
    """

    Args:
        data: list of triplets (sid, qid, score)
    
    Returns:
        renumbered datasets: list of triplets (sid, qid, score)
    """
    student_ids = sorted(set(t[0] for t in data))
    renumber_map = {sid: i for i, sid in enumerate(student_ids)}
    data = [(renumber_map[t[0]], t[1], t[2]) for t in data]
    return data
train_data = renumber_student_id(train_data)
test_data = renumber_student_id(test_data)
all_data = renumber_student_id(data)
print(f'train records length: {len(train_data)}')
print(f'test records length: {len(test_data)}')
print(f'all records length: {len(all_data)}')

def save_to_csv(data, path):
    """

    Args:
        data: list of triplets (sid, qid, correct)
        path: str representing saving path
    """
    pd.DataFrame.from_records(sorted(data), columns=['student_id', 'question_id', 'correct']).to_csv(path, index=False)
save_to_csv(train_data, 'train_triples.csv')
save_to_csv(test_data, 'test_triples.csv')
save_to_csv(all_data, 'triples.csv')
metadata = {"num_students": n_students, 
            "num_questions": c,
            "num_concepts": d, 
            "num_records": len(all_data), 
            "num_train_students": n_students - len(test_students), 
            "num_test_students": len(test_students)}
with open('metadata.json', 'w') as f:
    json.dump(metadata, f)
 