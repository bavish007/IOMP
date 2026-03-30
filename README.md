# IOMP - Talk2Shell (Windows Edition)
Talk2Shell is a locally executed system that translates natural language instructions into Windows CMD and PowerShell commands.
It enables users to interact with their system using simple English instead of memorizing command-line syntax, while ensuring safe and controlled execution.



# 🎯 Objectives

- Eliminate the need to memorize PowerShell commands
- Provide a natural language interface for system interaction
- Ensure safe execution of commands on the local machine
- Support multi-step task automation

  
#🚀 Features

 🔄 Natural Language → Windows Command Translation
 🛡️ Safety layer to detect potentially dangerous commands
 🔁 Multi-step command generation
 ⚡ Local command execution on user's machine

 # 🧠 System Workflow

1. User inputs a natural language instruction
2. Input is preprocessed (lowercase, cleaned)
3. Intent and entities are extracted
4. PowerShell command(s) are generated
5. Safety checks are applied
6. Command is executed locally
7. Output is displayed
 

# 🏗️ System Architecture

Modules:

1. Input Handler
-Accept user input (CLI or UI)
- Pass input to preprocessing module

  
2. Preprocessor
 Responsibilities:
- Convert text to lowercase
- Remove extra spaces
- Normalize keywords

 Example:
 "Create A Folder Named Test"
 → "create a folder named test"

3. Translator (NL → PowerShell)
 Responsibilities:
 - Convert natural language → PowerShell command

Approach:
1. Rule-based (initial)
2. NLP/LLM (optional upgrade)

Example mappings:

"create folder X"
→ New-Item -ItemType Directory -Name X

"delete all txt files"
→ Remove-Item *.txt

"list processes"
→ Get-Process

4. Safety Checker
Responsibilities:
- Detect dangerous commands

Examples:
- Remove-Item with -Recurse
- System-critical paths

Actions:
- Block OR ask confirmation

Example:
⚠️ This command may delete multiple files. Continue? (Y/N)

 5.Command Executor
 Responsibilities:
 - Execute PowerShell commands locally

Python Example:
import subprocess
subprocess.run(["powershell", "-Command", command])


6. Output Handler
Responsibilities:
- Capture output
- Display result to user
- Handle errors gracefully


# 🧩 Tech Stack

- Backend: Python / Node.js
- NLP: Rule-based system / OpenAI API
- Execution: subprocess (Python) / child_process (Node.js)
- Platform: Windows (PowerShell)


# 📂 Project Structure

Talk2Shell/
│── backend/
│   ├── translator.py
│   ├── executor.py
│   ├── safety.py
│── main.py
│── requirements.txt
│── README.md

## ⚙️ Installation

1. Clone the repository:
   git clone https://github.com/your-username/Talk2Shell.git

2. Navigate to the project:
   cd Talk2Shell

3. Install dependencies:
   pip install -r requirements.txt

4. Run the application:
   python main.py

# ▶️ Usage

Input:
"create a folder named test"

Output:
New-Item -ItemType Directory -Name test


# 💡 Example Use Cases

1. File Management
Input: "delete all txt files"
Output: Remove-Item *.txt

2. Process Management
Input: "show running processes"
Output: Get-Process

3. Multi-step Task
Input: "create folder and move files"
Output:
New-Item -ItemType Directory -Name myFolder
Move-Item *.txt myFolder

#🛡️ Safety Considerations

- Prevent execution of destructive commands
- Require confirmation for risky operations
- Avoid system-critical directories

  # 🧪 Limitations

- Limited understanding of complex sentences
- Rule-based system may not generalize well
- Requires improvement for real-world robustness

  
  
# 🧠 How It Works

1. User inputs a natural language instruction
2. System processes the input using predefined rules or NLP
3. Generates corresponding PowerShell command(s)
4. Performs safety checks
5. Executes the command locally and returns output


# 📊 Future Scope

- Add NLP model for better understanding
- Voice input support
- Command explanation feature
- GUI interface
- Context-aware execution



 
