import sys
import os

# Add the backend directory to sys.path
backend_path = r"c:\Users\Nishanth.KR\New folder\intelli-credit\backend"
if backend_path not in sys.path:
    sys.path.append(backend_path)

print(f"Working Directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")

try:
    import async_models
    print("SUCCESS: async_models imported correctly.")
    from async_models import AsyncBase
    print("SUCCESS: AsyncBase imported from async_models.")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
except Exception as e:
    print(f"FAILURE: An unexpected error occurred: {e}")
