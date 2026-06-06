import json
import os

def generate_architecture_diagram(repo_state):
    mermaid = "graph TD\n"

    # Frontend nodes
    if "React" in repo_state["frameworks"] or "Next.js" in repo_state["frameworks"]:
        mermaid += "    subgraph Frontend\n"
        mermaid += "        UI[User Interface - Next.js/React]\n"
        mermaid += "    end\n"

    # Backend nodes
    if "FastAPI" in repo_state["frameworks"]:
        mermaid += "    subgraph Backend\n"
        mermaid += "        API[FastAPI Service]\n"
        mermaid += "        Auth[Authentication Middleware]\n"
        mermaid += "        Routes[API Routers]\n"
        mermaid += "        Modules[Core Modules]\n"
        mermaid += "    end\n"
        mermaid += "    UI -->|HTTP Requests| API\n"
        mermaid += "    API --> Auth\n"
        mermaid += "    Auth --> Routes\n"
        mermaid += "    Routes --> Modules\n"

    # Database
    mermaid += "    subgraph Data\n"
    mermaid += "        DB[(PostgreSQL / Vector DB)]\n"
    mermaid += "    end\n"
    mermaid += "    Modules -->|Reads/Writes| DB\n"

    # External APIs
    env_vars = repo_state.get("env_vars", [])
    if any("FIREBASE" in env for env in env_vars):
        mermaid += "    UI -->|Auth| Firebase((Firebase))\n"
    if any("API_KEY" in env or "URL" in env for env in env_vars):
        mermaid += "    subgraph ExternalServices\n"
        mermaid += "        LLM[LLM/GenAI Models]\n"
        mermaid += "        ExtAPI[External Data Providers]\n"
        mermaid += "    end\n"
        mermaid += "    Modules -->|API calls| LLM\n"
        mermaid += "    Modules -->|API calls| ExtAPI\n"

    return mermaid

def generate_dependencies_diagram(repo_state):
    mermaid = "graph LR\n"
    libs = repo_state.get("libraries", [])
    if "react" in libs or "next" in libs:
        mermaid += "    UI --> React\n"
    if "fastapi" in libs:
        mermaid += "    API --> FastAPI\n"
    if "scikit-learn" in libs or "xgboost" in libs:
        mermaid += "    ML[Machine Learning] --> scikit-learn\n"
        mermaid += "    API --> ML\n"
    if "langchain" in libs or "langchain>=0.2.0" in libs or "openai" in libs:
        mermaid += "    AI[AI/LLM Integration] --> LangChain\n"
        mermaid += "    API --> AI\n"
    return mermaid

if __name__ == "__main__":
    if not os.path.exists("repo_state.json"):
        print("repo_state.json not found.")
        exit(1)

    with open("repo_state.json", "r") as f:
        state = json.load(f)

    arch_diagram = generate_architecture_diagram(state)
    deps_diagram = generate_dependencies_diagram(state)

    os.makedirs("docs", exist_ok=True)
    with open("docs/architecture_diagram.md", "w") as f:
        f.write("# Architecture Diagram\n\n```mermaid\n")
        f.write(arch_diagram)
        f.write("```\n")

    with open("docs/dependencies_diagram.md", "w") as f:
        f.write("# Dependencies Diagram\n\n```mermaid\n")
        f.write(deps_diagram)
        f.write("```\n")

    print("Diagrams generated in docs/")
