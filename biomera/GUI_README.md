# 🧬 SOLARIS Chatbot GUI

Beautiful web interface for interacting with SOLARIS bioinformatics toolkit.

## 🚀 Quick Start

```bash
cd biomera
chmod +x start_gui.sh
./start_gui.sh
```

Then open your browser to: **http://localhost:5000**

## ✨ Features

- 💬 **Natural language interface** - Ask questions in plain English
- 🎨 **Beautiful UI** - Modern, gradient design with smooth animations
- 📝 **Example prompts** - Quick-start chips for common tasks
- 💻 **Command execution** - See real-time SOLARIS command output
- ⚡ **Fast responses** - Powered by local Mistral LLM via Ollama

## 📸 Screenshots

The interface includes:
- Clean chat bubbles for conversations
- Command output in terminal-style display
- Example question chips for quick starts
- Typing indicators
- Smooth animations

## 🎯 Example Questions

Try clicking the example chips or type:

- "extract EC numbers for 3HP pathway"
- "check my files"  
- "what can compatibility_predictor do?"
- "help with pangenomic analysis"
- "compare strains for best host"
- "find organisms for my pathway"

## 🛠️ Configuration

The GUI uses the same configuration as the CLI:
- **Config**: `config/config.json`
- **Prompts**: `config/prompt_solaris.txt` 
- **Tools**: `config/tools_solaris.json`

## 🔧 Requirements

- Python 3.8+
- Flask (already in requirements.txt)
- Ollama with mistral model: `ollama pull mistral`
- SOLARIS installed

## 🌐 API Endpoints

The GUI uses these endpoints:
- `GET /` - Serves the chat interface
- `POST /ask` - Send messages to the chatbot
- `POST /reset` - Reset the conversation

## 🐛 Troubleshooting

**Can't connect to http://localhost:5000:**
```bash
# Check if port 5000 is already in use
lsof -i :5000

# Try a different port
export FLASK_RUN_PORT=5001
python3 api.py
```

**Chatbot not responding:**
```bash
# Make sure Ollama is running
ollama list

# Check the Flask logs in terminal
```

**Styling looks broken:**
- Clear browser cache (Ctrl+Shift+R)
- Check browser console for errors (F12)

## 💡 Tips

1. **Long responses**: The chat auto-scrolls to the latest message
2. **Command outputs**: Shown in terminal-style black boxes
3. **Multiple commands**: Bot can execute multiple commands in sequence
4. **File paths**: Bot checks actual files before running commands

## 🔄 Development Mode

For hot-reload during development:
```bash
export FLASK_ENV=development
python3 api.py
```

---

Enjoy using SOLARIS Chatbot! 🚀
