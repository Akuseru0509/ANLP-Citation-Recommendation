import uvicorn
import dotenv
from pathlib import Path
import os

from scripts.__init__ import app
from scripts.utils.utils import parse_url

BASE_DIR = Path(__file__).parents[0].resolve()
ENV_DIR = BASE_DIR / ".env"

dotenv.load_dotenv(ENV_DIR)

if __name__ == "__main__":
    url = os.getenv("BACKEND_URL")
    port, host = parse_url(url=url)

    uvicorn.run(app, host=host, port=port)