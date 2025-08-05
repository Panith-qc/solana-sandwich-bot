# src/core/rpc_client.py
import time
from typing import Optional, Dict, Any
import asyncio

from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed

from config.settings import settings

class RPCClientWrapper:
    """Enhanced RPC client for sandwich bot operations"""
    
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or settings.SOLANA_RPC_URL
        self.client = Client(endpoint=self.endpoint)
        self.stats = {
            'transactions_sent': 0,
            'transactions_confirmed': 0,
            'transactions_failed': 0,
            'average_confirmation_time': 0.0
        }
    
    def get_balance(self, pubkey: Pubkey) -> float:
        """Get SOL balance for a public key"""
        try:
            response = self.client.get_balance(pubkey)
            balance_lamports = response.value
            return balance_lamports / 1_000_000_000  # Convert to SOL
        except Exception as e:
            print(f"❌ Failed to get balance: {e}")
            return 0.0
    
    def send_transaction(self, transaction: VersionedTransaction) -> Optional[str]:
        """Send a transaction and return signature"""
        try:
            start_time = time.time()
            
            # Send transaction
            opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
            response = self.client.send_transaction(transaction, opts)
            
            if response.value:
                signature = str(response.value)
                self.stats['transactions_sent'] += 1
                
                print(f"✅ Transaction sent: {signature}")
                return signature
            else:
                print(f"❌ Transaction failed to send")
                self.stats['transactions_failed'] += 1
                return None
                
        except Exception as e:
            print(f"❌ Failed to send transaction: {e}")
            self.stats['transactions_failed'] += 1
            return None
    
    def confirm_transaction(self, signature: str, timeout: int = 30) -> bool:
        """Wait for transaction confirmation"""
        try:
            start_time = time.time()
            
            # Poll for confirmation
            for _ in range(timeout):
                try:
                    response = self.client.get_signature_statuses([signature])
                    if response.value and response.value[0]:
                        status = response.value[0]
                        if status.confirmation_status:
                            confirmation_time = time.time() - start_time
                            self.stats['transactions_confirmed'] += 1
                            
                            # Update average confirmation time
                            if self.stats['transactions_confirmed'] > 1:
                                current_avg = self.stats['average_confirmation_time']
                                new_avg = (current_avg * (self.stats['transactions_confirmed'] - 1) + confirmation_time) / self.stats['transactions_confirmed']
                                self.stats['average_confirmation_time'] = new_avg
                            else:
                                self.stats['average_confirmation_time'] = confirmation_time
                            
                            print(f"✅ Transaction confirmed in {confirmation_time:.2f}s: {signature}")
                            return True
                    
                    time.sleep(1)  # Wait 1 second before next check
                    
                except Exception as e:
                    print(f"⚠️ Error checking confirmation: {e}")
                    time.sleep(1)
            
            print(f"⚠️ Transaction confirmation timeout: {signature}")
            return False
            
        except Exception as e:
            print(f"❌ Failed to confirm transaction: {e}")
            return False
    
    def get_recent_blockhash(self) -> Optional[str]:
        """Get recent blockhash for transactions"""
        try:
            response = self.client.get_latest_blockhash()
            return str(response.value.blockhash)
        except Exception as e:
            print(f"❌ Failed to get recent blockhash: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        success_rate = 0.0
        if self.stats['transactions_sent'] > 0:
            success_rate = (self.stats['transactions_confirmed'] / self.stats['transactions_sent']) * 100
        
        return {
            **self.stats,
            'success_rate': f"{success_rate:.2f}%",
            'endpoint': self.endpoint
        }
    
    def print_stats(self):
        """Print client statistics"""
        stats = self.get_stats()
        print("\n📊 RPC Client Statistics:")
        print(f"   - Endpoint: {stats['endpoint']}")
        print(f"   - Transactions Sent: {stats['transactions_sent']}")
        print(f"   - Transactions Confirmed: {stats['transactions_confirmed']}")
        print(f"   - Transactions Failed: {stats['transactions_failed']}")
        print(f"   - Success Rate: {stats['success_rate']}")
        print(f"   - Avg Confirmation Time: {stats['average_confirmation_time']:.2f}s")

# Test the RPC client wrapper
if __name__ == "__main__":
    print("🧪 Testing RPC Client Wrapper...")
    
    # Test RPC client
    rpc = RPCClientWrapper()
    
    # Test basic functionality
    from solders.pubkey import Pubkey
    
    # Test with system program (known address)
    system_program = Pubkey.from_string("11111111111111111111111111111111")
    balance = rpc.get_balance(system_program)
    print(f"✅ System Program Balance: {balance} SOL")
    
    # Test blockhash retrieval
    blockhash = rpc.get_recent_blockhash()
    if blockhash:
        print(f"✅ Recent Blockhash: {blockhash[:20]}...")
    
    # Print initial stats
    rpc.print_stats()
    
    print("🎉 RPC Client Wrapper working perfectly!")