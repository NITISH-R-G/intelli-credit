import subprocess
import sys

def main():
    missing = []
    while True:
        result = subprocess.run([sys.executable, "-c", "import main"], capture_output=True, text=True)
        if result.returncode == 0:
            print("SUCCESS! No more missing modules.")
            break
        
        output = result.stderr or result.stdout
        if "ModuleNotFoundError: No module named" in output:
            lines = output.strip().split("\n")
            err_line = [l for l in lines if "ModuleNotFoundError: No module named" in l][-1]
            module_name = err_line.split("'")[1]
            print(f"MISSING: {module_name}")
            missing.append(module_name)
            subprocess.run([sys.executable, "-m", "pip", "install", module_name], check=True)
        else:
            print("OTHER ERROR:")
            print(output)
            break
            
    if missing:
        print("\nSUMMARY OF ALL MISSING MODULES FOUND:")
        for m in missing:
            print(m)

if __name__ == "__main__":
    main()
