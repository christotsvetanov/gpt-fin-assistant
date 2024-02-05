# gpt-fin-assistant
An OpenAI assistant leverages Metatrader5 to access real-time market quotes and conduct financial analysis based on the current financial situation.

# What is this?
This is an [openai assistant](https://platform.openai.com/docs/assistants/overview), which is currently (beginning of 2023) the newest way to create a tailored generative AI with access to the outside world.

On default ChatGPT exists in a bubble and all its answers are using data from the past.

OpenAI Assistent API offer 3 ways (named tools) to solve this issue:
- Code Interpreter
- Knowledge Retrieval
- Function calling

From them only the Function calling can allow using of APIs ouside the sandbox..

## The goal
The goal is to create an assistant with access to live market data and performing market analisys. The easiest way to achieve this is to use [Metatrader5](https://www.metatrader5.com/) [Python API](https://www.mql5.com/en/docs/python_metatrader5)

# Prerequisites
1. Windows OS. Metatrader works only on Windows
2. Installed Metatrader. During the installation, a demo account to some broker will be created. You may use either this demo account or create another one, even a real one.
3. Python 3 installed
4. Obtained [OpenAI API key](https://platform.openai.com/api-keys)

# Installation
1. [Setup the developer environment](https://platform.openai.com/docs/quickstart?context=python)
2. Clone the repository:
```
git clone git@github.com:christotsvetanov/gpt-fin-assistant.git
cd gpt-fin-assistant
```
3. Create and activate virtual environment:
```
python -m venv venv
venv\Scripts\activate.bat
```
4. Install the required dependencies:
```
pip install -r requirements.txt
```
5. Run the assistant:
```
python .\gpt-fin-assistant.py
```
You may stop the assistant by pressing Ctrl+C.

# Notes
1. At beginning the script will look for `config.ini` file with assistant id
2. If there is such an id - this assistant will be used.
3. If not - a new one will be created and then used.
4. In current implementation the thread is deleted after Ctrl-C. Comment the last code line to prevent this.
5. As usual - if you are not happy with the assistant answers just ask clarifying questions.