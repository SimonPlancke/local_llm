# config.py
class Config:
    def __init__(self, **kwargs):
        # Add more parameters as needed
        self.rag_working_name = kwargs.get('rag_working_name', 'faiss_aimodel')
        self.text_file_path = kwargs.get('text_file_path', './text_files')

# Global config instance
config = Config()