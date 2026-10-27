#!/bin/bash
# Скрипт быстрого запуска Pharma Sentinel
cd "$(dirname "$0")"
source .venv/bin/activate
export HOME="$(pwd)"
streamlit run app.py
