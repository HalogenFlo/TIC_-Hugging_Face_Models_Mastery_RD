import gradio as gr
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoImageProcessor, AutoModelForSequenceClassification, AutoModelForImageClassification, pipeline
from peft import PeftModel
from PIL import Image, ImageOps
import numpy as np

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

print("Loading emotion tokenizer and model...")
emotion_model_name = "HalogenFlo/microsoft-deberta-v3-base-emotion-recognition"
emotion_tokenizer = AutoTokenizer.from_pretrained(emotion_model_name)
emotion_model = AutoModelForSequenceClassification.from_pretrained(emotion_model_name).to(device)
emotion_labels = ["sadness", "joy", "love", "anger", "fear", "surprise"]

def predict_emotion(text):
    inputs = emotion_tokenizer(text, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = emotion_model(**inputs)
    pros = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
    # pred = torch.argmax(pros, dim=-1)
    results = {emotion_labels[i]: float(pros[i]) for i in range(len(emotion_labels))} 
    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))

print("Loading vit processor and model...")
emnist_model_name = "HalogenFlo/vit-emnist-byclass"
process = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
emnist_model = AutoModelForImageClassification.from_pretrained(emnist_model_name).to(device)
emnist_labels = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]
def predict_character(image):
    if image is None:
        return {}
    
    # Extract the composite PIL Image from gr.Sketchpad dict
    pil_image = image.get("composite") if isinstance(image, dict) else image
    if pil_image is None:
        return {}
        
    try:
        # Convert to RGBA to easily handle transparency
        rgba_image = pil_image.convert("RGBA")
        
        # Create a solid white background of the same size
        white_bg = Image.new("RGBA", rgba_image.size, (255, 255, 255, 255))
        
        # Standardize: Composite the drawing onto the white background
        composite = Image.alpha_composite(white_bg, rgba_image)
        
        # Convert to Grayscale
        gray_image = composite.convert("L")
        
        # EMNIST models require white strokes on a black background.
        # Detect if the background is light (avg_color > 127) and invert if necessary.
        avg_color = np.mean(np.array(gray_image))
        if avg_color > 127:
            gray_image = ImageOps.invert(gray_image)
            
        # Convert back to RGB for the Vision Transformer processor
        processed_image = gray_image.convert("RGB")
        rgb_image = processed_image.resize((224, 224))
        
        inputs = process(images=rgb_image, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = emnist_model(**inputs)
        
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
        topk_probs, topk_idx = torch.topk(probs, 5)
        
        results = {
            emnist_labels[int(idx.item())]: float(val.item())
            for val, idx in zip(topk_probs, topk_idx)
        }
        return results
    except Exception as e:
        print(f"Error predicting character: {e}")
        return {}

def predict_character_upload(image):
    if image is None:
        return {}
    
    try:
        pil_image = image if isinstance(image, Image.Image) else Image.open(image)

        gray_image = pil_image.convert("L")
        
        avg_color = np.mean(np.array(gray_image))
        if avg_color > 127:
            gray_image = ImageOps.invert(gray_image)
        rgb_image = gray_image.convert("RGB").resize((224, 224))
        
        inputs = process(images=rgb_image, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = emnist_model(**inputs)
        
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
        topk_probs, topk_idx = torch.topk(probs, 5)
        
        return {
            emnist_labels[int(idx.item())]: float(val.item())
            for val, idx in zip(topk_probs, topk_idx)
        }
    except Exception as e:
        print(f"Error predicting from uploaded image: {e}")
        return {}


print("Loading llm processor and model...")
base_model_name = "Qwen/Qwen2.5-0.5B-Instruct"
llm_model_name = "HalogenFlo/qwen-2.5b-finetuned-qlora"
llm_tokenizer = AutoTokenizer.from_pretrained(base_model_name)
base_model = AutoModelForCausalLM.from_pretrained(base_model_name).to(device)
llm_model = PeftModel.from_pretrained(base_model, llm_model_name)

def format_covert(text):
    return f"<|im_start|>user\n{text}\n<|im_end|>\n<|im_start|>assistant"

def generate_text(message, history):
    try:
        inputs = llm_tokenizer(format_covert(message), return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = llm_model.generate(
                **inputs,
                max_length=2048,
                do_sample=False,
                repetition_penalty=1.15,
                eos_token_id=llm_tokenizer.eos_token_id,
                pad_token_id=llm_tokenizer.pad_token_id
            )
        response = llm_tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
        return response
    except Exception as e:
        print(f"Error generating text: {e}")
        return f"Error: {str(e)}"

custom_css = """
body, .gradio-container {
    background: #0f172a !important;
    color: #f1f5f9 !important;
}
.main-title {
    color: #38bdf8;
    text-align: center;
    font-weight: 800;
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}
.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 2rem;
}
.primary-btn {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
}
"""

with gr.Blocks(css=custom_css, title="TIC AI Hub") as demo:
    gr.HTML("<h1 class='main-title'>TIC Multi-Task AI Hub</h1>")
    gr.HTML("<p class='subtitle'>Experience 3 state-of-the-art AI models from the HF Mastery R&D roadmap</p>")
    
    with gr.Tabs():
        # Tab 1: Emotion Classifier
        with gr.TabItem("Emotion Classification"):
            gr.Markdown("### Analyze the emotion of English text using DeBERTa-v3")
            with gr.Row():
                with gr.Column():
                    txt_input = gr.Textbox(
                        label="Enter English text to analyze", 
                        placeholder="Type something here...",
                        lines=4
                    )
                    with gr.Row():
                        clear_btn_e = gr.Button("Clear", elem_classes="secondary-btn")
                        submit_btn_e = gr.Button("Analyze", elem_classes="primary-btn")
                with gr.Column():
                    lbl_emotion = gr.Label(label="Emotion Probabilities", num_top_classes=6)
            
            submit_btn_e.click(fn=predict_emotion, inputs=txt_input, outputs=lbl_emotion)
            clear_btn_e.click(fn=lambda: ("", None), outputs=[txt_input, lbl_emotion])
            
        # Tab 2: Handwriting Recognition
        with gr.TabItem("Handwriting Recognition"):
            gr.Markdown("### Recognize handwritten characters and digits using ViT")
            with gr.Tabs():
                # Sub-tab: Vẽ tay
                with gr.TabItem("✏️ Draw"):
                    with gr.Row():
                        with gr.Column():
                            img_input = gr.Sketchpad(
                                label="Draw a character on the sketchpad below", 
                                type="pil"
                            )
                            with gr.Row():
                                clear_btn_h = gr.Button("Clear", elem_classes="secondary-btn")
                                submit_btn_h = gr.Button("Predict", elem_classes="primary-btn")
                        with gr.Column():
                            lbl_handwrite = gr.Label(label="Top 5 Predicted Characters", num_top_classes=5)
                    
                    submit_btn_h.click(fn=predict_character, inputs=img_input, outputs=lbl_handwrite)
                    clear_btn_h.click(fn=lambda: (None, None), outputs=[img_input, lbl_handwrite])
                
                # Sub-tab: Upload ảnh
                with gr.TabItem("📷 Upload Image"):
                    with gr.Row():
                        with gr.Column():
                            img_upload = gr.Image(
                                label="Upload an image of a handwritten character",
                                type="pil",
                                sources=["upload", "clipboard"]
                            )
                            with gr.Row():
                                clear_btn_u = gr.Button("Clear", elem_classes="secondary-btn")
                                submit_btn_u = gr.Button("Predict", elem_classes="primary-btn")
                        with gr.Column():
                            lbl_upload = gr.Label(label="Top 5 Predicted Characters", num_top_classes=5)
                    
                    submit_btn_u.click(fn=predict_character_upload, inputs=img_upload, outputs=lbl_upload)
                    clear_btn_u.click(fn=lambda: (None, None), outputs=[img_upload, lbl_upload])
            
        # Tab 3: Chatbot
        with gr.TabItem("AI Chatbot"):
            gr.Markdown("### Interactive conversation with fine-tuned Qwen2.5 LLM")
            gr.ChatInterface(fn=generate_text)
    gr.HTML("<div style='text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 2rem;'>R&D Project developed by HalogenFlo</div>")

if __name__ == "__main__":
    demo.launch()