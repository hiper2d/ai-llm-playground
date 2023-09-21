# ai-llm-playground
Experiments with Langchain, OpenAI API, Embedding, and Agents

# Projects

### Restaurant Advisor

This chat-bot is aware of restaurant database in MongoDB and is capable of finding the best one nearby. It combines vector semantic search with geo-location MongoDb Atlas Index search. It is quite awesome:
I will add more details of how to setup it and how to configure a free MongoDb Cloud database cluster with search indexes.

![restaurant-advisor.png](images/restaurant-advisor.png)

### AI Girlfriend

A simple chat using Langchain, Streamlit, and OpenAI API. It uses a prompt to add some personality to the ChatGPT and make use it has some memory of the conversation. And it can voice-talk almost like a real human using Elevenlabs API.  
I use [Elevenlabs](https://elevenlabs.io/speech-synthesis) to generate a voice and [FlowGPT](https://flowgpt.com/) to generate prompts

![ai-girlfriend.png](images/ai-girlfriend.png)

### Chat with Multiple Documents

Here I use vector database to store txt documents' content. Langchain with `stuff` chain type allows to query this store and use it in chatting with llm

![multi-doc.png](images/multi-doc.png)

# Setup

### Pipenv setup

I use `pipenv` to manage dependencies. Install it, create a virtual environment, activate it and install dependencies.

1. Install `pipenv` using official [docs](https://pipenv.pypa.io/en/latest/install/#installing-pipenv). For example, on Mac:
    ```bash
    pip install pipenv --user
    ```

2. Add `pipenv` to PATH if it's not there. For example, I had to add to the `~/.zshrc` file the following line:
    ```bash
    export PATH="/Users/hiper2d/Library/Python/3.11/bin:$PATH"
    ```

3. Install packages and create a virtual environment for the project:
    ```bash
    cd <project dir> # navigate to the project dir
    pipenv install
    ```
    This should create a virtual environment and install all dependencies from `Pipfile.lock` file.

    If for any reason you need to create a virtual environment manually, use the following command:
    ```bash
    pip install virtualenv # install virtualenv if you don't have it
    virtualenv --version # check if it's installed
    cd <virtualenv dir> # for example, my virtual envs as here: /Users/hiper2d/.local/share/virtualenvs
    virtualenv <virtualenv name> # I usually use a project name
    ```

4. To swtich to the virtual environment, use the following command:
    ```bash
    cd <project dir>
    pipenv shell
    ```
    If this fails, than do the following:
    ```bash
    cd <virtualenv dir>/bin
    source activate
    ```

### Intellij Idea/PyCharm Run/Debug setup

1. Add a Python Interpreter. Idea will generate a virtual environment for you.
   - Go to Project Settings > SDK > Add SDK > Python SDK > Pipenv Environment
   - Add paths to python and pipenv like this:
     ![add-python-interpreter.png](images/add-python-interpreter.png)

2. Create a Python StreamLit Run/Debug configuration like this:
   ![streamlit-run-debug-config.png](images/streamlit-run-debug-config.png)

3. Create a Python Flask Run/Debug configuration like this:
    ![flask-run-debug-config.png](images/flask-run-debug-config.png)