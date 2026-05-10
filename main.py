import logging
import tkinter as tk
from gui import TradingBotGUI

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main entry point for the trading bot GUI"""
    logger = setup_logging()
    logger.info("Starting Trading Bot Application GUI")
    
    root = tk.Tk()
    app = TradingBotGUI(root)
    
    # Handle window close properly
    def on_closing():
        if app.engine and app.engine.running:
            app.stop_bot()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
