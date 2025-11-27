 ### <img width="400" height="400" alt="Barbie logo-04 (3)" src="https://github.com/user-attachments/assets/eb3eeac8-8ca5-45bb-9640-608140839196" /> 
 # Stein Search — Hybrid Web & Local Indexed Search

## 📌 Overview

This project is a full-stack intelligent search engine that performs hybrid search across the web and locally indexed documents. It integrates external APIs (Google, SerpAPI, job platforms, marketplaces) with an internal tokenized and ranked document database, delivering fast, relevant and str
uctured results.

The system is designed with scalability, modularity and production readiness, supporting:

- Web UI search
- Job search aggregation
- Marketplace price comparison
- Alerts & notifications
- Real-time monitoring and analytics

## 🎯 Key Features

| Category | Capabilities |
|----------|-------------|
| 🔎 Web Search | Federated search using Google / SerpAPI + custom ranking |
| 📁 Local Search | Full-text search over indexed JSON documents |
| 💼 Job Search | Aggregated job results + alert subscriptions |
| 🛒 Marketplace | Product comparison + price alerts |
| 🧠 NLP Processing | Spell correction, query parsing, keyword extraction, snippet generation |
| ⚡ Speed | In-memory caching + database storage indexing supports fast lookup |
| 📊 Monitoring | Metrics collection for performance & API tracking |
| 🔔 Notifications | Email job alerts / price drop alerts |
| ☁️ API Ready | JSON REST API for frontend or 3rd-party consumers |

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Data Storage | JSON index + analytics store |
| Processing | Custom tokenizer, ranker, filters, NLP pipeline |
| External APIs | Google Search, SerpAPI, Job & Marketplace providers |
| Task Queue (Optional) | Celery |
| Deployment | Docker-ready |

## 📂 Folder Structure

```
Search-Engine/
│
├── README.md
├── main.py
├── setup.py
├── requirements.txt
├── init_db.py
├── index.json
├── celery_app.py
│
├── API_DIAGNOSTIC_REPORT.md
├── API_DOCUMENTATION.md
├── API_RESULTS_LIMIT_FIX.md
├── EXECUTIVE_SUMMARY.md
├── EXTERNAL_API_FIX.md
├── FINAL_STATUS.txt
├── IMPLEMENTATION_COMPLETE.md
├── TEST_RESULTS_FINAL.md
│
├── data/
│   └── (indexed JSON data files)
│
├── logs/
│   └── (generated runtime logs)
│
├── src/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   ├── caching/
│   │   └── cache_manager.py
│   │
│   ├── crawler/
│   │   └── spider.py
│   │
│   ├── external/
│   │   ├── google_search_client.py
│   │   └── serpapi_client.py
│   │
│   ├── indexing/
│   │   ├── __init__.py
│   │   └── indexer.py
│   │
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── job_search_client.py
│   │   └── email_notifications.py
│   │
│   ├── marketplace/
│   │   ├── __init__.py
│   │   ├── marketplace_client.py
│   │   └── price_alerts.py
│   │
│   ├── monitoring/
│   │   └── metrics.py
│   │
│   ├── processing/
│   │   ├── tokenizer.py
│   │   ├── spell_corrector.py
│   │   ├── query_parser.py
│   │   ├── filter_processor.py
│   │   └── snippet_generator.py
│   │
│   ├── ranking/
│   │   ├── __init__.py
│   │   ├── ranker.py
│   │   └── advanced_ranker.py
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   └── search_manager.py
│   │
│   ├── storage/
│   │   ├── analytics_store.py
│   │   ├── database.py
│   │   └── document_store.py
│   │
│   ├── utils/
│   │   └── logger.py
│   │
│   └── web/
│       ├── app.py
│       │
│       ├── static/
│       │   ├── css/
│       │   │   └── (stylesheets)
│       │   │
│       │   ├── images/
│       │   │   └── (image assets)
│       │   │
│       │   └── js/
│       │       ├── api.js
│       │       ├── search.js
│       │       ├── results.js
│       │       ├── jobs.js
│       │       ├── utils.js
│       │       ├── filters.js
│       │       └── autocomplete.js
│       │
│       └── templates/
│           ├── base.html
│           ├── search.html
│           ├── jobs.html
│           ├── marketplace.html
│           └── marketplaces.html
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_api_endpoints.py
    ├── test_crawler.py
    ├── test_indexer_concurrency.py
    ├── test_indexing.py
    ├── test_integration.py
    └── postman_collection.json
```

## 🚀 Running the Project

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Initialize indexing database
```bash
python init_db.py
```

### 3️⃣ Start the engine
```bash
python main.py
```

### 4️⃣ Access UI
Navigate to: `http://127.0.0.1:5000`

## 📌 Contribution Guidelines

- Write modular PRs
- Add / update tests for every feature
- Log API failures via monitoring module
- Document new feature behavior in `/API_DOCUMENTATION.md`

## 📄 License

[Add your license information here]

## 🤝 Support

For issues, questions, or contributions, please open an issue or submit a pull request.
