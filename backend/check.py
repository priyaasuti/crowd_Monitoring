import torch

print("=" * 50)
print("GPU CHECK")
print("=" * 50)

# Check basic availability
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"XPU (Intel) Available: {torch.xpu.is_available()}")

# Set device
device = torch.device("xpu" if torch.xpu.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
print(f"\n✅ Using Device: {device}")

# Test computation on GPU
test_tensor = torch.randn(1000, 1000).to(device)
result = (test_tensor @ test_tensor).sum()

if device.type == "xpu":
    print(f"🎯 INTEL ARC GPU MEMORY: {torch.xpu.memory_allocated() / 1024**2:.2f} MB")
    print("✅ GPU IS WORKING!")
else:
    print("❌ GPU NOT DETECTED - Using CPU")

print("=" * 50)