import spacy
import networkx as nx
from pyvis.network import Network

nlp = spacy.load("en_core_web_sm")

def extract_ae_triplets(text):
    doc = nlp(text)
    triplets = []
    for sent in doc.sents:
        subj, verb, obj = None, None, None
        for token in sent:
            if token.dep_ == "nsubj":
                subj = token.text
            elif token.pos_ == "VERB":
                verb = token.text
            elif token.dep_ == "dobj":
                obj = token.text
        if subj and verb and obj:
            triplets.append((subj, verb, obj))
    return triplets

def build_graph(triplets):
    g = nx.DiGraph()
    for subj, verb, obj in triplets:
        g.add_edge(subj, obj, label=verb)
    return g

def visualize_graph(graph, output_file):
    net = Network(height="500px", width="100%", directed=True)
    for u, v, data in graph.edges(data=True):
        net.add_node(u, label=u)
        net.add_node(v, label=v)
        net.add_edge(u, v, label=data['label'])
    net.show(output_file)