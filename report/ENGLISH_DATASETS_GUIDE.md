# List of English Datasets For Hugging Face Mastery Roadmap (TIC Project)

Based on the requirements from `REQUIREMENTS.md` and the TIC project's R&D guidelines, below are the recommended English datasets to execute the 12-step roadmap, ensuring optimization for SOTA technologies like Unsloth, LoRA/DoRA, and Alignment (DPO/ORPO).

## 1. Fundamentals & Deep Learning Phase (Steps 2 & 3)

Objective: Get familiar with Trainer API, Tokenization, and basic classification problems.

| Task | Recommended Dataset | Description | HF Link |
| :--- | :--- | :--- | :--- |
| **Text Classification** | `hate_speech18` | Dataset for detecting hate speech. Great for practicing Classification. | [Link](https://huggingface.co/datasets/hate_speech18) |
| **Sentiment Analysis** | `imdb` | Large Movie Review Dataset for binary sentiment classification. | [Link](https://huggingface.co/datasets/imdb) |
| **Emotion Recognition** | `dair-ai/emotion` | Recognizes 6 basic emotions from Twitter data (sadness, joy, love, anger, fear, surprise). | [Link](https://huggingface.co/datasets/dair-ai/emotion) |
| **Fine-grained Emotion** | `go_emotions` | Detailed emotion recognition with 27/28 labels (Multi-label). | [Link](https://huggingface.co/datasets/go_emotions) |
| **NER (Named Entity Recognition)** | `conll2003` | Standard dataset for Named Entity Recognition tasks. | [Link](https://huggingface.co/datasets/conll2003) |
| **Image Classification** | `Food-101` | Classification of 101 food categories, suitable for Step 3 on Computer Vision. | [Link](https://huggingface.co/datasets/ethz/food101) |

## 2. Instruction Tuning Phase (Steps 5, 6 & 7)

Objective: Fine-tune LLMs (Llama 3.2, Qwen 2.5) using Unsloth and LoRA/DoRA. High-quality Instruction datasets are required.

| Dataset | Size | Characteristics | HF Link |
| :--- | :--- | :--- | :--- |
| **tatsu-lab/alpaca** | 52k | Original Stanford Alpaca instruction tuning dataset, popular and stable for basic SFT. | [Link](https://huggingface.co/datasets/tatsu-lab/alpaca) |
| **HuggingFaceH4/instruction-dataset** | 327 | A tiny instruction dataset used for quick testing and alignments. | [Link](https://huggingface.co/datasets/HuggingFaceH4/instruction-dataset) |
| **lmsys/chatbot_arena_conversations** | 33k | Multi-turn conversational data from real user interactions, suitable for training Chatbots in Step 9. | [Link](https://huggingface.co/datasets/lmsys/chatbot_arena_conversations) |

## 3. Alignment & Frontier LLMs Phase (Step 10)

Objective: Align the model to human preferences using DPO (Direct Preference Optimization) or ORPO.

| Dataset | Type | Description | HF Link |
| :--- | :--- | :--- | :--- |
| **Intel/orca_dpo_pairs** | DPO Pairs | Includes answer pairs (Chosen vs Rejected). Essential for DPO/ORPO techniques. | [Link](https://huggingface.co/datasets/Intel/orca_dpo_pairs) |
| **argilla/dpo-mix-7k** | DPO Pairs | High-quality, curated dataset combining various sources for robust preference alignment. | [Link](https://huggingface.co/datasets/argilla/dpo-mix-7k) |

## 4. Specifics for Ecommerce Chatbot

To build a professional ecommerce chatbot, focus on specialized datasets:

| Dataset | Source | Purpose | Description |
| :--- | :--- | :--- | :--- |
| **bitext/Bitext-customer-support-llm-chatbot-training-dataset** | **Synthetic** | **SFT (Sales Support)** | High-quality simulated data on product advice, pricing, and returns. |
| **McGill-NLP/FaithDial** | **Conversational** | **Chatbot (Multi-turn)** | Real dialogues helping models maintain context and reduce hallucinations. |
| **meta-math/MetaMathQA** | **General/Math** | **Customer Support** | Reasoning data that helps the bot process numerical queries (like pricing/discounts). |
| **llm-agents/trak-rag-dataset** | Benchmark | **RAG (Retrieval)** | Used to train model's ability to answer based on provided documents (Product Catalogues). |

## 🚀 Ecommerce Chatbot Deployment Workflow (Roadmap)

1.  **Steps 5-7 (Training):** Fine-tune a model like **Qwen2.5-7B** or **Llama-3.2-3B** using **Unsloth** with the `bitext` support dataset. Use LoRA/DoRA to make the model "smarter" in consulting.
2.  **Step 9 (Demo Building):** Use Gradio combined with a multi-turn chat dataset to create a test Chatbot interface.
3.  **Step 10 (Alignment):** Use DPO with the `orca_dpo_pairs` dataset to ensure the Chatbot always responds politely and avoids negative language (Safety Alignment).
4.  **Step 12 (Production):** Deploy a **RAG** system. When a customer asks about a specific product, the Chatbot will query the company's Database/PDFs via a Vector Database (like Pinecone or Vertex AI Search) before answering.

> [!IMPORTANT]
> For Ecommerce Chatbots, **RAG** is crucial because product data changes constantly. Do not rely solely on the knowledge within the model (Parametric Knowledge).
