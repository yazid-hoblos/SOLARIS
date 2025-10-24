# SOLARIS Bioinformatics Chatbot

Deploy this chatbot to analyze metabolic pathways in cyanobacteria.

## Local Development
```bash
# Use local Ollama model
export GROQ_API_KEY=your_key_here  # Optional for local
cd biomera
python api.py
```

## Online Deployment (Render.com)
1. Get Groq API key from https://console.groq.com/keys
2. Push to GitHub
3. Connect to Render.com
4. Set GROQ_API_KEY environment variable
5. Deploy automatically

## Features
- Real-time streaming responses
- Automatic error recovery
- Progress indicators
- Command execution in sandboxed workspace
