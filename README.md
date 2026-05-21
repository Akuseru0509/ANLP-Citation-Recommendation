# CiteSense - Citation Recommendation System

Welcome to CiteSense, a citation recommendation platform! This repository contains the code for downloading data, preprocessing it, setting up the necessary databases, and running the backend/frontend services for inference.

## Project Structure

- `src/dao/`: Data Access Objects and scripts to download, preprocess, and create dataset contexts.
- `src/backend/`: FastAPI backend and Chroma vector database setup for handling recommendation logic.
- `src/frontend/`: Streamlit web interface for users to enter queries and view recommendations.
- `data/`: The directory where datasets and outputs are stored.

## Setup Instructions

### 1. Environment Setup

First, make sure you have:

- Python 3.10 or later installed.
- An active Kaggle Credential to download the dataset.
- SemanticScholar API key.
- Groq API key.

Then create a virtual environment before installing the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. Data Preparation

#### Step 1: Download the Data

Download the arXiv metadata dataset using the provided script. It will fetch the dataset using kagglehub and store it in the `data/` directory.

```bash
python src/dao/download.py
```

#### Step 2: Preprocess the Data

Process the downloaded metadata, split it into train/test datasets, generate `papers.json`, and populate the local Chroma Vector Database with paper titles and abstracts.

```bash
python src/dao/data_preprocess.py
```

#### Step 3: Create Citation Contexts

Generate citation contexts by mapping arXiv IDs to Semantic Scholar IDs and fetching the context of citations.

**Note:** You must have an active `API_KEY` from Semantic Scholar. Create a `.env` file with `API_KEY=your_semantic_scholar_api_key` in the root directory or configure it properly before running this script.

```bash
python src/dao/context_creator.py
```

### 3. Model Training and Testing (Optional)

This part requires the a based SciBERT model from Hugging Face and the download.py, data_preprocess.py, and context_creator.py to have been run first. It will produce the papers' database, the contexts' database and the train/test dataset.

If you want to train the ranking model from scratch or evaluate its performance:

#### Train the Model

You can configure the training hyperparameters in `src/backend/model/configs/train_config.yaml`. To start training:

```bash
python src/backend/model/scripts/train.py
```

#### Test the Model

You can configure the testing parameters in `src/backend/model/configs/test_config.yaml`. To run the evaluation:

```bash
python src/backend/model/scripts/test.py
```

### 4. Running the Service

You will need two terminal windows to run the Backend and the Frontend concurrently.

#### Start the Backend

The backend is a FastAPI server. Ensure you have configured the `BACKEND_URL` properly (e.g., in `src/backend/scripts/.env`).

Run the backend from the root directory:

```bash
uvicorn src.backend.scripts.entry:app --reload
```

#### Start the Frontend

The frontend uses Streamlit to provide a sleek, modern UI. Ensure your Streamlit configuration has access to the backend (e.g., `BACKEND_URL` defined in `.streamlit/secrets.toml` or environment variables).

In a new terminal window, run:

```bash
python -m streamlit run src.frontend.app
```

### 5. Inference

Once both the backend and frontend are running, open the Streamlit URL provided in the terminal (usually `http://localhost:8501`).
Enter your abstract or research topic in the **Query** field, adjust the **Year Range**, and hit **Search** to discover relevant papers!

## External Links

During the process of making this system, we utilize *Kaggle's* GPUs. The links are available as followed:

- [create_context](https://www.kaggle.com/code/akuseru0001/scibert-training-dataset-prep)
- [train](https://www.kaggle.com/code/akuseru0001/scibert-train)
- [test](https://www.kaggle.com/code/akuseru0001/scibert-test)
