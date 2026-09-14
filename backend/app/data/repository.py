import json
import os
from typing import Dict, List, Optional
from backend.app.models.customer import Customer
from backend.app.models.merchant import Merchant
from backend.app.models.transaction import Transaction
from backend.app.models.evidence import Evidence

# Determine paths relative to root or data directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data'))

class Repository:
    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.merchants: Dict[str, Merchant] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.evidence_store: Dict[str, List[Evidence]] = {}
        self.load_data()

    def load_data(self):
        # Load customers
        cust_path = os.path.join(DATA_DIR, 'customers', 'customers.json')
        if os.path.exists(cust_path):
            with open(cust_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    self.customers[item['customer_id']] = Customer(**item)
        
        # Load merchants
        merch_path = os.path.join(DATA_DIR, 'merchants', 'merchants.json')
        if os.path.exists(merch_path):
            with open(merch_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    self.merchants[item['merchant_id']] = Merchant(**item)

        # Load transactions
        tx_path = os.path.join(DATA_DIR, 'transactions', 'transactions.json')
        if os.path.exists(tx_path):
            with open(tx_path, 'r', encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    self.transactions[item['transaction_id']] = Transaction(**item)

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self.customers.get(customer_id)

    def get_merchant(self, merchant_id: str) -> Optional[Merchant]:
        return self.merchants.get(merchant_id)

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        return self.transactions.get(transaction_id)

    def add_transaction(self, tx: Transaction):
        self.transactions[tx.transaction_id] = tx

    def get_evidence_for_transaction(self, transaction_id: str) -> List[Evidence]:
        return self.evidence_store.get(transaction_id, [])

    def set_evidence_for_transaction(self, transaction_id: str, evidence_list: List[Evidence]):
        self.evidence_store[transaction_id] = evidence_list

repo = Repository()

def get_customer(customer_id: str) -> Optional[Customer]:
    return repo.get_customer(customer_id)

def get_merchant(merchant_id: str) -> Optional[Merchant]:
    return repo.get_merchant(merchant_id)

def get_transaction(transaction_id: str) -> Optional[Transaction]:
    return repo.get_transaction(transaction_id)
