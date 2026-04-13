import dotenv
import os

class aGraeConfig():
    def __init__(self) -> None:
        env_path = os.path.join(os.path.dirname(__file__), '.env.local')

        if os.path.exists(env_path):
            dotenv.load_dotenv(env_path, override=True)

        self.local: bool = str(os.getenv('LOCAL')).strip().lower() in ['true', '1', 'yes']
        self.backend_url:str = os.getenv('backend_url_dev') if self.local else 'http://142.93.41.109:8000'
        self.gee_backend_url:str = os.getenv('backend_gee_url_dev') if self.local else 'http://142.93.41.109:8500'

        # print(f"Configuration loaded: local={self.local}, backend_url={self.backend_url}, gee_backend_url={self.gee_backend_url}")

