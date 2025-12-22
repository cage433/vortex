from abc import ABC, abstractmethod
from typing import Union

from vortex.banking.category.payee_categories import PayeeCategory
from vortex.utils import checked_type, checked_list_type


class AbstractCategoryTree(ABC):
    def __init__(self, name: str):
        self.name: str = checked_type(name, str)

    @abstractmethod
    def includes(self, category: PayeeCategory) -> bool:
        pass

class CategoryLeaves(AbstractCategoryTree):
    def __init__(self, name: str, categories: list[PayeeCategory]):
        super().__init__(name)
        self.categories: list[PayeeCategory] = checked_list_type(categories, PayeeCategory)

    def includes(self, category: PayeeCategory) -> bool:
        return category in self.categories

class CategoryTree(AbstractCategoryTree):
    def __init__(self, name: str, categories: list[AbstractCategoryTree]):
        super().__init__(name)
        self.categories: list[AbstractCategoryTree] = checked_list_type(categories, AbstractCategoryTree)

    def includes(self, category: PayeeCategory) -> bool:
        return any(b.includes(category) for b in self.categories)

