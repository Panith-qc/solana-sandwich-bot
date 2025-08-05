# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Network Configuration
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.devnet.solana.com')
    SOLANA_NETWORK = os.getenv('SOLANA_NETWORK', 'devnet')
    
    # Bot Configuration
    TARGET_PAIRS = os.getenv('TARGET_PAIRS', 'SOL/USDC').split(',')
    MAX_SLIPPAGE = float(os.getenv('MAX_SLIPPAGE', '0.05'))
    MIN_PROFIT_THRESHOLD = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.001'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '1.0'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # Development
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'true').lower() == 'true'
    DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

settings = Settings()