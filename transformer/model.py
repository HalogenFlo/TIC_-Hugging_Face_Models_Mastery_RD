import torch
import torch.nn as nn
import numpy as np
import math
from transformers.modeling_outputs import SequenceClassifierOutput

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_length=5000):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_length, d_model)
        position = torch.arange(0,max_length, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0,d_model,2).float()*(-math.log(10000.0)/d_model))
        pe[:, 0::2] = torch.sin(position*div_term)
        pe[:, 1::2] = torch.cos(position*div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe',pe)
        
    def forward(self, x):
        # x: (batch_size, seq_len, d_model)
        x = x + self.pe[:, :x.size(1),:]
        return self.dropout(x)
        # output: (batch_size, seq_len, d_model)

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads):
        super().__init__()
        assert d_model % n_heads == 0
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads

        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)

    def scaled_dot_product_attention(self, q, k, v, mask=None):
        # q, k, v: (batch_size, n_heads, seq_len, d_k)
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)
        # attn_scores: (batch_size, n_heads, seq_len, seq_len)
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)
        attn_probs = torch.softmax(attn_scores, dim=-1)
        output = torch.matmul(attn_probs, v)
        # output: (batch_size, n_heads, seq_len, d_k)
        return output
    
    def forward(self, q, k, v, mask=None):
        # q, k, v: (batch_size, seq_len, d_model)
        batch_size = q.size(0)

        q = self.w_q(q).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        k = self.w_k(k).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        v = self.w_v(v).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        # q, k, v sau transpose: (batch_size, n_heads, seq_len, d_k)

        attn_output = self.scaled_dot_product_attention(q,k,v,mask)
        # attn_output: (batch_size, n_heads, seq_len, d_k)
        
        attn_output = attn_output.transpose(1,2).contiguous().view(batch_size,-1,self.d_model)
        # attn_output: (batch_size, seq_len, d_model)
        
        return self.w_o(attn_output)
        # output: (batch_size, seq_len, d_model)

class PositionWiseFeedForward(nn.Module):
    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.fc1 = nn.Linear(d_model,d_ff)
        self.fc2 = nn.Linear(d_ff,d_model)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # x: (batch_size, seq_len, d_model)
        x = self.fc1(x) # (batch_size, seq_len, d_ff)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x) # (batch_size, seq_len, d_model)
        return x

class TransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        super().__init__()
        self.attn = MultiHeadAttention(d_model, n_heads)
        self.ff = PositionWiseFeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
    def forward(self, x, mask=None):
        # x: (batch_size, seq_len, d_model)
        attn_output = self.attn(x,x,x,mask)
        x = self.norm1(x + self.dropout(attn_output))
        # x: (batch_size, seq_len, d_model)
        
        dff_output = self.ff(x)
        x = self.norm2(x + self.dropout(dff_output))
        # x: (batch_size, seq_len, d_model)
        return x

class TransformerClassifier(nn.Module):
    def __init__(self, vocab_size, d_model, n_heads, n_layers, d_ff, n_classes, max_len=512, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model, dropout, max_len)
        self.encoder_layer = nn.ModuleList([
            TransformerEncoderLayer(d_model,n_heads,d_ff,dropout)
            for _ in range(n_layers)
        ])
        self.fc = nn.Linear(d_model, n_classes)
    def forward(self, x, labels=None, mask=None):
        # x: (batch_size, seq_len)
        x = self.embedding(x) * math.sqrt(self.embedding.embedding_dim)
        # x: (batch_size, seq_len, d_model)
        
        x = self.pos_encoding(x)
        # x: (batch_size, seq_len, d_model)

        for layer in self.encoder_layer:
            x = layer(x, mask)
            # x: (batch_size, seq_len, d_model)

        x = x.mean(dim=1)
        # x: (batch_size, d_model)
        
        logits = self.fc(x)
        # logits: (batch_size, n_classes)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits, labels)

        return SequenceClassifierOutput(
            loss=loss,
            logits=logits
        )