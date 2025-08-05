def test_solana_imports():
    print("Testing Solana 0.36.6 Import Paths...")
    print("=" * 50)
    
    # Test 1: Basic solana import
    try:
        import solana
        print("✅ Basic solana import: Working")
        print(f"   - Available modules: {dir(solana)}")
    except Exception as e:
        print(f"❌ Basic solana import: Failed - {e}")
    
    # Test 2: RPC client
    try:
        from solana.rpc.api import Client
        print("✅ Solana RPC Client: Working")
    except Exception as e:
        print(f"❌ Solana RPC Client: Failed - {e}")
    
    # Test 3: PublicKey (try different paths)
    try:
        from solana.publickey import PublicKey
        print("✅ Solana PublicKey (solana.publickey): Working")
    except Exception as e:
        print(f"❌ Solana PublicKey (solana.publickey): Failed - {e}")
        
        # Try alternative path
        try:
            from solders.pubkey import Pubkey as PublicKey
            print("✅ Solana PublicKey (solders.pubkey): Working")
        except Exception as e2:
            print(f"❌ Solana PublicKey (solders.pubkey): Failed - {e2}")
    
    # Test 4: Keypair (try different paths)
    try:
        from solana.keypair import Keypair
        print("✅ Solana Keypair (solana.keypair): Working")
    except Exception as e:
        print(f"❌ Solana Keypair (solana.keypair): Failed - {e}")
        
        # Try alternative import path
        try:
            from solders.keypair import Keypair
            print("✅ Solana Keypair (solders.keypair): Working")
        except Exception as e2:
            print(f"❌ Solana Keypair (solders.keypair): Failed - {e2}")
    
    # Test 5: Transaction
    try:
        from solana.transaction import Transaction
        print("✅ Solana Transaction (solana.transaction): Working")
    except Exception as e:
        print(f"❌ Solana Transaction (solana.transaction): Failed - {e}")
        
        # Try alternative path
        try:
            from solders.transaction import Transaction
            print("✅ Solana Transaction (solders.transaction): Working")
        except Exception as e2:
            print(f"❌ Solana Transaction (solders.transaction): Failed - {e2}")
    
    # Test 6: System Program
    try:
        from solana.system_program import SystemProgram
        print("✅ System Program: Working")
    except Exception as e:
        print(f"❌ System Program: Failed - {e}")
    
    # Test 7: Check what's in solders
    try:
        import solders
        print("✅ Solders import: Working")
        print(f"   - Solders modules: {dir(solders)}")
    except Exception as e:
        print(f"❌ Solders import: Failed - {e}")
    
    print("=" * 50)
    print("🔍 Solana package analysis completed!")

if __name__ == "__main__":
    test_solana_imports()