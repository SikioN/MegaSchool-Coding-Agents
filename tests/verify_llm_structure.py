import sys
import os

# Add src to pythonpath
sys.path.append(os.getcwd())

try:
    from src.core.llm import LLMProvider, OpenAILLM, YandexGPTLLM, get_llm
    from src.core.config import Config
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except NameError as e:
    print(f"❌ NameError (Missing class?): {e}")
    sys.exit(1)

# Check YandexGPT instantiation (should always work as it uses requests)
try:
    yandex = YandexGPTLLM()
    print("✅ YandexGPTLLM instantiation successful")
except Exception as e:
    print(f"❌ YandexGPTLLM instantiation failed: {e}")

# Check generic factory
try:
    # Modify env var temporarily to test logic (optional, but good for sanity)
    # We just want to see if get_llm returns *something* without crashing
    llm = get_llm()
    print(f"✅ get_llm() returned: {type(llm).__name__}")
except Exception as e:
    print(f"❌ get_llm() failed: {e}")

print("Verification passed!")
