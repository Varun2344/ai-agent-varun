
import gradio as gr
from agent import Retriever, run

retriever = Retriever("./db")

def chat_fn(question, model_name):
    out = run(question, retriever, model=model_name)
    header = f"**Tool used:** `{out['tool']}`\n\n"
    return header + out["answer"]

with gr.Blocks() as demo:
    gr.Markdown("# 🔎 Domain-Aware AI Agent (Free, Local)")
    with gr.Row():
        inp = gr.Textbox(label="Ask in-domain question", placeholder="e.g., What is RAG? Cite sources.", scale=3)
        model = gr.Dropdown(choices=["mistral:7b","llama3.1:8b","tinyllama"], value="mistral:7b", label="Model")
    btn = gr.Button("Ask")
    out_md = gr.Markdown()
    btn.click(fn=chat_fn, inputs=[inp, model], outputs=out_md)
    gr.Markdown("Tip: Run ingestion first to load your own documents. Smaller models run faster.")

if __name__ == "__main__":
    demo.launch()  # set share=True to expose publicly
