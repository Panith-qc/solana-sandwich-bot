# src/utils/wallet_manager.py
import json
import os
from typing import Optional

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
#from config.settings import settings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

class WalletManager:
    """Handles wallet operations for the sandwich bot"""
    
    def __init__(self, rpc_client: Optional[Client] = None):
        self.client = rpc_client or Client(endpoint=settings.SOLANA_RPC_URL)
        self.keypair: Optional[Keypair] = None
        self.public_key: Optional[Pubkey] = None
    
    def load_keypair_from_file(self, file_path: str) -> Keypair:
        """Load keypair from Solana CLI wallet file"""
        try:
            with open(file_path, 'r') as f:
                keypair_data = json.load(f)
            
            # Convert to bytes if needed
            if isinstance(keypair_data, list):
                keypair_bytes = bytes(keypair_data)
            else:
                keypair_bytes = keypair_data
            
            self.keypair = Keypair.from_bytes(keypair_bytes)
            self.public_key = self.keypair.pubkey()
            
            print(f"✅ Wallet loaded: {self.public_key}")
            return self.keypair
            
        except Exception as e:
            print(f"❌ Failed to load wallet: {e}")
            raise
    
    def get_balance(self) -> float:
        """Get SOL balance of loaded wallet"""
        if not self.public_key:
            raise ValueError("No wallet loaded")
        
        try:
            response = self.client.get_balance(self.public_key)
            balance_lamports = response.value
            balance_sol = balance_lamports / 1_000_000_000  # Convert lamports to SOL
            return balance_sol
        except Exception as e:
            print(f"❌ Failed to get balance: {e}")
            raise
    
    def get_address(self) -> str:
        """Get wallet address as string"""
        if not self.public_key:
            raise ValueError("No wallet loaded")
        return str(self.public_key)

# Test the wallet manager
if __name__ == "__main__":
    print("🧪 Testing Wallet Manager...")
    
    # Test wallet manager
    wallet = WalletManager()
    
    # Load wallet from Solana CLI
    wallet_path = os.path.expanduser("~/.config/solana/dev-wallet.json")
    
    try:
        wallet.load_keypair_from_file(wallet_path)
        
        # Get balance
        balance = wallet.get_balance()
        print(f"✅ Wallet Balance: {balance} SOL")
        print(f"✅ Wallet Address: {wallet.get_address()}")
        print("🎉 Wallet Manager working perfectly!")
        
    except Exception as e:
        print(f"❌ Wallet Manager test failed: {e}")