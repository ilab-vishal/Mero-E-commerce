from abc import ABC, abstractmethod

class CatalogBase(ABC):
    def __init__(self,client_id:str):
        self._client_id = client_id

    @abstractmethod
    def list_products(self):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def get_product(self, product_id: int):
        raise NotImplementedError("Subclasses must implement this method")