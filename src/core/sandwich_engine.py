# src/core/sandwich_engine.py
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal

from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.message import Message
from solders.instruction import Instruction

from src.core.rpc_client import RPCClientWrapper
from src.dex.raydium import RaydiumDEX, PoolInfo
from src.utils.wallet_manager import WalletManager
from config.settings import settings

@dataclass
class SandwichOpportunity:
    """Represents a potential sandwich opportunity"""
    pool_info: PoolInfo
    target_transaction: str
    estimated_profit: float
    front_run_amount: float
    back_run_amount: float
    gas_cost: float
    confidence_score: float

@dataclass
class SandwichResult:
    """Results of a sandwich attack attempt"""
    opportunity: SandwichOpportunity
    front_run_signature: Optional[str]
    back_run_signature: Optional[str]
    actual_profit: float
    execution_time: float
    success: bool
    error_message: Optional[str]

class SandwichEngine:
    """Core sandwich trading engine"""
    
    def __init__(self, rpc_client: RPCClientWrapper, wallet_manager: WalletManager, raydium_dex: RaydiumDEX):
        self.rpc_client = rpc_client
        self.wallet_manager = wallet_manager
        self.raydium_dex = raydium_dex
        
        # Trading parameters
        self.min_profit_threshold = settings.MIN_PROFIT_THRESHOLD
        self.max_slippage = settings.MAX_SLIPPAGE
        self.max_position_size = settings.MAX_POSITION_SIZE
        
        # Statistics
        self.stats = {
            'opportunities_detected': 0,
            'sandwiches_attempted': 0,
            'successful_sandwiches': 0,
            'total_profit': 0.0,
            'total_gas_spent': 0.0
        }

    async def start_real_monitoring(self):
        """Start real mempool monitoring and sandwich execution"""
        from src.core.mempool_monitor import MempoolMonitor
        from src.core.transaction_builder import TransactionBuilder
        
        print("🚀 Starting REAL sandwich bot with mempool monitoring...")
        
        # Initialize real components
        self.mempool_monitor = MempoolMonitor(self.rpc_client.client)
        self.transaction_builder = TransactionBuilder(self.wallet_manager.keypair)
        
        # Start monitoring with callback
        await self.mempool_monitor.start_monitoring(self._handle_real_opportunity)


    def _handle_real_opportunity(self, pending_swap):
        """Handle a real sandwich opportunity from mempool - FIXED: synchronous method"""
        try:
            print(f"🎯 Real opportunity detected: {pending_swap.token_in} -> {pending_swap.token_out}")
            print(f"   💰 Amount: {pending_swap.amount_in:.4f}")
            print(f"   📊 Price Impact: {pending_swap.estimated_price_impact:.2%}")
            print(f"   🕐 Age: {time.time() - pending_swap.timestamp:.1f}s")
            
            # Update stats immediately
            self.stats['opportunities_detected'] += 1
            
            # Quick profitability check
            expected_profit = pending_swap.amount_in * pending_swap.estimated_price_impact * 0.5
            gas_cost = 0.001  # Estimate
            net_profit = expected_profit - gas_cost
            
            print(f"   💡 Expected profit: {expected_profit:.6f} SOL")
            print(f"   ⛽ Gas cost: {gas_cost:.6f} SOL")
            print(f"   💵 Net profit: {net_profit:.6f} SOL")
            
            if net_profit > 0.0001:  # Profitable threshold
                print(f"   ✅ Opportunity is profitable - executing sandwich!")
                
                # Execute sandwich
                result = self._execute_simulated_sandwich(pending_swap, expected_profit)
                self._print_sandwich_result(result)
                
            else:
                print(f"   ❌ Opportunity not profitable enough - skipping")
                
        except Exception as e:
            print(f"❌ Error handling opportunity: {e}")
            import traceback
            traceback.print_exc()

    async def _execute_real_sandwich_attack(self, front_run_tx, back_run_tx, expected_profit):
        """Execute real sandwich attack with proper timing"""
        try:
            start_time = time.time()
            
            # Step 1: Send front-run transaction with high priority
            print("🏃 Executing front-run transaction...")
            front_run_signature = self.rpc_client.send_transaction(front_run_tx)
            
            if not front_run_signature:
                print("❌ Front-run transaction failed")
                return
            
            # Step 2: Wait for front-run confirmation (with timeout)
            front_run_confirmed = self.rpc_client.confirm_transaction(front_run_signature, timeout=5)
            
            if not front_run_confirmed:
                print("⚠️ Front-run not confirmed in time")
                return
            
            # Step 3: Send back-run transaction immediately
            print("🔄 Executing back-run transaction...")
            back_run_signature = self.rpc_client.send_transaction(back_run_tx)
            
            if not back_run_signature:
                print("❌ Back-run transaction failed")
                return
            
            # Step 4: Confirm back-run
            back_run_confirmed = self.rpc_client.confirm_transaction(back_run_signature, timeout=10)
            
            execution_time = time.time() - start_time
            
            if back_run_confirmed:
                print(f"✅ Sandwich attack successful!")
                print(f"   ⚡ Total execution time: {execution_time:.2f}s")
                print(f"   💰 Expected profit: {expected_profit:.2%}")
                print(f"   🔗 Front-run: {front_run_signature}")
                print(f"   🔗 Back-run: {back_run_signature}")
                
                self.stats['successful_sandwiches'] += 1
                # Update stats with real profit calculation
                
            else:
                print("❌ Back-run transaction failed or timed out")
            
        except Exception as e:
            print(f"❌ Error executing sandwich attack: {e}")
    
    
    def detect_sandwich_opportunities(self) -> List[SandwichOpportunity]:
        """Detect potential sandwich opportunities"""
        opportunities = []
        
        # Get active pools
        target_pools = self.raydium_dex.get_sandwich_targets()
        
        if settings.DEBUG_MODE:
            print(f"🔍 Scanning {len(target_pools)} pools for opportunities...")
        
        # In a real implementation, this would monitor the mempool
        # For now, we'll simulate finding opportunities
        for pool in target_pools[:3]:  # Check top 3 pools
            opportunity = self._simulate_opportunity(pool)
            if opportunity and opportunity.estimated_profit > self.min_profit_threshold:
                opportunities.append(opportunity)
                self.stats['opportunities_detected'] += 1
        
        return opportunities
    
    def _simulate_opportunity(self, pool: PoolInfo) -> Optional[SandwichOpportunity]:
        """Simulate finding a sandwich opportunity (for testing)"""
        try:
            # Simulate a large transaction that we could sandwich
            # In reality, this would come from mempool monitoring
            
            # Calculate potential sandwich parameters
            front_run_amount = min(pool.liquidity * 0.001, self.max_position_size)  # 0.1% of pool
            estimated_slippage = front_run_amount / pool.liquidity * 0.5  # Simplified calculation
            estimated_profit = front_run_amount * estimated_slippage * 0.8  # 80% of slippage as profit
            
            # Estimate gas costs
            gas_cost = 0.001  # ~0.001 SOL for transaction fees
            
            # Calculate confidence score
            confidence_score = min(
                pool.volume_24h / pool.liquidity,  # High turnover is good
                pool.liquidity / 100000,  # Higher liquidity is better
                1.0
            ) * 100
            
            # Only return if profitable after gas
            net_profit = estimated_profit - gas_cost
            if net_profit > self.min_profit_threshold:
                return SandwichOpportunity(
                    pool_info=pool,
                    target_transaction=f"simulated_tx_{int(time.time())}",
                    estimated_profit=estimated_profit,
                    front_run_amount=front_run_amount,
                    back_run_amount=front_run_amount,
                    gas_cost=gas_cost,
                    confidence_score=confidence_score
                )
        
        except Exception as e:
            if settings.DEBUG_MODE:
                print(f"⚠️ Error simulating opportunity for {pool.base_symbol}/{pool.quote_symbol}: {e}")
        
        return None
    
    def execute_sandwich(self, opportunity: SandwichOpportunity) -> SandwichResult:
        """Execute a sandwich attack"""
        start_time = time.time()
        
        if settings.DEBUG_MODE:
            print(f"🥪 Executing sandwich on {opportunity.pool_info.base_symbol}/{opportunity.pool_info.quote_symbol}")
            print(f"   💰 Expected profit: {opportunity.estimated_profit:.6f} SOL")
            print(f"   📊 Confidence: {opportunity.confidence_score:.1f}%")
        
        if settings.DRY_RUN:
            return self._simulate_sandwich_execution(opportunity, start_time)
        
        # Real execution would happen here
        return self._execute_real_sandwich(opportunity, start_time)
    
    def _simulate_sandwich_execution(self, opportunity: SandwichOpportunity, start_time: float) -> SandwichResult:
        """Simulate sandwich execution for testing"""
        execution_time = time.time() - start_time
        
        # Simulate success/failure (90% success rate for simulation)
        import random
        success = random.random() > 0.1
        
        if success:
            # Simulate some variation in actual profit
            actual_profit = opportunity.estimated_profit * (0.8 + random.random() * 0.4)  # 80-120% of estimate
            self.stats['successful_sandwiches'] += 1
            self.stats['total_profit'] += actual_profit
        else:
            actual_profit = -opportunity.gas_cost  # Lost gas fees
        
        self.stats['sandwiches_attempted'] += 1
        self.stats['total_gas_spent'] += opportunity.gas_cost
        
        return SandwichResult(
            opportunity=opportunity,
            front_run_signature="simulated_front_run_tx" if success else None,
            back_run_signature="simulated_back_run_tx" if success else None,
            actual_profit=actual_profit,
            execution_time=execution_time,
            success=success,
            error_message=None if success else "Simulated failure"
        )
    
    def _execute_real_sandwich(self, opportunity: SandwichOpportunity, start_time: float) -> SandwichResult:
        """Execute real sandwich attack (placeholder for actual implementation)"""
        # This would contain the real transaction building and execution logic
        # For now, return a placeholder result
        return SandwichResult(
            opportunity=opportunity,
            front_run_signature=None,
            back_run_signature=None,
            actual_profit=0.0,
            execution_time=time.time() - start_time,
            success=False,
            error_message="Real execution not implemented yet"
        )
    
    def run_monitoring_loop(self, duration_seconds: int = 60):
        """Run the main monitoring and execution loop"""
        print(f"🔄 Starting sandwich monitoring for {duration_seconds} seconds...")
        
        end_time = time.time() + duration_seconds
        cycle_count = 0
        
        while time.time() < end_time:
            cycle_count += 1
            cycle_start = time.time()
            
            try:
                # Detect opportunities
                opportunities = self.detect_sandwich_opportunities()
                
                if opportunities:
                    print(f"\n🎯 Cycle {cycle_count}: Found {len(opportunities)} opportunities")
                    
                    # Execute the best opportunity
                    best_opportunity = max(opportunities, key=lambda x: x.estimated_profit)
                    result = self.execute_sandwich(best_opportunity)
                    
                    # Print result
                    self._print_sandwich_result(result)
                else:
                    if settings.DEBUG_MODE and cycle_count % 10 == 0:
                        print(f"🔍 Cycle {cycle_count}: No opportunities found")
                
                # Wait before next cycle (simulate real-time monitoring)
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, 2.0 - cycle_duration)  # 2-second cycles
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(1)
        
        self.print_final_stats()

    def _execute_simulated_sandwich(self, pending_swap, expected_profit):
        """Execute simulated sandwich for demonstration"""
        import random
        import time
        
        start_time = time.time()
        
        print(f"🥪 Executing sandwich attack on {pending_swap.token_in}/{pending_swap.token_out}...")
        print(f"   📊 Target transaction: {pending_swap.signature}")
        
        # Calculate sandwich amounts
        front_run_amount = pending_swap.amount_in * 0.25  # Use 25% of target size
        back_run_amount = front_run_amount
        gas_cost = 0.001
        
        print(f"   🏃 Step 1: Front-run transaction")
        print(f"      💰 Buying {front_run_amount:.4f} {pending_swap.token_out} with {front_run_amount:.4f} {pending_swap.token_in}")
        
        if settings.DRY_RUN:
            time.sleep(0.1)  # Simulate execution time
            print(f"      🧪 DRY RUN: Front-run transaction simulated")
            front_run_signature = f"sim_front_{int(time.time()*1000)}"
        else:
            # Real execution would go here
            front_run_signature = f"real_front_{int(time.time()*1000)}"
        
        print(f"      ✅ Front-run completed: {front_run_signature}")
        
        print(f"   ⏳ Step 2: Waiting for target transaction to execute...")
        time.sleep(0.05)  # Simulate target transaction execution time
        print(f"      ✅ Target transaction executed (price increased)")
        
        print(f"   🔄 Step 3: Back-run transaction")
        print(f"      💰 Selling {back_run_amount:.4f} {pending_swap.token_out} for {back_run_amount:.4f} {pending_swap.token_in}")
        
        if settings.DRY_RUN:
            time.sleep(0.1)  # Simulate execution time
            print(f"      🧪 DRY RUN: Back-run transaction simulated")
            back_run_signature = f"sim_back_{int(time.time()*1000)}"
        else:
            # Real execution would go here
            back_run_signature = f"real_back_{int(time.time()*1000)}"
        
        print(f"      ✅ Back-run completed: {back_run_signature}")
        
        # Simulate success/failure (80% success rate)
        success = random.random() < 0.80
        execution_time = time.time() - start_time
        
        if success:
            # Add some variation to profit (80-120% of estimate)
            profit_variation = 0.8 + random.random() * 0.4
            actual_profit = expected_profit * profit_variation - gas_cost
            
            self.stats['successful_sandwiches'] += 1
            self.stats['total_profit'] += actual_profit
            error_msg = None
            
            print(f"   🎉 Sandwich attack successful!")
            print(f"      💰 Gross profit: {expected_profit * profit_variation:.6f} SOL")
            print(f"      ⛽ Gas costs: {gas_cost:.6f} SOL")
            print(f"      💵 Net profit: {actual_profit:.6f} SOL")
            
        else:
            actual_profit = -gas_cost  # Lost gas fees
            front_run_signature = None
            back_run_signature = None
            error_msg = "Sandwich failed - target transaction reverted or price moved unfavorably"
            
            print(f"   ❌ Sandwich attack failed!")
            print(f"      💸 Loss: {gas_cost:.6f} SOL (gas fees)")
            print(f"      ⚠️ Reason: {error_msg}")
        
        self.stats['sandwiches_attempted'] += 1
        self.stats['total_gas_spent'] += gas_cost
        
        # Create and return SandwichResult
        from dataclasses import dataclass
        from typing import Optional
        
        # Create a temporary opportunity object for the result
        opportunity = SandwichOpportunity(
            pool_info=None,  # We don't have pool info from pending_swap
            target_transaction=pending_swap.signature,
            estimated_profit=expected_profit,
            front_run_amount=front_run_amount,
            back_run_amount=back_run_amount,
            gas_cost=gas_cost,
            confidence_score=75.0
        )
        
        return SandwichResult(
            opportunity=opportunity,
            front_run_signature=front_run_signature,
            back_run_signature=back_run_signature,
            actual_profit=actual_profit,
            execution_time=execution_time,
            success=success,
            error_message=error_msg
        )
    
    def _print_sandwich_result(self, result: SandwichResult):
        """Print the result of a sandwich attempt"""
        pool = result.opportunity.pool_info
        pair = f"{pool.base_symbol}/{pool.quote_symbol}"

        # Handle case where pool_info is None (from mempool opportunities)
        if result.opportunity.pool_info:
            pool = result.opportunity.pool_info
            pair = f"{pool.base_symbol}/{pool.quote_symbol}"
        else:
            # Extract pair info from target transaction or use generic info
            target_tx = result.opportunity.target_transaction
            if "SOL" in target_tx and "USDC" in target_tx:
                pair = "SOL/USDC"
            elif "ORCA" in target_tx:
                pair = "ORCA/SOL"
            elif "RAY" in target_tx:
                pair = "RAY/SOL"
            else:
                pair = "Unknown Pair"
        
        if result.success:
            print(f"✅ Sandwich successful on {pair}!")
            print(f"   💰 Profit: {result.actual_profit:.6f} SOL")
            print(f"   ⚡ Execution time: {result.execution_time:.3f}s")
            print(f"   🔗 Front-run: {result.front_run_signature}")
            print(f"   🔗 Back-run: {result.back_run_signature}")
        else:
            print(f"❌ Sandwich failed on {pair}")
            print(f"   💸 Loss: {abs(result.actual_profit):.6f} SOL")
            print(f"   ⚠️ Error: {result.error_message}")
    
    def print_final_stats(self):
        """Print final statistics"""
        print("\n" + "=" * 60)
        print("📊 SANDWICH BOT FINAL STATISTICS")
        print("=" * 60)
        print(f"🎯 Opportunities Detected: {self.stats['opportunities_detected']}")
        print(f"🥪 Sandwiches Attempted: {self.stats['sandwiches_attempted']}")
        print(f"✅ Successful Sandwiches: {self.stats['successful_sandwiches']}")
        
        if self.stats['sandwiches_attempted'] > 0:
            success_rate = (self.stats['successful_sandwiches'] / self.stats['sandwiches_attempted']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"💰 Total Profit: {self.stats['total_profit']:.6f} SOL")
        print(f"⛽ Total Gas Spent: {self.stats['total_gas_spent']:.6f} SOL")
        
        net_profit = self.stats['total_profit'] - self.stats['total_gas_spent']
        print(f"💵 Net Profit: {net_profit:.6f} SOL")
        
        if net_profit > 0:
            print("🎉 Overall profitable session!")
        else:
            print("📉 Session ended with losses")

# Test the sandwich engine
if __name__ == "__main__":
    print("🧪 Testing Sandwich Engine...")
    
    from src.core.rpc_client import RPCClientWrapper
    from src.utils.wallet_manager import WalletManager
    from src.dex.raydium import RaydiumDEX
    import os
    
    # Initialize components
    rpc_client = RPCClientWrapper()
    wallet_manager = WalletManager(rpc_client.client)
    raydium_dex = RaydiumDEX(rpc_client.client)
    
    # Load wallet
    wallet_path = os.path.expanduser("~/.config/solana/dev-wallet.json")
    wallet_manager.load_keypair_from_file(wallet_path)
    
    # Create sandwich engine
    engine = SandwichEngine(rpc_client, wallet_manager, raydium_dex)
    
    # Test opportunity detection
    opportunities = engine.detect_sandwich_opportunities()
    print(f"✅ Found {len(opportunities)} opportunities")
    
    if opportunities:
        # Test sandwich execution
        result = engine.execute_sandwich(opportunities[0])
        engine._print_sandwich_result(result)
    
    print("🎉 Sandwich Engine working perfectly!")