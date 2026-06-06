import os
import json
import re

def analyze_repo(root_dir="."):
    repo_state = {
        "frameworks": [],
        "libraries": [],
        "env_vars": [],
        "directories": [],
        "services": []
    }

    env_vars_set = set()

    # Analyze package.json
    package_json_paths = []
    requirements_paths = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # skip hidden dirs and node_modules/venv
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('node_modules', 'venv', '__pycache__')]

        rel_path = os.path.relpath(dirpath, root_dir)
        if rel_path != ".":
            repo_state["directories"].append(rel_path)

        for filename in filenames:
            file_path = os.path.join(dirpath, filename)

            if filename == "package.json":
                package_json_paths.append(file_path)
            elif filename == "requirements.txt":
                requirements_paths.append(file_path)
            elif filename.endswith(".env") or filename.endswith(".env.example"):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            var_name = line.split("=")[0].strip()
                            env_vars_set.add(var_name)

            # Look for process.env or os.environ usage
            if filename.endswith(".js") or filename.endswith(".ts") or filename.endswith(".jsx") or filename.endswith(".tsx"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = re.findall(r'process\.env\.([A-Z0-9_]+)', content)
                        for match in matches:
                            env_vars_set.add(match)
                except Exception:
                    pass
            elif filename.endswith(".py"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = re.findall(r'os\.environ\.get\([\'"]([A-Z0-9_]+)[\'"]\)', content)
                        matches += re.findall(r'os\.getenv\([\'"]([A-Z0-9_]+)[\'"]\)', content)
                        for match in matches:
                            env_vars_set.add(match)
                except Exception:
                    pass

    for pkg_json_path in package_json_paths:
        try:
            with open(pkg_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
                repo_state["libraries"].extend(deps)
                if "next" in deps:
                    repo_state["frameworks"].append("Next.js")
                if "react" in deps:
                    repo_state["frameworks"].append("React")
        except Exception:
            pass

    for req_path in requirements_paths:
        try:
            with open(req_path, "r", encoding="utf-8") as f:
                content = f.read()
                deps = [line.split("==")[0].strip() for line in content.split("\n") if line.strip() and not line.startswith("#")]
                repo_state["libraries"].extend(deps)
                if "fastapi" in deps:
                    repo_state["frameworks"].append("FastAPI")
        except Exception:
            pass

    repo_state["frameworks"] = list(set(repo_state["frameworks"]))
    repo_state["libraries"] = list(set(repo_state["libraries"]))
    repo_state["env_vars"] = list(env_vars_set)
    repo_state["directories"] = list(set(repo_state["directories"]))

    return repo_state

if __name__ == "__main__":
    state = analyze_repo()
    with open("repo_state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print("Repository analysis complete. output saved to repo_state.json")
