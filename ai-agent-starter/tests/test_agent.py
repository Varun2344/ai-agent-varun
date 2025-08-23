
import os
from agent import Retriever, run

def test_basic_response():
    r = Retriever("./db")
    out = run("Say hello in one line.", r)
    assert isinstance(out["answer"], str) and len(out["answer"]) > 0
