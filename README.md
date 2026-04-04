# 🏦 Intelli-Credit - Intelligent Corporate Underwriting

> An autonomous AI Credit Officer platform designed to automate Tier-1 bank credit committee operations, leveraging Multi-Agent architecture, specialized Financial LLMs, and explainable risk scoring.

Intelli-Credit is an end-to-end B2B credit decisioning engine. It ingests complex financial documents, conducts autonomous due diligence via specialized agents, computes risk scores using machine learning ensembles, and generates professional Credit Appraisal Memos (CAM).

---

## 🏗 Project Architecture

Intelli-Credit is built with a modern, decoupled architecture designed for high performance and scalability.

- **Frontend**: A highly interactive **Next.js 16** (App Router) application built with **React 19** and **Tailwind CSS 4**. It features a "Decision Studio" built on **XYFlow** for visual policy orchestration.
- **Backend**: A high-performance **FastAPI** service powered by **Python 3.11+**, utilizing **Async SQLAlchemy** for non-blocking database operations and **Google Gemini 1.5 Flash** for document intelligence.
- **AI Ecosystem**: Employs a multi-tier AI strategy using **Camel-AI** for multi-agent workflows, **Mem0** for persistent agent memory, and **XGBoost/SHAP** for transparent credit scoring.
- **Data Layer**: Integrates with **Databricks SQL Warehouse** for enterprise-grade data ingestion and **FAISS** for vector search capabilities.

---

## 📂 Project Structure

```bash
intelli-credit/
├── frontend/                # Next.js 16 + React 19 Frontend
│   ├── src/
│   │   ├── app/             # App Router pages and layouts
│   │   ├── components/      # Reusable UI components (Tailwind 4)
│   │   ├── store/           # Zustand state management
│   │   └── hooks/           # Custom React hooks
├── backend/                 # FastAPI + Python Backend
│   ├── modules/             # Core logic: Ingestion, Scoring, Agents
│   ├── routers/             # API endpoints (V2 Async supported)
│   ├── schemas/             # Pydantic data models
│   ├── database/            # SQLAlchemy models and migrations
│   ├── security/            # Firebase Auth integration
│   └── training/            # ML model training scripts
├── docker-compose.yml       # Container orchestration
└── architecture.md          # Technical Deep-Dive
```

---

## 🔥 Key Features

### 1. 🧠 Intelligent Ingestion Engine
Uses **Gemini 1.5 Flash** & **OCR (Tesseract/pdfplumber)** to extract structured financial data from messy, scanned Indian corporate PDFs, including:
- Schedule III Balance Sheets & Profit/Loss statements.
- GST Filings (GSTR-1, 3B) linked to **Databricks**.
- Bank Statements with automated transaction categorization.

### 2. 🎨 Decision Studio (Visual Policy Engine)
A drag-and-drop canvas powered by **XYFlow** that allows risk managers to:
- Build nested credit policies without writing code.
- Trigger external webhooks and data integrations.
- Define dynamic rules using a secure Python AST execution engine.

### 3. 🤖 Multi-Agent Due Diligence
Deploys a swarm of autonomous agents using **Camel-AI** and **Mem0**:
- **Searcher Agent**: Conducts web-scale adverse media and regulatory searches.
- **Analyst Agent**: Synthesizes financial ratios and macro-economic factors.
- **Summarizer Agent**: Authors high-quality narrative commentary for the CAM.

### 4. 📊 Explainable Risk Scoring (SHAP)
Avoids "black box" decisions by providing full transparency:
- **XGBoost Ensembles**: Predicts probability of default with high accuracy.
- **SHAP Interpretability**: Visualizes exactly which factors (e.g., DSCR, Current Ratio) drove the final decision.
- **RAROC Simulation**: Estimates Risk-Adjusted Return on Capital and capital impact.

---

## 🛠 Tech Stack

- **Frontend**: Next.js 16, React 19, Tailwind CSS 4, XYFlow, Zustand, Recharts, Framer Motion.
- **Backend**: FastAPI, SQLAlchemy 2.0, Pydantic, ReportLab, Celery (Optional).
- **AI/ML**: Google Gemini 1.5 Flash, XGBoost, SHAP, Camel-AI, Mem0, FinBERT (Sentiment).
- **Data & Auth**: PostgreSQL/SQLite, Databricks, Firebase Auth (Identity Platform).

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📜 Documentation
For a deeper dive into the system design, check out [architecture.md](file:///d:/Hackathons/intelli-credit/architecture.md).
