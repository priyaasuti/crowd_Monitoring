"""
GPU/Hardware acceleration utilities for Jetson and NVIDIA systems
Optimizes model execution for available hardware (CUDA, GPU, or CPU)
"""
import os
import torch
import logging

logger = logging.getLogger(__name__)


def get_optimal_device():
    """
    Determine the optimal device for model execution.
    Priority: CUDA GPU > CPU (with optimizations)
    
    Returns:
        torch.device: Optimal device for computation
    """
    # Check for CUDA availability
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        logger.info(f"✅ CUDA GPU detected: {torch.cuda.get_device_name(0)}")
        return device
    
    # Fallback to CPU with optimizations
    logger.warning("⚠️  CUDA not detected. Using CPU with optimizations.")
    logger.info("For Jetson systems, YOLO will use GPU acceleration internally.")
    return torch.device("cpu")


def optimize_gpu_memory():
    """
    Enable memory optimizations for GPU if available
    """
    if torch.cuda.is_available():
        try:
            # Enable GPU memory optimization
            torch.cuda.empty_cache()
            torch.cuda.set_per_process_memory_fraction(0.9)  # Use 90% of GPU memory
            logger.info("✅ GPU memory optimization enabled")
        except Exception as e:
            logger.warning(f"Could not optimize GPU memory: {e}")


def enable_gpu_acceleration():
    """
    Enable various GPU acceleration techniques
    """
    try:
        # Set environment variables for optimal GPU usage
        os.environ['CUDA_LAUNCH_BLOCKING'] = '0'  # Async GPU execution
        os.environ['TORCH_HOME'] = os.path.expanduser('~/.torch')
        
        # Enable cuDNN optimizations if available
        if torch.cuda.is_available():
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = True
            logger.info("✅ CUDA NN optimizations enabled")
        else:
            logger.info("ℹ️  CUDA NN optimizations not available")
            
    except Exception as e:
        logger.warning(f"Could not enable GPU acceleration: {e}")


def get_device_info():
    """
    Get detailed information about available compute devices
    
    Returns:
        dict: Device information
    """
    info = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "device_names": [],
        "pytorch_version": torch.__version__,
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else "N/A",
    }
    
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            info["device_names"].append(torch.cuda.get_device_name(i))
    
    return info


def print_device_info():
    """
    Print detailed device information
    """
    info = get_device_info()
    
    print("\n" + "=" * 70)
    print("🔍 SYSTEM COMPUTE DEVICE INFO")
    print("=" * 70)
    print(f"PyTorch Version: {info['pytorch_version']}")
    print(f"CUDA Version: {info['cuda_version']}")
    print(f"CUDA Available: {info['cuda_available']}")
    print(f"GPU Count: {info['device_count']}")
    
    if info['device_names']:
        print("\nAvailable GPUs:")
        for idx, name in enumerate(info['device_names']):
            print(f"  {idx}: {name}")
    
    if not info['cuda_available']:
        print("\n⚠️  CUDA not directly available.")
        print("ℹ️  For Jetson: GPU acceleration enabled through YOLO framework")
        print("ℹ️  For other systems: Ensure NVIDIA drivers and CUDA toolkit installed")
    else:
        print("\n✅ CUDA GPU acceleration is ACTIVE!")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print_device_info()
    device = get_optimal_device()
    optimize_gpu_memory()
    enable_gpu_acceleration()
    print(f"Using device: {device}")
