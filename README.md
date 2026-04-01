---
title: SQL Analyst
emoji: 📊
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# SQL Analyst Agent Environment

## Description
An OpenEnv-compliant environment where AI agents are evaluated on their ability to 
write SQL queries to answer real business questions against a synthetic e-commerce database.

## Motivation
SQL querying often becomes a real-world bottleneck because poorly optimized queries (e.g., missing indexes, inefficient joins, or full table scans) can drastically increase execution time as data scales. Additionally, high concurrency in production systems leads to contention for database resources (CPU, memory, locks), further degrading performance and slowing down overall application responsiveness.

## Action Space
Type: Text (SQL query string)
Format: Valid SQL SELECT statement targeting the provided schema

## Observation Space  
- schema_info: Full DB schema description
- question: Natural language business question to answer
- last_query_result: Result of the previous query (None on first step)
- step: Current step number
- done: Whether episode is complete

## Tasks
| Task | Difficulty | Description | Max Steps |
|------|-----------|-------------|-----------|
| easy_sql | Easy | Single-table aggregation | 5 |
| medium_sql | Medium | Multi-table JOIN with ranking | 8 |
| hard_sql | Hard | CTE + window function analysis | 10 |

## Baseline Scores (Llama-3.1-8B-Instruct)
| Task | Score |
|------|-------|
| easy_sql | 1.000 |
| medium_sql | 0.000 |
| hard_sql | 0.000 |

## Setup
docker build -t sql-analyst-env .
docker run -p 7860:7860 sql-analyst-env

## Usage
PING_URL=http://localhost:7860 MODEL_NAME=gpt-5-nano HF_TOKEN=xxx python inference.py
