from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Account:
    """Represents an account in the ledger."""
    name: str
    
    def __str__(self):
        return self.name

@dataclass
class Item:
    """Represents an item in the ledger."""
    id: int
    account: str
    description: str
    price: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Create an Item from a dictionary."""
        return cls(
            id=data['id'],
            account=data['account'],
            description=data['description'],
            price=data['price']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Item to dictionary."""
        return {
            'id': self.id,
            'account': self.account,
            'description': self.description,
            'price': self.price
        }
    
    def formatted_price(self) -> str:
        """Return formatted price string."""
        return f"${self.price:,.2f}"