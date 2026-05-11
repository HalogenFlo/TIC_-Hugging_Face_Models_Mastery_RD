"""
Chức năng: Định nghĩa kiến trúc Transformer Encoder từ đầu bằng PyTorch.
Lý do tạo: Để người dùng hiểu sâu về cơ chế Self-Attention và kiến trúc Transformer theo lộ trình Step 4.
Tham khảo: 
- "Attention Is All You Need" (Vaswani et al., 2017): https://arxiv.org/abs/1706.03762
- The Annotated Transformer: https://nlp.seas.harvard.edu/2018/04/03/attention.html
"""

import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    """
    Lý do: Transformer không có tính tuần tự, nên cần thêm thông tin vị trí vào vector nhúng.
    Link: https://arxiv.org/pdf/1706.03762.pdf#page=6 (Mục 3.5)
    """
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

class MultiHeadAttention(nn.Module):
    """
    Lý do: Cho phép mô hình tập trung vào các phần khác nhau của chuỗi đồng thời.
    Link: https://arxiv.org/pdf/1706.03762.pdf#page=4 (Mục 3.2.2)
    """
    def __init__(self, d_model, n_heads):
        super(MultiHeadAttention, self).__init__()
        assert d_model % n_heads == 0
        
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        
    def scaled_dot_product_attention(self, q, k, v, mask=None):
        attn_scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)
        attn_probs = torch.softmax(attn_scores, dim=-1)
        output = torch.matmul(attn_probs, v)
        return output

    def forward(self, q, k, v, mask=None):
        batch_size = q.size(0)
        
        q = self.w_q(q).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        k = self.w_k(k).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        v = self.w_v(v).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        
        attn_output = self.scaled_dot_product_attention(q, k, v, mask)
        
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.w_o(attn_output)

class PositionWiseFeedForward(nn.Module):
    """
    Lý do: Áp dụng phép biến đổi phi tuyến cho từng vị trí.
    Link: https://arxiv.org/pdf/1706.03762.pdf#page=5 (Mục 3.3)
    """
    def __init__(self, d_model, d_ff, dropout=0.1):
        super(PositionWiseFeedForward, self).__init__()
        self.fc1 = nn.Linear(d_model, d_ff)
        self.fc2 = nn.Linear(d_ff, d_model)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.fc2(self.dropout(self.relu(self.fc1(x))))

class TransformerEncoderLayer(nn.Module):
    """
    Lý do: Khối cơ bản kết hợp Self-Attention và FeedForward.
    Link: https://arxiv.org/pdf/1706.03762.pdf#page=3 (Hình 1 - Left)
    """
    def __init__(self, d_model, n_heads, d_ff, dropout=0.1):
        super(TransformerEncoderLayer, self).__init__()
        self.self_attn = MultiHeadAttention(d_model, n_heads)
        self.feed_forward = PositionWiseFeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        attn_output = self.self_attn(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        return x

class TransformerClassifier(nn.Module):
    """
    Lý do: Model hoàn chỉnh cho bài toán phân loại văn bản.
    Sử dụng kiến trúc Encoder kết hợp với lớp Linear ở cuối.
    """
    def __init__(self, vocab_size, d_model, n_heads, n_layers, d_ff, n_classes, max_len=512, dropout=0.1):
        super(TransformerClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model, dropout, max_len)
        self.encoder_layers = nn.ModuleList([
            TransformerEncoderLayer(d_model, n_heads, d_ff, dropout) 
            for _ in range(n_layers)
        ])
        self.fc = nn.Linear(d_model, n_classes)
        
    def forward(self, x, mask=None):
        x = self.embedding(x) * math.sqrt(self.embedding.embedding_dim)
        x = self.pos_encoding(x)
        
        for layer in self.encoder_layers:
            x = layer(x, mask)
            
        x = x.mean(dim=1) 
        return self.fc(x)
