# rag-mcp: a ridiculously over-engineered retrieval system

welcome to rag-mcp, a project that answers the age-old question, "what if we took a perfectly good idea—retrieval-augmented generation—and made it so complicated it becomes a monument to our own hubris?" it's a model context protocol (mcp) server that slings text embeddings around like a coked-up short-stop, using postgresql and the `pgvector` extension because, honestly, who needs simplicity?

this is for the real sickos, the ones who look at a problem and think, "i could solve this with a simple script, but what if, instead, i built a byzantine system of interlocking parts that will be a nightmare to maintain?" you're my people.

## what the hell is this thing?

at its core, rag-mcp is a python server that provides a set of tools for searching a knowledge base of text. but instead of just one boring way to search, we've got *modalities*. think of them as different flavors of search, each one a special little snowflake optimized for a specific kind of task.

-   **semantic search**: for when you want to find things that are, like, *vibing* with your query.
-   **question/answer search**: you ask a question, it pretends to have the answer. classic.
-   **style search**: finds stuff that *feels* the same. it's like a sommelier for text. deeply pretentious and surprisingly useful.

it's all built on the `fastmcp` framework, which means you can talk to it with other ai agents, creating a truly absurd, self-referential ouroboros of code.

## architecture, or "how the sausage gets made"

it's a beautiful mess. here's the blueprint:

1.  **the server (`rag_mcp_server.py`)**: a python script that's the brains of the operation. it handles incoming requests, talks to the database, and generally tries to keep its cool.
2.  **the database (`postgresql` + `pgvector`)**: this is where we stash all the text and its corresponding vector embeddings. the `create_tables.pgsql` script lays out the whole schema, which is surprisingly organized for something i came up with. we're talking `documents`, `document_chunks`, and `embeddings` tables, all linked up. it's almost professional.
3.  **the embedding engine (openai-compatible)**: we need something to turn words into numbers. the server calls out to an openai-compatible api to get the embeddings. you get to provide the endpoint, so you can use whatever weird, home-brewed model you want.
4.  **the tools**: the server exposes its search modalities as mcp tools. right now, we've got `search_semantic_similarity`, `search_qa`, and `search_style`.

## setup, or "good luck"

getting this beast to run is a rite of passage.

**prerequisites:**
*   python 3.whatever. if it works, it works.
*   postgresql, with the `pgvector` extension enabled. if you don't know how to do that, google it. this isn't a charity.

**installation:**

1.  clone the repo. obviously.
2.  install the python junk:
    ```sh
    pip install -r requirements.txt
    ```
3.  set up the database. connect to your postgres instance and run the `create_tables.pgsql` script. it'll create the tables and the fancy hnsw indexes for fast, fast, fast vector searches.
4.  environment variables. you need to set these. create a `.env` file or just scream them into the void, your choice.

    ```
    # database stuff
    rm_db_host=localhost
    rm_db_port=5432
    rm_db_name=your_db_name
    rm_db_user=your_db_user
    rm_db_password=your_super_secret_password

    # embedding model stuff
    rm_openai_api_key=your_api_key
    rm_openai_endpoint=your_model_endpoint_url
    ```

## usage, or "let's dance"

if you've made it this far, you're either a genius or you're very, very lost. either way, let's fire it up.

1.  run the server:
    ```sh
    python rag_mcp_server.py
    ```
2.  if it doesn't immediately crash and burn, the server is now listening, exposing its mcp tools to the world. you can now call `search_style`, `search_qa`, and `search_semantic_similarity` from whatever mcp client you've got.

## connecting from clients, or "who's gonna talk to this thing?"

so you've got this glorious monstrosity running. now what? you need something to talk to it. if you're using some ai assistant thingy in vscode or claude desktop or whatever the hell, you'll need to tell it how to find our server.

you'll probably have to edit some json settings file. find the spot for `mcpServers` and add something like this:

```json
{
  "mcpServers": {
    "RAG-MCP Knoledge Base Server": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "/location/of/the/script/rag_mcp_server.py:mcp"
      ],
      "env": {
        "RM_DB_HOST": "localhost",
        "RM_DB_PORT": "5432",
        "RM_DB_NAME": "your_db_name",
        "RM_DB_USER": "your_db_user",
        "RM_DB_PASSWORD": "your_super_secret_password",
        "RM_OPENAI_API_KEY": "your_api_key",
        "RM_OPENAI_ENDPOINT": "your_model_endpoint_url"
      },
      "transport": "stdio",
      "type": null,
      "cwd": null,
      "timeout": null,
      "description": null,
      "icon": null,
      "authentication": null
    }
  }
}
```

obviously, change `/location/of/the/script/rag_mcp_server.py:mcp` to the actual, you know, location of the script. and fill in the `env` with your secrets. don't just copy-paste this like a mindless drone. or do. i'm not your dad.

## extending the system, or "make it weirder"

the best part of this whole thing is how easy it is to make it even more baroque. you can add your own search modalities. maybe you want a search that only returns results in iambic pentameter. maybe you want one that searches for recipes for disaster. go nuts.

i wrote a whole damn manual for it. check out `manual.md`. it'll walk you through the process of adding new models, tasks, and tool functions. it's so easy, it's almost disappointing.

---

*this project is provided as-is, without any warranty, express or implied. if it sets your computer on fire, that's on you. you chose this life.*
