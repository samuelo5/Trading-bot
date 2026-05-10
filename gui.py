import tkinter as tk
from tkinter import ttk
import threading
import logging
import queue
from config import Config
from trading_engine import TradingEngine
from market_data import MarketDataFetcher
from strategies.base_strategy import StrategyManager

class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget"""
    def __init__(self, text):
        super().__init__()
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            self.text.yview(tk.END)
        self.text.after(0, append)

class TradingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Llama Trading Bot Dashboard")
        self.root.geometry("900x700")
        
        self.engine = None
        self.bot_thread = None
        
        self.create_widgets()
        self.setup_logging()
        
    def create_widgets(self):
        # Top Frame - Controls
        control_frame = ttk.LabelFrame(self.root, text="Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Bot", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="Status: Stopped")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, font=("Arial", 12, "bold"))
        status_label.pack(side=tk.RIGHT, padx=10)
        
        # Manual Trade Frame
        manual_frame = ttk.LabelFrame(self.root, text="Manual Trading")
        manual_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(manual_frame, text="Symbol:").pack(side=tk.LEFT, padx=5, pady=5)
        self.symbol_var = tk.StringVar(value="EURUSD")
        ttk.Entry(manual_frame, textvariable=self.symbol_var, width=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.buy_btn = ttk.Button(manual_frame, text="Buy (Long)", command=lambda: self.manual_trade("LONG"), state=tk.DISABLED)
        self.buy_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.sell_btn = ttk.Button(manual_frame, text="Sell (Short)", command=lambda: self.manual_trade("SHORT"), state=tk.DISABLED)
        self.sell_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Middle Frame - Open Positions
        positions_frame = ttk.LabelFrame(self.root, text="Open Positions")
        positions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("Symbol", "Type", "Size", "Entry Price", "Current Price", "PnL")
        self.tree = ttk.Treeview(positions_frame, columns=columns, show="headings", height=5)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bottom Frame - Logs
        log_frame = ttk.LabelFrame(self.root, text="System Logs (Llama Predictions & Trades)")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, state='disabled', bg='black', fg='lightgreen', font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Periodic update
        self.root.after(1000, self.update_positions)
        
    def setup_logging(self):
        # Add the TextHandler to the root logger
        text_handler = TextHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        text_handler.setFormatter(formatter)
        logging.getLogger().addHandler(text_handler)
        
    def init_bot(self):
        try:
            config = Config()
            data_fetcher = MarketDataFetcher(config)
            strategy_manager = StrategyManager(config)
            self.engine = TradingEngine(config, data_fetcher, strategy_manager)
            return True
        except Exception as e:
            logging.error(f"Failed to initialize bot: {e}")
            return False
        
    def start_bot(self):
        if self.init_bot():
            self.status_var.set("Status: Running")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.buy_btn.config(state=tk.NORMAL)
            self.sell_btn.config(state=tk.NORMAL)
            
            self.bot_thread = threading.Thread(target=self.engine.run, daemon=True)
            self.bot_thread.start()
            
    def stop_bot(self):
        if self.engine:
            logging.info("Stopping bot... Please wait for current cycle to finish.")
            self.status_var.set("Status: Stopping...")
            self.engine.running = False
            self.stop_btn.config(state=tk.DISABLED)
            
            def cleanup():
                if self.bot_thread:
                    self.bot_thread.join(timeout=30)
                # Ensure UI updates happen on main thread
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.buy_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.sell_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.status_var.set("Status: Stopped"))
                
            threading.Thread(target=cleanup, daemon=True).start()

    def manual_trade(self, position_type):
        if not self.engine or not getattr(self.engine, 'running', False):
            logging.warning("Bot is not running. Cannot execute manual trade.")
            return
            
        symbol = self.symbol_var.get().strip().upper()
        if not symbol:
            logging.warning("Please enter a symbol.")
            return
            
        def execute():
            try:
                logging.info(f"Executing manual {position_type} for {symbol}...")
                quotes = self.engine.data_fetcher.get_forex_quotes([symbol])
                if symbol not in quotes:
                    logging.error(f"Could not fetch current price for {symbol}")
                    return
                    
                current_price = quotes[symbol]['mid']
                signal = {"action": "BUY" if position_type == "LONG" else "SELL", "strength": 1.0, "manual": True}
                self.engine._open_position(symbol, current_price, position_type, signal)
            except Exception as e:
                logging.error(f"Manual trade failed: {str(e)}")
                
        threading.Thread(target=execute, daemon=True).start()

    def update_positions(self):
        # Periodically refresh the positions treeview
        if self.engine and self.engine.running:
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            for symbol, pos in self.engine.positions.items():
                pnl_str = f"${pos.get_pnl():.2f} ({pos.get_pnl_percent():.2f}%)"
                self.tree.insert("", tk.END, values=(
                    pos.symbol,
                    pos.position_type,
                    f"{pos.size:.4f}",
                    f"${pos.entry_price:.4f}",
                    f"${pos.current_price:.4f}",
                    pnl_str
                ))
                
        self.root.after(2000, self.update_positions)
