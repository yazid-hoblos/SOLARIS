#!/bin/bash
# Switch to online mode for deployment
export USE_ONLINE=true
export GROQ_API_KEY="${GROQ_API_KEY}"

cd biomera && python api.py
