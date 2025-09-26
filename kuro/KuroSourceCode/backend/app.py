from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM

import torch

from prompts import ORIGINAL_PROMPT_ENGLISH

app = FastAPI()

# Load your MT5 model and tokenizer locally, force slow tokenizer (SentencePiece)
tokenizer = AutoTokenizer.from_pretrained('./models/tinyllama', local_files_only=True, use_fast=False)
model = AutoModelForCausalLM.from_pretrained('./models/tinyllama', local_files_only=True)


class Message(BaseModel):
    text: str

@app.get("/")
async def test():
    return {"status": "ok", "message": "Backend is connected and running!"}


@app.post("/")
async def chat(message: Message):
    # Compose the full prompt for the model
    combined_input = ORIGINAL_PROMPT_ENGLISH + "\nUser: " + message.text + "\nBot: "

    print(combined_input)
    
    # Tokenize input (no eos token needed for MT5)
    input_ids = tokenizer.encode(combined_input, return_tensors="pt")

    # Create attention mask (all ones since no padding)
    attention_mask = torch.ones(input_ids.shape, dtype=torch.long)

    # Generate response from the model
    generated_ids = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_length=200,
        pad_token_id=tokenizer.pad_token_id,
        no_repeat_ngram_size=3,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.1
    )

    # Decode the output, skipping special tokens
    output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

    return {"response": output}
