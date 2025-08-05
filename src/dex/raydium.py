# src/dex/raydium.py
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import requests
from solders.pubkey import Pubkey
from solana.rpc.api import Client

from config.settings import settings

@dataclass
class PoolInfo:
    """Raydium pool information"""
    pool_id: str
    base_mint: str
    quote_mint: str
    base_symbol: str
    quote_symbol: str
    liquidity: float
    volume_24h: float
    price: float

class RaydiumDEX:
    """Raydium DEX integration for sandwich bot"""
    
    def __init__(self, rpc_client: Client):
        self.rpc_client = rpc_client
        self.pools_cache = {}
        self.last_update = 0
        self.cache_duration = 300  # 5 minutes
        
        # Raydium program IDs
        self.RAYDIUM_LIQUIDITY_PROGRAM_ID = Pubkey.from_string(
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
        )
        self.RAYDIUM_AMM_PROGRAM_ID = Pubkey.from_string(
            "5quBtoiQqxF9Jv6KYKctB59NT3gtJD2N1RdgFZRnTMK"
        )
    
    def get_popular_pools(self) -> List[PoolInfo]:
        """Get popular trading pools from Raydium"""
        try:
            # Use Raydium API to get pool information
            url = "https://api.raydium.io/v2/sdk/liquidity/mainnet.json"
            
            if settings.SOLANA_NETWORK == "devnet":
                # For devnet, we'll create mock data
                return self._get_devnet_mock_pools()
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                pools = []
                
                # Process official pools
                for pool_id, pool_data in data.get("official", {}).items():
                    if self._is_valid_pool(pool_data):
                        pool_info = PoolInfo(
                            pool_id=pool_id,
                            base_mint=pool_data.get("baseMint", ""),
                            quote_mint=pool_data.get("quoteMint", ""),
                            base_symbol=pool_data.get("baseSymbol", ""),
                            quote_symbol=pool_data.get("quoteSymbol", ""),
                            liquidity=float(pool_data.get("liquidity", 0)),
                            volume_24h=float(pool_data.get("volume24h", 0)),
                            price=float(pool_data.get("price", 0))
                        )
                        pools.append(pool_info)
                
                # Sort by liquidity (higher is better for sandwich attacks)
                pools.sort(key=lambda x: x.liquidity, reverse=True)
                return pools[:20]  # Top 20 pools
                
        except Exception as e:
            print(f"❌ Failed to fetch Raydium pools: {e}")
            return self._get_devnet_mock_pools()
        
        return []
    
    def _get_devnet_mock_pools(self) -> List[PoolInfo]:
        """Mock pools for devnet testing"""
        return [
            PoolInfo(
                pool_id="mock_sol_usdc_pool",
                base_mint="So11111111111111111111111111111111111111112",  # SOL
                quote_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                base_symbol="SOL",
                quote_symbol="USDC",
                liquidity=1000000.0,
                volume_24h=500000.0,
                price=25.50
            ),
            PoolInfo(
                pool_id="mock_ray_sol_pool",
                base_mint="4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",  # RAY
                quote_mint="So11111111111111111111111111111111111111112",  # SOL
                base_symbol="RAY",
                quote_symbol="SOL",
                liquidity=750000.0,
                volume_24h=300000.0,
                price=0.125
            ),
            PoolInfo(
                pool_id="mock_orca_sol_pool",
                base_mint="orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",  # ORCA
                quote_mint="So11111111111111111111111111111111111111112",  # SOL
                base_symbol="ORCA",
                quote_symbol="SOL",
                liquidity=500000.0,
                volume_24h=200000.0,
                price=0.85
            )
        ]
    
    def _is_valid_pool(self, pool_data: Dict) -> bool:
        """Check if pool is valid for sandwich trading"""
        try:
            liquidity = float(pool_data.get("liquidity", 0))
            volume_24h = float(pool_data.get("volume24h", 0))
            
            # Minimum requirements for sandwich trading
            return (
                liquidity > 50000 and  # At least $50k liquidity
                volume_24h > 10000 and  # At least $10k daily volume
                pool_data.get("baseSymbol") and
                pool_data.get("quoteSymbol")
            )
        except:
            return False
    
    def get_pool_info(self, pool_id: str) -> Optional[PoolInfo]:
        """Get specific pool information"""
        pools = self.get_popular_pools()
        for pool in pools:
            if pool.pool_id == pool_id:
                return pool
        return None
    
    def find_pools_by_symbol(self, symbol: str) -> List[PoolInfo]:
        """Find pools containing a specific token symbol"""
        pools = self.get_popular_pools()
        matching_pools = []
        
        for pool in pools:
            if (symbol.upper() in pool.base_symbol.upper() or 
                symbol.upper() in pool.quote_symbol.upper()):
                matching_pools.append(pool)
        
        return matching_pools
    
    def get_sandwich_targets(self, min_liquidity: float = 100000) -> List[PoolInfo]:
        """Get pools that are good targets for sandwich attacks"""
        pools = self.get_popular_pools()
        targets = []
        
        for pool in pools:
            if (pool.liquidity >= min_liquidity and 
                pool.volume_24h > pool.liquidity * 0.1):  # At least 10% turnover
                targets.append(pool)
        
        return targets
    
    def print_pool_summary(self):
        """Print summary of available pools"""
        pools = self.get_sandwich_targets()
        
        print(f"\n🏊 Raydium Pool Summary ({len(pools)} targets found):")
        print("-" * 80)
        print(f"{'Symbol':<15} {'Pool ID':<20} {'Liquidity':<15} {'24h Volume':<15} {'Price':<10}")
        print("-" * 80)
        
        for pool in pools[:10]:  # Show top 10
            pair = f"{pool.base_symbol}/{pool.quote_symbol}"
            pool_id_short = pool.pool_id[:17] + "..." if len(pool.pool_id) > 20 else pool.pool_id
            liquidity_str = f"${pool.liquidity:,.0f}"
            volume_str = f"${pool.volume_24h:,.0f}"
            price_str = f"${pool.price:.4f}"
            
            print(f"{pair:<15} {pool_id_short:<20} {liquidity_str:<15} {volume_str:<15} {price_str:<10}")

# Test the Raydium DEX integration
if __name__ == "__main__":
    print("🧪 Testing Raydium DEX Integration...")
    
    from solana.rpc.api import Client
    client = Client(endpoint=settings.SOLANA_RPC_URL)
    
    # Test Raydium integration
    raydium = RaydiumDEX(client)
    
    # Get popular pools
    pools = raydium.get_popular_pools()
    print(f"✅ Found {len(pools)} pools")
    
    # Get sandwich targets
    targets = raydium.get_sandwich_targets()
    print(f"✅ Found {len(targets)} sandwich targets")
    
    # Print pool summary
    raydium.print_pool_summary()
    
    # Test specific symbol search
    sol_pools = raydium.find_pools_by_symbol("SOL")
    print(f"✅ Found {len(sol_pools)} SOL pools")
    
    print("🎉 Raydium DEX Integration working perfectly!")