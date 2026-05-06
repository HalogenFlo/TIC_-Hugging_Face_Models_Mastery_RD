from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

tokenizer = AutoTokenizer.from_pretrained("VietAI/gpt-j-6B-vietnamese-news")
model = AutoModelForCausalLM.from_pretrained("VietAI/gpt-j-6B-vietnamese-news", low_cpu_mem_usage=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
model.to(device)

prompt = "Tiềm năng của trí tuệ nhân tạo" # your input sentence
input_ids = tokenizer(prompt, return_tensors="pt")['input_ids'].to(device)

gen_tokens = model.generate(
        input_ids,
        max_length=100,
        do_sample=True,
        temperature=0.9,
        top_k=20,
    )

gen_text = tokenizer.batch_decode(gen_tokens)[0]
print(gen_text)
