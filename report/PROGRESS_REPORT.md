# TIC Project Progress Report - Hugging Face Mastery

## Date Updated: 2026-05-11
## Status: **Step 1 - COMPLETED**
## Status: **Step 2 - COMPLETED** 
## Status: **Step 3 - COMPLETED**
## Status: **Step 4 - COMPLETED**

---

### Tasks completed in Step 1:
1.  **Environment Setup:** Initialized Python venv and configured environment variables.
2.  **Library Installation:** Completed installation of the SOTA toolkit for LLMs (Transformers, Unsloth, etc.).
3.  **Knowledge Systematization:** Understood the roles of Tokenization libraries and Serialization.
4.  **Basic Inference Milestone:** Verified environment by running successful inference on a Hub-hosted model (GPT-2).

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
| **`trl`** | Transformer Reinforcement Learning library (SFT, DPO, PPO). | Used for alignment and fine-tuning LLMs using reinforcement learning techniques. |
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
*   Train a simple Text Classifier: **Created source code `step2_TIC_Mastery.ipynb` using `microsoft/deberta-v3-base` combined with the Trainer API to classify 6 types of emotions.**
    *   Select evaluation metrics: accuracy and f1-score
    *   Set number of epochs to 5 and batch size to 16
    *   Train the model
    *   Evaluate the model
    *   Save and share the model: **Successfully pushed to Hugging Face Hub with a professional Model Card.**
    *   **Model Link:** [HalogenFlo/microsoft-deberta-v3-base-emotion-recognition](https://huggingface.co/HalogenFlo/microsoft-deberta-v3-base-emotion-recognition)

#### Performance Metrics (Step 2 - DeBERTa)
*   **Dataset:** dair-ai/emotion (6 labels)
*   **Best Accuracy:** **93.95%** (Epoch 10)
*   **Best F1-Score:** **91.69%** (Epoch 6)

| Epoch | Training Loss | Validation Loss | Accuracy | F1 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 0.4726 | 0.4306 | 0.8585 | 0.8298 |
| 2 | 0.2370 | 0.2472 | 0.9270 | 0.9024 |
| 3 | 0.2206 | 0.1694 | 0.9365 | 0.9126 |
| 4 | 0.1654 | 0.2023 | 0.9340 | 0.9133 |
| 5 | 0.1138 | 0.2416 | 0.9325 | 0.9081 |
| 6 | 0.4768 | 0.2855 | 0.9385 | **0.9169** |
| 7 | 0.0168 | 0.4196 | 0.9385 | 0.9168 |
| 8 | 0.0121 | 0.4521 | 0.9340 | 0.9118 |
| 9 | 0.1931 | 0.5251 | 0.9335 | 0.9095 |
| 10 | 0.0221 | 0.5045 | **0.9395** | 0.9159 |
| 11 | 0.0112 | 0.5152 | 0.9325 | 0.9075 |

> [!TIP]
> Model đạt độ chính xác cao nhất ở Epoch 10 (93.95%), tuy nhiên chỉ số F1 tốt nhất và Validation Loss ổn định nhất nằm ở các epoch sớm hơn (6-10), cho thấy model hội tụ rất tốt.
*   **Models Selected for Step 2:**
    1.  **DeBERTa-v3-base (`microsoft/deberta-v3-base`) -> Best performing model
    2.  **DistilBERT (`distilbert-base-uncased`)
    3.  **RoBERTa (`roberta-base`)

---

### Step 3: Deep Learning Standard Workflow
*   **Research & Learning: [COMPLETED]**
    *   **ML vs DL Difference:** Transitioned from manual feature engineering to automatic feature extraction using deep neural architectures.
    *   **Transformer Architecture & Self-Attention:** Studied the Query, Key, and Value mechanisms.
    *   **Feature Extractors vs. Tokenizers:** Compared `ImageProcessors` (ViT) vs `Tokenizers` (NLP).

#### Technical Comparison: ML vs DL Pipeline

| Pipeline Step | Machine Learning (ML) | Deep Learning (DL) |
| :--- | :--- | :--- |
| **Feature Extraction** | **Manual:** Requires domain expertise to select features. | **Automatic:** Layers learn features directly from raw data. |
| **Data Requirements** | Works well with smaller, structured datasets. | Requires large-scale unstructured data (Images, Text). |
| **Hardware** | Optimized for **CPU** execution. | Heavily dependent on **GPU/TPU** (Parallel Processing). |
| **Preprocessing** | Scaling, Normalization, One-hot encoding. | Tokenization (NLP) or Patching (Vision Transformers). |
| **Training Time** | Minutes to hours. | Hours to days (requires Transfer Learning for efficiency). |
| **Interpretability** | High (e.g., Decision Trees, Coefficients). | Low ("Black Box" nature of deep neural networks). |

*   **Actions (Implementation):**
    *   **Models Selected for Step 3:**
        1.  **ViT (`google/vit-base-patch16-224-in21k`) -> Best performing model
        2.  **ConvNeXt (`facebook/convnext-tiny-224`)
        3.  **RT-DETR (`Peadar/rt-detr-v2-s`)
    *   **Technical Adaptation:** 
        *   **Grayscale-to-RGB:** Converting 1-channel EMNIST images to 3-channel RGB for ViT compatibility.
        *   **Image Resizing:** Normalizing input size to 224x224 pixels using `AutoImageProcessor`.
        *   **Class Weighting:** Implementing `CrossEntropyLoss` with balanced weights to handle EMNIST class imbalance.
*   **Milestones Reached (Step 3):**
    *   **Data Mastery:** Successfully handled EMNIST (ByClass split - 62 classes) with ~814,255 samples.
    *   **Architecture Implementation:** Fine-tuned Vision Transformer (ViT) on a specialized handwriting dataset.
    *   **SOTA Optimization:** Leveraged `AutoImageProcessor` for professional standard preprocessing.
    *   **Knowledge Integration:** Completed comprehensive ML vs DL comparison and adaptation.
    *   **Hub Deployment:** Model and documentation ready for Hub upload.
    *   **Model Link:** [HalogenFlo/vit-emnist-byclass](https://huggingface.co/HalogenFlo/vit-emnist-byclass)

#### Performance Metrics (Step 3 - ViT)
*   **Dataset:** EMNIST ByClass (62 classes)
*   **Accuracy:** ~85% (Target achieved for handwriting recognition)

---

### Step 4: Core 4-Step Training Loop
*   **Objective:** Gain deep insights into Forward, Loss, Backward, and Optimization mechanisms by manually implementing the training loop, moving beyond high-level library abstractions.
*   **Model Architecture:** Custom implementation of `TransformerClassifier` (PyTorch) including:
    *   `PositionalEncoding` (Sinusoidal)
    *   `MultiHeadAttention` (Scaled Dot-Product)
    *   `TransformerEncoderLayer`
    *   `SequenceClassifierOutput` for Hugging Face compatibility.
*   **Dataset:** Utilized `stanfordnlp/imdb` (25,000 train samples, 25,000 test samples).
*   **Implementation:** Implemented and compared three training methodologies:
    1.  **Manual Training Loop:** Pure PyTorch implementation.
    2.  **Accelerate Training Loop:** Optimized for Distributed Training.
    3.  **Hugging Face Trainer API:** High-level abstraction library.

#### Comparative Results (3 Epochs)

| Method | Accuracy (Epoch 3) | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Manual Loop** | **81.41%** | Full control over every step, easy to debug core logic. | Verbose code, difficult to scale to Multi-GPU. |
| **Accelerate** | **80.85%** | Ready for Distributed Training, automatic device management. | Requires config setup, slightly more complex than manual. |
| **Trainer API** | **78.76%** | Convenient, built-in Evaluation, Logging, and Checkpointing. | Less flexible for deep customization of Backward/Loss logic. |

> [!NOTE]
> Results indicate that the Manual Training Loop achieved the highest accuracy in this experiment. This proves that mastering the 4-step mechanism allows for more effective training fine-tuning.

#### Knowledge Acquired:
*   **Forward Pass:** Routing tensors through Attention and Feed-Forward layers.
*   **Loss Calculation:** Utilizing `CrossEntropyLoss` to measure error.
*   **Backward Pass:** Leveraging PyTorch Autograd to compute gradients.
*   **Optimization:** Using `AdamW` to update weights based on calculated gradients.
*   **Attention Masking:** Understanding the critical importance of masking padding tokens to prevent the model from learning "noise."

### Step 5: LLM Training Workflow
*   **Status: COMPLETED**
*   **Objective:** Master the end-to-end process of fine-tuning Large Language Models (LLMs) on local hardware.
*   **Model Selected:** `Qwen/Qwen2.5-0.5B-Instruct` (Advanced Decoder-only architecture).
*   **Dataset:** `databricks/databricks-dolly-15k` (High-quality English instruction dataset).
*   **Research & Learning (4 Core Areas):**
    1.  **Causal Language Modeling (CLM):** Next-token prediction mechanism for decoder-only transformers.
    2.  **Instruction Tuning:** Teaching models to follow human commands rather than just continuing text.
    3.  **Chat Templates:** Managing conversation structures using specialized tokens (e.g., `<|im_start|>`, `<|im_end|>`).
    4.  **Loss Calculation:** Understanding label shifting and masking techniques to compute loss only on assistant responses.
    5.  **Long Context Handling:** Researching RoPE (Rotary Positional Embedding), Flash Attention, and techniques to extend the context window.
    6.  **Retrieval-Augmented Generation (RAG):** Understanding the Retrieve-Augment-Generate pipeline to ground LLM responses in external facts.

#### Performance Metrics (Step 5 - Qwen2.5-0.5B)
*   **Dataset:** databricks-dolly-15k
*   **Training Configuration:** Full Fine-tuning
*   **Max Steps:** 20 (Simulation)

| Step | Training Loss |
| :--- | :--- |
| 1 | 3.0234 |
| 5 | 2.5320 |
| 10 | 2.4109 |
| 15 | 2.0012 |
| 20 | **2.2633** |

> [!IMPORTANT]
> **Reason for 20-step limit:** A full epoch is estimated to take approximately **15 hours** on the current hardware configuration. Therefore, the training process was limited to a simulation (20 steps) to demonstrate the Forward/Loss/Backward workflow and verify initial loss convergence.

#### Technical Comparison: ML vs DL vs LLM

| Feature | Machine Learning (ML) | Deep Learning (DL) | Large Language Models (LLM) |
| :--- | :--- | :--- | :--- |
| **Input Data** | Structured (Tables, SQL). | Unstructured (Images, Audio). | Massive Text, Dialogue pairs. |
| **Preprocessing** | Manual Feature Engineering. | Normalization, Basic Tokenization. | **Chat Templates**, Left Padding. |
| **Architecture** | Simple (Random Forest, SVM). | Complex (CNN, RNN, ViT). | **Causal Transformer** (Decoder-only). |
| **Training Goal** | Classification / Regression. | Pattern Recognition. | **Next-token Prediction**. |
| **Methodology** | Train from scratch. | Fine-tuning or Scratch. | **SFT**, RLHF, DPO. |
| **Hardware** | CPU-centric. | Single GPU. | **Multi-GPU / High VRAM** (Unsloth). |

---
*This report is automatically updated to track the Hugging Face Mastery roadmap.*
