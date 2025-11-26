Search Engine — Hybrid Web & Local Indexed Search
📌 Overview

This project is a full-stack intelligent search engine that performs hybrid search across the web and locally indexed documents.
It integrates external APIs (Google, SerpAPI, job platforms, marketplaces) with an internal tokenized and ranked document database, delivering fast, relevant and structured results.

The system is designed with scalability, modularity and production readiness, supporting:

Web UI search

Job search aggregation

Marketplace price comparison

Alerts & notifications

Real-time monitoring and analytics

🎯 Key Features
Category	Capabilities
🔎 Web Search	Federated search using Google / SerpAPI + custom ranking
📁 Local Search	Full-text search over indexed JSON documents
💼 Job Search	Aggregated job results + alert subscriptions
🛒 Marketplace	Product comparison + price alerts
🧠 NLP Processing	Spell correction, query parsing, keyword extraction, snippet generation
⚡ Speed	In-memory caching + database storage indexing supports fast lookup
📊 Monitoring	Metrics collection for performance & API tracking
🔔 Notifications	Email job alerts / price drop alerts
☁ API Ready	JSON REST API for frontend or 3rd-party consumers
🧱 Tech Stack
Layer	Technology
Backend	Python, Flask
Frontend	HTML, CSS, JavaScript
Data Storage	JSON index + analytics store
Processing	Custom tokenizer, ranker, filters, NLP pipeline
External APIs	Google Search, SerpAPI, Job & Marketplace providers
Task Queue (Optional)	Celery
Deployment	Docker-ready
📂 Folder Structure
Search-Engine/
│  API_DIAGNOSTIC_REPORT.md
│  API_DOCUMENTATION.md
│  API_RESULTS_LIMIT_FIX.md
│  EXECUTIVE_SUMMARY.md
│  EXTERNAL_API_FIX.md
│  FINAL_STATUS.txt
│  IMPLEMENTATION_COMPLETE.md
│  TEST_RESULTS_FINAL.md
│  README.md
│  main.py
│  setup.py
│  requirements.txt
│  init_db.py
│  index.json
│  celery_app.py
│
├─ data/
│   └─ (indexed JSON data files)
│
├─ logs/
│   └─ (generated runtime logs)
│
├─ src/
│  ├─ config/
│  │   ├─ config.py
│  │   └─ __init__.py
│  ├─ caching/
│  │   └─ cache_manager.py
│  ├─ crawler/
│  │   └─ spider.py
│  ├─ external/
│  │   ├─ google_search_client.py
│  │   └─ serpapi_client.py
│  ├─ indexing/
│  │   ├─ indexer.py
│  │   └─ __init__.py
│  ├─ jobs/
│  │   ├─ job_search_client.py
│  │   ├─ email_notifications.py
│  │   └─ __init__.py
│  ├─ marketplace/
│  │   ├─ marketplace_client.py
│  │   ├─ price_alerts.py
│  │   └─ __init__.py
│  ├─ monitoring/
│  │   └─ metrics.py
│  ├─ processing/
│  │   ├─ tokenizer.py
│  │   ├─ spell_corrector.py
│  │   ├─ query_parser.py
│  │   ├─ filter_processor.py
│  │   └─ snippet_generator.py
│  ├─ ranking/
│  │   ├─ ranker.py
│  │   ├─ advanced_ranker.py
│  │   └─ __init__.py
│  ├─ search/
│  │   ├─ search_manager.py
│  │   └─ __init__.py
│  ├─ storage/
│  │   ├─ analytics_store.py
│  │   ├─ database.py
│  │   └─ document_store.py
│  ├─ utils/
│  │   └─ logger.py
│  ├─ web/
│  │   ├─ app.py
│  │   ├─ static/
│  │   │   ├─ css/
│  │   │   ├─ images/
│  │   │   └─ js/
│  │   │       ├─ api.js
│  │   │       ├─ search.js
│  │   │       ├─ results.js
│  │   │       ├─ jobs.js
│  │   │       ├─ utils.js
│  │   │       ├─ filters.js
│  │   │       └─ autocomplete.js
│  │   └─ templates/
│  │       ├─ base.html
│  │       ├─ search.html
│  │       ├─ jobs.html
│  │       ├─ marketplace.html
│  │       └─ marketplaces.html
│  └─ __init__.py
│
└─ tests/
   ├─ test_api_endpoints.py
   ├─ test_crawler.py
   ├─ test_indexer_concurrency.py
   ├─ test_indexing.py
   ├─ test_integration.py
   ├─ postman_collection.json
   ├─ conftest.py
   └─ __init__.py

🚀 Running the Project
1️⃣ Install dependencies
pip install -r requirements.txt

2️⃣ Initialize indexing database
python init_db.py

3️⃣ Start the engine
python main.py

4️⃣ Access UI
http://127.0.0.1:5000

📌 Contribution Guidelines

Write modular PRs

Add / update tests for every feature

Log API failures via monitoring module

Document new feature behavior in /API_DOCUMENTATION.md