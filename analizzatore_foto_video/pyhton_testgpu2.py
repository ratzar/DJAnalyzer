import torch
import time

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"🚀 Device in uso: {torch.cuda.get_device_name(0) if device=='cuda' else 'CPU'}")

# Test velocità matrice grande (GPU vs CPU)
size = 10000
x = torch.randn(size, size, device=device)
y = torch.randn(size, size, device=device)

start_time = time.time()
z = torch.matmul(x, y)
gpu_time = time.time() - start_time

print(f"⏱️ Tempo moltiplicazione matriciale {size}x{size}: {gpu_time:.4f} secondi")