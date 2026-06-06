import os
import ast
import json
import re

def parse_python_imports(file_path):
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
    except Exception:
        pass
    return imports

def parse_js_imports(file_path):
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Match standard ES6 imports
            matches = re.findall(r'import\s+.*?\s+from\s+[\'"](.*?)[\'"]', content)
            imports.extend(matches)
            # Match dynamic imports
            matches_dynamic = re.findall(r'import\([\'"](.*?)[\'"]\)', content)
            imports.extend(matches_dynamic)
            # Match requires
            matches_require = re.findall(r'require\([\'"](.*?)[\'"]\)', content)
            imports.extend(matches_require)
    except Exception:
        pass
    return imports

def build_knowledge_graph(root_dir="."):
    graph = {
        "nodes": [],
        "edges": []
    }

    nodes_set = set()

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('node_modules', 'venv', '__pycache__')]

        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, root_dir)

            if rel_path not in nodes_set:
                graph["nodes"].append({"id": rel_path, "type": "file"})
                nodes_set.add(rel_path)

            imports = []
            if filename.endswith(".py"):
                imports = parse_python_imports(file_path)
            elif filename.endswith((".js", ".jsx", ".ts", ".tsx")):
                imports = parse_js_imports(file_path)

            for imp in imports:
                if imp not in nodes_set:
                    graph["nodes"].append({"id": imp, "type": "module"})
                    nodes_set.add(imp)
                graph["edges"].append({"source": rel_path, "target": imp})

    return graph

def generate_mermaid_graph(graph):
    mermaid = "graph TD\n"
    # Limit to top 100 edges to prevent massive graphs
    edges = graph["edges"][:100]
    for edge in edges:
        source = edge["source"].replace("/", "_").replace(".", "_").replace("-", "_")
        target = edge["target"].replace("/", "_").replace(".", "_").replace("-", "_")
        mermaid += f"    {source}[{edge['source']}] --> {target}[{edge['target']}]\n"
    return mermaid

if __name__ == "__main__":
    kg = build_knowledge_graph()

    os.makedirs("docs", exist_ok=True)
    with open("docs/knowledge_graph.json", "w", encoding="utf-8") as f:
        json.dump(kg, f, indent=2)

    mermaid_graph = generate_mermaid_graph(kg)
    with open("docs/knowledge_graph.md", "w", encoding="utf-8") as f:
        f.write("# Repository Knowledge Graph\n\n```mermaid\n")
        f.write(mermaid_graph)
        f.write("```\n")

    print("Knowledge graph generated in docs/")
