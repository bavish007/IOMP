# IOMP - Talk2Shell (Windows Edition)
Talk2Shell is a locally executed system that translates natural language instructions into Windows CMD and PowerShell commands.
It enables users to interact with their system using simple English instead of memorizing command-line syntax, while ensuring safe and controlled execution.

#🚀 Features

 🔄 Natural Language → Windows Command Translation
 🛡️ Safety layer to detect potentially dangerous commands
 🔁 Multi-step command generation
 ⚡ Local command execution on user's machine

# 🏗️ Architecture

                  User Input  
                     ↓  
                Preprocessing  
                     ↓  
               Intent Detection  
                     ↓  
               Command Generation  
                     ↓  
                Safety Check  
                     ↓  
          Execution Engine (PowerShell)  
                     ↓  
                   Output

# 🧩 Tech Stack

- Backend: Python / Node.js
- NLP: Rule-based system / OpenAI API
- Execution: subprocess (Python) / child_process (Node.js)
- Platform: Windows (PowerShell)
  
# 🧠 How It Works

1. User inputs a natural language instruction
2. System processes the input using predefined rules or NLP
3. Generates corresponding PowerShell command(s)
4. Performs safety checks
5. Executes the command locally and returns output



 
