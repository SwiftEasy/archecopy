import os
from openai import OpenAI
import gradio as gr
import logging as log
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
CHAT_COMPLETION_ENDPOINT = os.getenv("CHAT_COMPLETION_ENDPOINT")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

log.info("CHAT_COMPLETION_ENDPOINT: ", CHAT_COMPLETION_ENDPOINT)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=CHAT_COMPLETION_ENDPOINT)

def predict(message, history):
    history.append({"role": "user", "content": message})
    log.info("CHAT_COMPLETION_ENDPOINT: ", CHAT_COMPLETION_ENDPOINT)
    log.info("history: ", history)

    # Custom headers
    custom_headers = {
        'x-bolt-openai-api-key': f"{OPENAI_API_KEY}",
        'x-bolt-mistral-api-key': f"{MISTRAL_API_KEY}",
    }

    try:
      response = client.chat.completions.create(model=MODEL_NAME,
        messages= history,
        temperature=1.0,
        extra_headers=custom_headers
      )
    except Exception as e:
      log.info(e)
      # remove last user message in case of exception
      history.pop()
      log.info("CHAT_COMPLETION_ENDPOINT: ", CHAT_COMPLETION_ENDPOINT)
      log.info("Error calling gateway API: {}".format(e.message))
      raise gr.Error("Error calling gateway API: {}".format(e.message))

    choices = response.choices
    message = choices[0].message
    content = message.content
    history.append({"role": "assistant", "content": content})
    history[-1]["model"] = response.model

    messages = [(history[i]["content"], history[i+1]["content"]) for i in range(0, len(history)-1, 2)]
    return messages, history


with gr.Blocks(fill_height=True, css="footer {visibility: hidden}") as demo:
    print("Starting Demo...")
    chatbot = gr.Chatbot(label="Bolt Chatbot", scale=1)
    state = gr.State([])
    with gr.Row():
        txt = gr.Textbox(show_label=False, placeholder="Enter text and press enter", scale=1, autofocus=True)

    txt.submit(predict, [txt, state], [chatbot, state])

demo.launch(server_name="0.0.0.0", server_port=8080, show_error=True, debug=True)
