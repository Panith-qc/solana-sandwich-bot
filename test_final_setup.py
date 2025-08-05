# test_final_setup.py
import subprocess
import os

def test_complete_setup():
    print("🚀 FINAL SETUP TEST - Solana Sandwich Bot")
    print("=" * 60)
    
    # Test 1: Solana CLI
    try:
        result = subprocess.run(['solana', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Solana CLI: Working")
            print(f"   - Version: {result.stdout.strip()}")
        else:
            print("❌ Solana CLI: Failed")
    except Exception as e:
        print(f"❌ Solana CLI: Failed - {e}")
    
    # Test 2: Wallet and Balance
    try:
        result = subprocess.run(['solana', 'balance'], capture_output=True, text=True)
        if result.returncode == 0:
            balance = result.stdout.strip()
            print("✅ Wallet Balance: Working")
            print(f"   - Balance: {balance}")
        else:
            print("❌ Wallet Balance: Failed")
    except Exception as e:
        print(f"❌ Wallet Balance: Failed - {e}")
    
    # Test 3: Solana RPC Client
    try:
        from solana.rpc.api import Client
        client = Client("https://api.devnet.solana.com")
        print("✅ Solana RPC Client: Working")
    except Exception as e:
        print(f"❌ Solana RPC Client: Failed - {e}")
    
    # Test 4: Solders Core Types (Correct Imports)
    try:
        from solders.pubkey import Pubkey
        from solders.keypair import Keypair
        from solders.transaction import Transaction
        from solders.system_program import SystemProgram
        
        # Create test objects
        keypair = Keypair()
        pubkey = keypair.pubkey()
        
        print("✅ Solders Core Types: Working")
        print(f"   - Can create keypairs and pubkeys")
        print(f"   - Test wallet: {pubkey}")
    except Exception as e:
        print(f"❌ Solders Core Types: Failed - {e}")
    
    # Test 5: Configuration Loading
    try:
        from config.settings import settings
        print("✅ Configuration Loading: Working")
        print(f"   - Network: {settings.SOLANA_NETWORK}")
        print(f"   - RPC URL: {settings.SOLANA_RPC_URL}")
        print(f"   - Target Pairs: {settings.TARGET_PAIRS}")
        print(f"   - Debug Mode: {settings.DEBUG_MODE}")
    except Exception as e:
        print(f"❌ Configuration Loading: Failed - {e}")
    
    # Test 6: HTTP Libraries
    try:
        import requests
        import aiohttp
        import websockets
        print("✅ HTTP/WebSocket Libraries: Working")
    except Exception as e:
        print(f"❌ HTTP/WebSocket Libraries: Failed - {e}")
    
    # Test 7: Live RPC Connection
    try:
        from solana.rpc.api import Client
        from solders.pubkey import Pubkey
        
        client = Client("https://api.devnet.solana.com")
        # Test with a known public key (System Program)
        system_program = Pubkey.from_string("11111111111111111111111111111111")
        balance = client.get_balance(system_program)
        
        print("✅ Live RPC Connection: Working")
        print(f"   - Successfully connected to devnet")
    except Exception as e:
        print(f"❌ Live RPC Connection: Failed - {e}")
    
    print("=" * 60)
    print("🎯 SETUP STATUS:")
    print("   If all items show ✅, you're ready to build the bot!")
    print("   Any ❌ items need to be fixed before proceeding.")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_setup()