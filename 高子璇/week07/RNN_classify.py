import jieba
import pandas as pd
from collections import Counter
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
import time

# 1. 数据准备
file_path = r'C:\Users\e0973783\Desktop\大模型学习\week7 文本分类问题\week7 文本分类问题\文本分类练习.csv'
df = pd.read_csv(file_path, header=None, names=['label', 'text'])
texts = df['text'].tolist()[1:]
labels = [int(label) for label in df['label'].tolist()[1:]]  # 确保标签为整数


# 分词
def tokenize(text):
    return list(jieba.cut(text))


tokenized_texts = [tokenize(text) for text in texts]

# 构建词表
word_counts = Counter()
for tokens in tokenized_texts:
    word_counts.update(tokens)
vocab_size = min(2000, len(word_counts))  # 不超过实际词表大小
vocab = {word: idx + 2 for idx, (word, _) in enumerate(word_counts.most_common(vocab_size))}
vocab['<PAD>'] = 0
vocab['<UNK>'] = 1


# 编码文本
def encode_text(tokens, vocab, max_len):
    encoded = [vocab.get(token, vocab['<UNK>']) for token in tokens]
    return encoded[:max_len] + [vocab['<PAD>']] * (max_len - len(encoded))  # 确保固定长度


max_len = 30
encoded_texts = [encode_text(tokens, vocab, max_len) for tokens in tokenized_texts]

# 分割数据集
train_texts, test_texts, train_labels, test_labels = train_test_split(
    encoded_texts, labels, test_size=0.2, random_state=42, stratify=labels
)


# 2. 定义Dataset和DataLoader
class TextDataset(Dataset):
    def __init__(self, texts, labels):
        self.texts = texts
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return torch.tensor(self.texts[idx]), torch.tensor(self.labels[idx])


batch_size = 32
train_dataset = TextDataset(train_texts, train_labels)
test_dataset = TextDataset(test_texts, test_labels)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)


# 3. 定义模型（Embedding + LSTM）
class TextRNN(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        x = self.embedding(x)
        _, (h_n, _) = self.lstm(x)
        return self.fc(h_n.squeeze(0))


# 初始化模型
vocab_size = len(vocab)
embed_dim = 100
hidden_dim = 128
num_classes = 2
model = TextRNN(vocab_size, embed_dim, hidden_dim, num_classes)

# 4. 训练配置
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
epochs = 10

# 5. 训练循环
for epoch in range(epochs):
    model.train()
    train_loss, train_correct = 0, 0

    for texts, labels in train_loader:
        texts, labels = texts.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(texts)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        train_correct += (outputs.argmax(1) == labels).sum().item()

    train_acc = train_correct / len(train_dataset)

    model.eval()
    test_correct = 0
    with torch.no_grad():
        for texts, labels in test_loader:
            texts, labels = texts.to(device), labels.to(device)
            outputs = model(texts)
            test_correct += (outputs.argmax(1) == labels).sum().item()

    test_acc = test_correct / len(test_dataset)

    print(f'Epoch {epoch + 1}/{epochs}: '
          f'Train Loss: {train_loss / len(train_loader):.4f}, '
          f'Train Acc: {train_acc:.4f}, '
          f'Test Acc: {test_acc:.4f}')

# 6. 预测耗时测试
model.eval()
test_samples = test_texts[:100]  # 确保不超过测试集大小
test_labels = test_labels[:100]

# 转换为Tensor（已确保所有样本长度为max_len）
test_tensor = torch.tensor(test_samples).to(device)
label_tensor = torch.tensor(test_labels).to(device)

# 预热
with torch.no_grad():
    _ = model(test_tensor[:1])

# 正式计时
start_time = time.time()
with torch.no_grad():
    outputs = model(test_tensor)
elapsed_time = time.time() - start_time

# 计算指标
preds = outputs.argmax(1)
accuracy = (preds == label_tensor).float().mean().item()

print(f"\n预测100条文本耗时: {elapsed_time:.4f}秒")
print(f"平均每条耗时: {elapsed_time * 10:.3f}毫秒")
print(f"预测准确率: {accuracy:.4f}")
