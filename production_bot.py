# production_bot.py
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import SolananSandwichBot

async def run_production_bot():
    """Run production bot with proper timeout handling"""
    print("🏭 PRODUCTION SOLANA SANDWICH BOT")
    print("=" * 50)
    print("⚠️  WARNING: This will execute REAL transactions with REAL money")
    print("📊 Make sure you understand the risks before proceeding")
    print("=" * 50)
    
    if input("Continue? (yes/no): ").lower() != 'yes':
        print("❌ Aborted by user")
        return
    
    # Initialize bot
    bot = SolananSandwichBot()
    bot.setup()
    
    print(f"⏱️  Bot will run for 60 seconds (or press Ctrl+C to stop)")
    print("-" * 50)
    
    try:
        # Start monitoring with timeout
        monitoring_task = asyncio.create_task(
            bot.sandwich_engine.start_real_monitoring()
        )
        
        # Wait for either completion or timeout
        await asyncio.wait_for(monitoring_task, timeout=60.0)
        
    except asyncio.TimeoutError:
        print("\n⏰ 60-second monitoring period completed")
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
    finally:
        # Stop monitoring
        if hasattr(bot.sandwich_engine, 'mempool_monitor'):
            bot.sandwich_engine.mempool_monitor.stop_monitoring()
        
        # Print final statistics
        bot.sandwich_engine.print_final_stats()

if __name__ == "__main__":
    asyncio.run(run_production_bot())