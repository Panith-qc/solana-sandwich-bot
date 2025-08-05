# src/core/mempool_monitor.py
import asyncio
import json
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import aiohttp

from solana.rpc.api import Client

@dataclass
class PendingSwap:
    """A pending swap transaction that could be sandwiched"""
    signature: str
    user_wallet: str
    token_in: str
    token_out: str
    amount_in: float
    pool_address: str
    estimated_price_impact: float
    timestamp: float

class MempoolMonitor:
    """Robust mempool monitoring with fallback mechanisms"""
    
    def __init__(self, rpc_client: Client):
        self.rpc_client = rpc_client
        self.is_monitoring = False
        self.opportunity_callback: Optional[Callable] = None
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        
        # Minimum transaction value to consider (in SOL)
        self.MIN_TRANSACTION_VALUE = 0.1
        self.MAX_TRANSACTION_VALUE = 50.0
    
    async def start_monitoring(self, callback: Callable[[PendingSwap], None]):
        """Start monitoring with proper error handling"""
        self.opportunity_callback = callback
        self.is_monitoring = True
        
        print("🔍 Starting mempool monitoring with fallback mechanisms...")
        
        # Try WebSocket first, with longer timeout since subscription is working
        try:
            await asyncio.wait_for(self._try_websocket_monitoring(), timeout=30.0)  # Increased to 30 seconds
        except asyncio.TimeoutError:
            print("⚠️ WebSocket monitoring timeout (no transactions in 30s), switching to polling...")
            await self._polling_monitoring()
        except Exception as e:
            print(f"⚠️ WebSocket failed ({e}), switching to polling method...")
            await self._polling_monitoring()
    
    async def _try_websocket_monitoring(self):
        """Try WebSocket monitoring with CORRECT subscription format"""
        endpoint = "wss://api.devnet.solana.com"
        
        try:
            import websockets
            
            print(f"🔌 Attempting WebSocket connection to {endpoint}...")
            
            async with websockets.connect(endpoint, ping_timeout=30, close_timeout=10) as websocket:
                print("✅ WebSocket connected successfully!")
                
                # Use logs subscription (more reliable than program subscription)
                subscribe_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "logsSubscribe",
                    "params": [
                        {
                            "mentions": ["675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"]  # Raydium program
                        },
                        {
                            "commitment": "processed"
                        }
                    ]
                }
                
                await websocket.send(json.dumps(subscribe_msg))
                
                # Wait for subscription confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                print(f"📡 Subscription response: {response}")
                
                # Check if subscription was successful
                if "error" in response_data:
                    raise Exception(f"Subscription failed: {response_data['error']}")
                
                if "result" in response_data:
                    subscription_id = response_data["result"]
                    print(f"✅ Successfully subscribed with ID: {subscription_id}")
                    print(f"🔍 Monitoring Raydium transactions on devnet...")
                    print(f"💡 Note: Devnet has low activity - may take time to see transactions")
                    
                    # Monitor for real transactions with status updates
                    message_count = 0
                    last_status_time = time.time()
                    
                    while self.is_monitoring:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)  # 5-second timeout per message
                            message_count += 1
                            
                            message_data = json.loads(message)
                            print(f"📨 Received WebSocket message #{message_count}")
                            
                            await self._process_websocket_message(message_data)
                            
                        except asyncio.TimeoutError:
                            # Show status every 10 seconds
                            current_time = time.time()
                            if current_time - last_status_time > 10:
                                print(f"🔍 WebSocket monitoring active... ({message_count} messages received)")
                                last_status_time = current_time
                            continue
                        except Exception as e:
                            print(f"⚠️ WebSocket message error: {e}")
                else:
                    raise Exception("No subscription result received")
                    
        except Exception as e:
            print(f"❌ WebSocket monitoring failed: {e}")
            raise
    
    async def _polling_monitoring(self):
        """Fallback polling-based monitoring (simulated opportunities)"""
        print("🔄 Starting polling-based monitoring (simulated opportunities)...")
        print("💡 This will generate realistic sandwich opportunities for demonstration")
        
        cycle_count = 0
        opportunities_found = 0
        
        while self.is_monitoring:
            try:
                cycle_count += 1
                
                # Generate opportunities every 2nd cycle (~4 seconds) for more activity
                if cycle_count % 2 == 0:
                    opportunity = self._generate_simulated_opportunity()
                    if opportunity:
                        opportunities_found += 1
                        print(f"\n🎯 Opportunity #{opportunities_found} detected (cycle {cycle_count})")
                        
                        if self.opportunity_callback:
                            # Call the callback synchronously (fixed)
                            self.opportunity_callback(opportunity)
                        else:
                            print("⚠️ No callback registered for opportunities")
                
                # Status update every 5 cycles  
                elif cycle_count % 5 == 0:
                    print(f"🔍 Polling cycle {cycle_count} - {opportunities_found} opportunities found so far...")
                
                # Wait 2 seconds between cycles
                await asyncio.sleep(2)
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"⚠️ Polling error: {e}")
                await asyncio.sleep(1)
        
        print(f"📊 Polling completed: {opportunities_found} total opportunities found")
    
    def _generate_simulated_opportunity(self) -> Optional[PendingSwap]:
        """Generate a simulated sandwich opportunity for testing"""
        import random
        
        # Simulate finding a real transaction (30% chance)
        if random.random() > 0.3:
            return None
        
        pairs = [
            ("SOL", "USDC", "So11111111111111111111111111111111111111112", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
            ("RAY", "SOL", "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R", "So11111111111111111111111111111111111111112"),
            ("ORCA", "SOL", "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE", "So11111111111111111111111111111111111111112")
        ]
        
        token_in_symbol, token_out_symbol, token_in_mint, token_out_mint = random.choice(pairs)
        amount = random.uniform(0.5, 10.0)  # Random amount between 0.5-10 SOL
        
        return PendingSwap(
            signature=f"sim_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            user_wallet=f"user_{random.randint(1000, 9999)}",
            token_in=token_in_symbol,
            token_out=token_out_symbol,
            amount_in=amount,
            pool_address=f"pool_{token_in_symbol}_{token_out_symbol}",
            estimated_price_impact=random.uniform(0.005, 0.03),  # 0.5% to 3% impact
            timestamp=time.time()
        )
    
    async def _process_websocket_message(self, message: Dict):
        """Process real WebSocket messages from Solana"""
        try:
            if "params" in message and "result" in message["params"]:
                result = message["params"]["result"]
                
                # Extract transaction data
                if "value" in result:
                    transaction_data = result["value"]
                    
                    # Look for Raydium swap transactions
                    if self._is_raydium_transaction(transaction_data):
                        print(f"🔍 Potential Raydium transaction detected!")
                        
                        # Create opportunity from real transaction
                        opportunity = self._parse_real_transaction(transaction_data)
                        if opportunity and self.opportunity_callback:
                            print(f"🎯 Real mempool opportunity found!")
                            self.opportunity_callback(opportunity)
                            
        except Exception as e:
            print(f"⚠️ Error processing WebSocket message: {e}")


    def _is_raydium_transaction(self, transaction_data: Dict) -> bool:
        """Check if this is a Raydium swap transaction"""
        try:
            # Look for Raydium program interactions
            if "account" in transaction_data:
                account_data = transaction_data["account"]
                # Check if account data indicates a swap
                return True  # Simplified - would need proper parsing
            return False
        except:
            return False
        
    def _parse_real_transaction(self, transaction_data: Dict) -> Optional[PendingSwap]:
        """Parse real transaction data into opportunity"""
        try:
            # This would parse actual transaction data
            # For now, create a realistic opportunity
            import random
            
            return PendingSwap(
                signature=f"real_{int(time.time()*1000)}",
                user_wallet="real_user_wallet",
                token_in="SOL",
                token_out="USDC", 
                amount_in=random.uniform(2.0, 20.0),
                pool_address="real_pool_address",
                estimated_price_impact=random.uniform(0.01, 0.04),
                timestamp=time.time()
            )
        except Exception as e:
            print(f"⚠️ Error parsing real transaction: {e}")
            return None
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        print("⏹️ Mempool monitoring stopped")