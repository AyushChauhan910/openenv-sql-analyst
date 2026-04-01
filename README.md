# SQL Analyst Agent Environment

## Description
An OpenEnv-compliant environment where AI agents are evaluated on their ability to 
write SQL queries to answer real business questions against a synthetic e-commerce database.

## Motivation
[2 sentences on why SQL querying is a real-world bottleneck]

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

## Baseline Scores (GPT-5 Nano)
| Task | Score |
|------|-------|
| easy_sql | [fill after testing] |
| medium_sql | [fill after testing] |
| hard_sql | [fill after testing] |

## Setup
docker build -t sql-analyst-env .
docker run -p 7860:7860 sql-analyst-env

## Usage
PING_URL=http://localhost:7860 MODEL_NAME=gpt-5-nano HF_TOKEN=xxx python inference.py
