from typing import Dict, Any, List

class DataStore:
    def __init__(self):
        # IN-MEMORY DATA STORES
        self.documents_store: Dict[str, Any] = {}
        self.final_academic_data: List[Dict[str, Any]] = []

    def get_document(self, document_id: str) -> dict | None:
        return self.documents_store.get(document_id)

    def set_document(self, document_id: str, data: dict):
        self.documents_store[document_id] = data

    def update_document(self, document_id: str, updates: dict):
        if document_id in self.documents_store:
            self.documents_store[document_id].update(updates)
            
    def add_final_academic_data(self, data: dict):
        self.final_academic_data.append(data)
        
    def get_all_final_academic_data(self):
        return self.final_academic_data

# Global instance for in-memory storage
store = DataStore()
