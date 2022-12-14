from collections import Counter
from pathlib import Path
import faiss
import json 
import yaml
import numpy as np
import pandas as pd


PATH_TEST=Path("data/test")
PATH_TEST.mkdir(exist_ok=True, parents=True)

## Params
with open("params.yaml") as fp:
    params = yaml.load(fp, Loader=yaml.FullLoader)
dim = params["train"]["latent_dim"] 

# index embeddings
xb = np.load("data/faiss-embeddings/embeddings.npy").astype("float32")
with open("data/faiss-embeddings/id_embeddings.json") as fp:
    id_xb = json.load(fp)
    id_xb = {int(k): v for k,v in id_xb.items()}

# query embeddings
xq = np.load("data/faiss-embeddings/query_embeddings.npy").astype("float32")

with open("data/faiss-embeddings/query_embeddings.json") as fp:
    id_query = json.load(fp)
    id_query = {int(k): v for k,v in id_query.items()}

# build the index
index = faiss.IndexFlatL2(dim)   
print(index.is_trained)

# add vectors to the index
index.add(xb)                  
print(index.ntotal)

# load labels for train+val and test
with open("data/train/labels-train-val-test.json","r") as fp:
    datasets = json.load(fp)
trainval = datasets["train"] + datasets["val"]
trainval_idx = {k:v for k,v in enumerate(trainval)}

# get labels from idx
get_label_= lambda idx: trainval_idx.get(idx)
# vectorize version
get_label = np.vectorize(get_label_)

# query the index
neighbors = 10
D,I = index.search(xq, neighbors)
neighbors_query = get_label(I)
ground_truth = datasets["test"]

def majority_vote(list_neighbors): 
    label, _ = Counter(list_neighbors).most_common(1)[0]
    return label

consensus=np.apply_along_axis(majority_vote, 1, neighbors_query)

df = pd.concat([ pd.DataFrame(datasets["test"],columns=["GT"]), pd.DataFrame(consensus,columns=["consensus"]), pd.DataFrame(neighbors_query)],axis=1)
df.to_csv(PATH_TEST.joinpath("closest_species.tsv"),sep="\t")
