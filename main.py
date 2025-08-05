# main.py
import asyncio
import sys
import os
from src.dex.raydium import RaydiumDEX
from src.core.sandwich_engine import SandwichEngine

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.wallet_manager import WalletManager
from src.core.rpc_client import RPCClientWrapper
from config.settings import settings

class SolananSandwichBot:
    """Main Solana Sandwich Bot Class"""
    
    def __init__(self):
        print("🤖 Initializing Solana Sandwich Bot...")
        
        # Initialize components
        self.rpc_client = RPCClientWrapper()
        self.wallet_manager = WalletManager(self.rpc_client.client)
        self.raydium_dex = RaydiumDEX(self.rpc_client.client)
        self.sandwich_engine = SandwichEngine(
            self.rpc_client, 
            self.wallet_manager, 
            self.raydium_dex
        )
        
        print(f"✅ Bot initialized for {settings.SOLANA_NETWORK}")
    
    def setup(self):
        """Setup the bot with wallet and initial configuration"""
        print("🔧 Setting up bot...")
        
        # Load wallet
        wallet_path = os.path.expanduser("~/.config/solana/dev-wallet.json")
        self.wallet_manager.load_keypair_from_file(wallet_path)
        
        # Check balance
        balance = self.wallet_manager.get_balance()
        print(f"💰 Wallet Balance: {balance} SOL")

        print("🏊 Loading DEX pools...")
        self.raydium_dex.print_pool_summary()
        
        if balance < 0.1:
            print("⚠️ Warning: Low SOL balance. Consider adding more SOL for trading.")
        
        print("✅ Bot setup complete!")
    
    def run(self, duration_seconds: int = 60):
        """Run the sandwich bot for specified duration"""
        print("🚀 Starting Solana Sandwich Bot...")
        print(f"📍 Network: {settings.SOLANA_NETWORK}")
        print(f"🎯 Target Pairs: {settings.TARGET_PAIRS}")
        print(f"🔧 Debug Mode: {settings.DEBUG_MODE}")
        
        if settings.DRY_RUN:
            print("🧪 Running in DRY RUN mode - simulated trades only")
        
        # Start the sandwich monitoring loop
        self.sandwich_engine.run_monitoring_loop(duration_seconds)

if __name__ == "__main__":
    # Create and run the bot
    bot = SolananSandwichBot()
    bot.setup()
    bot.run(30)