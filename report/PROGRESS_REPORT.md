# TIC Project Progress Report - Hugging Face Mastery

## Date Updated: 2026-05-06
## Status: **Step 1 - COMPLETED
## Status: **Step 2 - COMPLETED 
## Step 3 - IN PROGRESS**

---

### Tasks completed in Step 1:
1.  **Environment Setup:** Initialized Python venv and configured environment variables.
2.  **Library Installation:** Completed installation of the SOTA toolkit for LLMs.
3.  **Knowledge Systematization:** Understood the roles of Tokenization libraries (converting text -> tokens -> numbers) and Serialization (saving models to disk and loading them).

---

### Installed Libraries & Technical Rationale

| Library | Role / Reason for Installation | Importance for the Project |
| :--- | :--- | :--- |
| **`transformers`** | Core Hugging Face library to load and run models (BERT, Llama, Qwen...). | Contains optimized pre-trained architectures, which can be used for fine-tuning on custom datasets. |
| **`datasets`** | Manages, downloads, and pre-processes large-scale training data. | Supports efficient processing of large datasets. |
| **`tokenizers`** | High-performance tokenizer written in Rust. | Processes text and syllables with extremely high speed. |
| **`accelerate`** | Optimizes training on GPU/TPU and supports Distributed Training. | Essential for training large LLM models. |
| **`peft`** | Supports efficient Fine-tuning techniques (LoRA, DoRA, Prefix Tuning). | Helps reduce hardware costs when fine-tuning models for enterprises. |
| **`bitsandbytes`** | Supports Quantization (8-bit, 4-bit) to reduce VRAM memory. | Allows running/training LLMs on consumer-grade GPUs (12GB-16GB). |
| **`sentencepiece`** | Subword-based tokenization engine, required for Llama, Mistral, T5 families. | Helps read `.model` files containing language rules of SOTA models. |
| **`protobuf`** | Standardizes reading/writing configuration data and model tokenizers. | A prerequisite for the SentencePiece library to work stably. |
| **`unsloth`** | Tool to optimize LLM training to be 2-5x faster and save 70% VRAM. | **Key SOTA** of the project to achieve the highest performance. |
| **`google-cloud-aiplatform`** | SDK to interact with Google Vertex AI. | Serves for deploying models to Production environment (Step 12). |

---

### Tasks completed in Step 2:
*   **Implement standard Machine Learning pipeline:**
    *   Define the problem and data
    *   Tokenization and data preprocessing
    *   Select a pre-trained model
    *   Fine-tuning
    *   Acceleration and optimization
    *   Model evaluation
    *   Model deployment
    *   Save and share the model
*   **Compare ML, DL, and LLM:**
    *   **ML:** Simple, uses traditional algorithms, structured or unstructured tabular data, runs on CPU, trained from scratch.
    *   **DL:** Uses multi-layer neural network Deep Learning models, various data types (image, video, audio, text), runs on GPU, can be trained from scratch or use pre-trained architecture for fine-tuning.
    *   **LLM:** Uses Large Language Models, massive text data, runs on GPU, uses pre-trained architecture for fine-tuning.
*   **Evaluation Metrics:**
    *   **Text Classification:** accuracy, f1-score, precision, recall
    *   **Machine Translation:** BLEU, METEOR
    *   **Text Summarization:** ROUGE-1, ROUGE-2, ROUGE-L
    *   **Text Generation:** Perplexity, BLEU, BERTScore
    *   **Dialogue (Chatbot):** Human Evaluation (Fluency, Relevance, Coherence)
*   Download English dataset: **Using `dair-ai/emotion` (Emotion Recognition with 6 labels).**
    *   Create relationships between labels and ids
    *   Normalize labels to ids
    *   Load tokenizer and model `microsoft/deberta-v3-base`
*   Train a simple Text Classifier: **Created source code `TIC_Mastery.ipynb` using `microsoft/deberta-v3-base` combined with the Trainer API to classify 6 types of emotions.**
    *   Select evaluation metrics: accuracy and f1-score
    *   Set number of epochs to 5 and batch size to 16
    *   Train the model
    *   Evaluate the model
    *   Save and share the model

---

### Step 3: Deep Learning Standard Workflow
*   **Research & Learning: [COMPLETED]**
    *   **ML vs DL Difference:** Transitioned from sequence-level classification (Step 2) to understanding automatic feature extraction and deep neural architectures.
    *   **Transformer Architecture & Self-Attention:** Studied the Query, Key, and Value mechanisms that allow models to capture global dependencies and process data in parallel.
    *   **Feature Extractors vs. Tokenizers:** Learned the role of `ImageProcessors` in Vision Transformers (ViT) for normalization and patching, compared to `Tokenizers` in NLP.
*   **Actions (Conceptual Research):**
    *   **Task Selection:** Analyzed Vision Transformers (ViT) for Image Classification vs. NER for token-level NLP.
    *   **Model Selection:** Evaluated SOTA architectures like `google/vit-base-patch16-224` and `bert-base-cased`.
    *   **Comparison Report:** Finalized the technical comparison between ML and DL pipelines in the Hugging Face ecosystem.
*   **Planned Milestone:**
    *   [ ] Train a DL model using high-level HF tools.
    *   [ ] Push the model to Hugging Face Hub with a comprehensive Model Card.
    *   [ ] Finalize the ML vs DL comparison documentation.

---
*This report is automatically updated to track the Hugging Face Mastery roadmap.*
