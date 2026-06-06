# Dependencies Diagram

```mermaid
graph LR
    UI --> React
    API --> FastAPI
    ML[Machine Learning] --> scikit-learn
    API --> ML
    AI[AI/LLM Integration] --> LangChain
    API --> AI
```
