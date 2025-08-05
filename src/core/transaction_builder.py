# src/core/transaction_builder.py
from typing import Optional, Tuple
import struct

from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.message import Message
from solders.instruction import Instruction, AccountMeta
from solders.hash import Hash
from solders.system_program import TransferParams, transfer

class TransactionBuilder:
    """Build real Solana transactions for sandwich attacks"""
    
    def __init__(self, wallet_keypair: Keypair):
        self.wallet_keypair = wallet_keypair
        self.wallet_pubkey = wallet_keypair.pubkey()
        
        # Raydium Program IDs
        self.RAYDIUM_AMM_PROGRAM = Pubkey.from_string("5quBtoiQqxF9Jv6KYKctB59NT3gtJD2N1RdgFZRnTMK")
        self.TOKEN_PROGRAM = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        
    def build_raydium_swap(
        self, 
        pool_id: Pubkey,
        token_in_mint: Pubkey,
        token_out_mint: Pubkey,
        amount_in: int,
        minimum_amount_out: int,
        recent_blockhash: Hash
    ) -> Optional[VersionedTransaction]:
        """Build a Raydium swap transaction"""
        try:
            # This is a simplified version - real implementation needs proper
            # Raydium instruction encoding based on their IDL
            
            # Create swap instruction data
            instruction_data = self._encode_swap_instruction(
                amount_in, 
                minimum_amount_out
            )
            
            # Build accounts list (simplified)
            accounts = [
                AccountMeta(pubkey=self.wallet_pubkey, is_signer=True, is_writable=True),
                AccountMeta(pubkey=pool_id, is_signer=False, is_writable=True),
                AccountMeta(pubkey=token_in_mint, is_signer=False, is_writable=False),
                AccountMeta(pubkey=token_out_mint, is_signer=False, is_writable=False),
                AccountMeta(pubkey=self.TOKEN_PROGRAM, is_signer=False, is_writable=False),
            ]
            
            # Create instruction
            swap_instruction = Instruction(
                program_id=self.RAYDIUM_AMM_PROGRAM,
                accounts=accounts,
                data=instruction_data
            )
            
            # Build message
            message = Message.new_with_blockhash(
                instructions=[swap_instruction],
                payer=self.wallet_pubkey,
                blockhash=recent_blockhash
            )
            
            # Sign transaction
            transaction = VersionedTransaction(message)
            transaction.sign([self.wallet_keypair])
            
            return transaction
            
        except Exception as e:
            print(f"❌ Error building swap transaction: {e}")
            return None
    
    def _encode_swap_instruction(self, amount_in: int, minimum_amount_out: int) -> bytes:
        """Encode Raydium swap instruction data"""
        # Raydium swap instruction format (simplified)
        # Real implementation would use proper Anchor encoding
        instruction_type = 9  # Swap instruction discriminator
        
        return struct.pack(
            "<BQQ",  # Little endian: byte + 2 uint64s
            instruction_type,
            amount_in,
            minimum_amount_out
        )
    
    def calculate_swap_amounts(
        self, 
        pool_liquidity_in: int,
        pool_liquidity_out: int,
        amount_in: int,
        fee_rate: float = 0.0025
    ) -> Tuple[int, float]:
        """Calculate expected output and price impact"""
        # Constant product formula: x * y = k
        # After fee: amount_in_after_fee = amount_in * (1 - fee_rate)
        
        amount_in_after_fee = int(amount_in * (1 - fee_rate))
        
        # Calculate output using constant product formula
        amount_out = (pool_liquidity_out * amount_in_after_fee) // (pool_liquidity_in + amount_in_after_fee)
        
        # Calculate price impact
        price_before = pool_liquidity_out / pool_liquidity_in
        price_after = (pool_liquidity_out - amount_out) / (pool_liquidity_in + amount_in)
        price_impact = abs(price_after - price_before) / price_before
        
        return amount_out, price_impact
    
    def build_sandwich_transactions(
        self,
        target_transaction: str,
        pool_id: Pubkey,
        token_in: Pubkey,
        token_out: Pubkey,
        pool_liquidity_in: int,
        pool_liquidity_out: int,
        target_amount_in: int,
        recent_blockhash: Hash
    ) -> Tuple[Optional[VersionedTransaction], Optional[VersionedTransaction], float]:
        """Build front-run and back-run transactions for sandwich attack"""
        
        # Calculate optimal sandwich amounts
        # Front-run: Buy tokens to increase price before target transaction
        front_run_amount = min(
            target_amount_in // 4,  # 25% of target transaction
            pool_liquidity_in // 100  # 1% of pool liquidity
        )
        
        # Calculate front-run output
        front_run_output, front_run_impact = self.calculate_swap_amounts(
            pool_liquidity_in, pool_liquidity_out, front_run_amount
        )
        
        # Update pool state after front-run
        new_liquidity_in = pool_liquidity_in + front_run_amount
        new_liquidity_out = pool_liquidity_out - front_run_output
        
        # Calculate target transaction impact on updated pool
        target_output, target_impact = self.calculate_swap_amounts(
            new_liquidity_in, new_liquidity_out, target_amount_in
        )
        
        # Update pool state after target transaction
        final_liquidity_in = new_liquidity_in + target_amount_in
        final_liquidity_out = new_liquidity_out - target_output
        
        # Back-run: Sell tokens at higher price
        back_run_amount = front_run_output  # Sell what we bought
        back_run_output, back_run_impact = self.calculate_swap_amounts(
            final_liquidity_out, final_liquidity_in, back_run_amount
        )
        
        # Calculate profit (in terms of input token)
        profit = back_run_output - front_run_amount
        profit_percentage = profit / front_run_amount if front_run_amount > 0 else 0
        
        # Only proceed if profitable (considering gas costs)
        gas_cost_estimate = 0.001 * 2  # ~0.001 SOL per transaction * 2 transactions
        if profit_percentage < 0.01:  # Need at least 1% profit to cover gas + profit
            return None, None, 0.0
        
        # Build front-run transaction (buy)
        front_run_tx = self.build_raydium_swap(
            pool_id=pool_id,
            token_in_mint=token_in,
            token_out_mint=token_out,
            amount_in=front_run_amount,
            minimum_amount_out=int(front_run_output * 0.98),  # 2% slippage tolerance
            recent_blockhash=recent_blockhash
        )
        
        # Build back-run transaction (sell)
        back_run_tx = self.build_raydium_swap(
            pool_id=pool_id,
            token_in_mint=token_out,  # Swap directions
            token_out_mint=token_in,
            amount_in=back_run_amount,
            minimum_amount_out=int(back_run_output * 0.98),  # 2% slippage tolerance
            recent_blockhash=recent_blockhash
        )
        
        return front_run_tx, back_run_tx, profit_percentage