import logging
import threading
import tkinter as tk
from tkinter import ttk

from config import Config
from market_data import MarketDataFetcher
from trading_engine import TradingEngine
from strategies.base_strategy import StrategyManager


class TextHandler(logging.Handler):
    """Bridge log records into a Tkinter text widget."""

    def __init__(self, text_widget):
        super().__init__()
        self.text = text_widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state="normal")
            self.text.insert(tk.END, msg + "\n")
            self.text.configure(state="disabled")
            self.text.yview(tk.END)

        self.text.after(0, append)


class TradingBotGUI:
    """Modern trading dashboard UI."""

    def __init__(self, root):
        self.root = root
        self.root.title("Trading Bot Dashboard")
        self.root.geometry("1200x820")
        self.root.minsize(760, 560)
        self.root.configure(bg="#07141f")

        self.engine = None
        self.bot_thread = None

        self._setup_theme()
        self.create_widgets()
        self.setup_logging()

    def _setup_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Dashboard.TFrame", background="#07141f")
        style.configure("Panel.TFrame", background="#0d1b2a")
        style.configure("Card.TFrame", background="#101f2f")
        style.configure("Header.TLabel", background="#101f2f", foreground="#e6f1ff", font=("Segoe UI", 18, "bold"))
        style.configure("SubHeader.TLabel", background="#101f2f", foreground="#8ab4f8", font=("Segoe UI", 10, "bold"))
        style.configure("Metric.TLabel", background="#101f2f", foreground="#dfeefe", font=("Segoe UI", 11, "bold"))
        style.configure("Value.TLabel", background="#101f2f", foreground="#7ee7c5", font=("Segoe UI", 16, "bold"))
        style.configure("Table.Heading", background="#1f2f46", foreground="#dfeefe", font=("Segoe UI", 10, "bold"))
        style.configure("Table.Row", background="#0d1b2a", foreground="#eaf3ff")

        style.configure("Accent.TButton",
                        background="#3b82f6",
                        foreground="#ffffff",
                        padding=(18, 10),
                        font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton",
                  background=[("active", "#2563eb"), ("pressed", "#1d4ed8")],
                  foreground=[("disabled", "#cbd5e1")])

        style.configure("Success.TButton",
                        background="#10b981",
                        foreground="#ffffff",
                        padding=(18, 10),
                        font=("Segoe UI", 10, "bold"))
        style.map("Success.TButton",
                  background=[("active", "#059669"), ("pressed", "#047857")],
                  foreground=[("disabled", "#d1fae5")])

        style.configure("Danger.TButton",
                        background="#ef4444",
                        foreground="#ffffff",
                        padding=(18, 10),
                        font=("Segoe UI", 10, "bold"))
        style.map("Danger.TButton",
                  background=[("active", "#dc2626"), ("pressed", "#b91c1c")],
                  foreground=[("disabled", "#fee2e2")])

        style.configure("Secondary.TEntry",
                        fieldbackground="#111827",
                        foreground="#e2e8f0",
                        insertcolor="#ffffff",
                        bordercolor="#334155",
                        lightcolor="#334155",
                        darkcolor="#334155",
                        font=("Segoe UI", 10))

    def create_widgets(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        shell = tk.Frame(self.root, bg="#07141f")
        shell.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        shell.grid_rowconfigure(3, weight=1)
        shell.grid_columnconfigure(0, weight=1)

        header = tk.Frame(shell, bg="#0d1b2a", bd=0, highlightthickness=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title = tk.Label(header, text="THINKER TRADING BOT", bg="#0d1b2a", fg="#eaf3ff", font=("Segoe UI", 22, "bold"))
        title.grid(row=0, column=0, sticky="w", padx=(18, 0), pady=(18, 10))

        self.status_pill = tk.Label(header, text="Status: Stopped", bg="#1f2937", fg="#f8fafc", font=("Segoe UI", 10, "bold"), padx=14, pady=8, bd=0)
        self.status_pill.grid(row=0, column=1, sticky="e", padx=(0, 18), pady=(18, 10))

        control_bar = tk.Frame(shell, bg="#0d1b2a")
        control_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 14))
        control_bar.grid_columnconfigure(0, weight=1)

        control_left = tk.Frame(control_bar, bg="#0d1b2a")
        control_left.grid(row=0, column=0, sticky="ew")
        for column in range(5):
            control_left.grid_columnconfigure(column, weight=1)

        self.start_btn = ttk.Button(control_left, text="Start Bot", style="Accent.TButton", command=self.start_bot)
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(18, 10), pady=16)

        self.stop_btn = ttk.Button(control_left, text="Stop Bot", style="Danger.TButton", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=16)

        symbol_wrap = tk.Frame(control_left, bg="#0d1b2a")
        symbol_wrap.grid(row=0, column=2, sticky="ew", padx=(10, 8), pady=16)

        tk.Label(symbol_wrap, text="Symbol", bg="#0d1b2a", fg="#bcd3ff", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.symbol_var = tk.StringVar(value="EURUSD")
        symbol_entry = tk.Entry(symbol_wrap, textvariable=self.symbol_var, width=12, bg="#0f172a", fg="#f8fafc", insertbackground="#ffffff", bd=1, relief="flat")
        symbol_entry.pack(fill=tk.X, pady=(3, 0))

        self.buy_btn = ttk.Button(control_left, text="Buy (Long)", style="Success.TButton", command=lambda: self.manual_trade("LONG"), state=tk.DISABLED)
        self.buy_btn.grid(row=0, column=3, sticky="ew", padx=(12, 10), pady=16)

        self.sell_btn = ttk.Button(control_left, text="Sell (Short)", style="Danger.TButton", command=lambda: self.manual_trade("SHORT"), state=tk.DISABLED)
        self.sell_btn.grid(row=0, column=4, sticky="ew", padx=(0, 18), pady=16)

        metric_row = tk.Frame(shell, bg="#07141f")
        metric_row.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        metric_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.summary_labels = {}
        for index, label in enumerate(["Balance", "Exposure", "Signals", "Mode"]):
            card = tk.Frame(metric_row, bg="#0d1b2a", padx=18, pady=18)
            card.grid(row=0, column=index, sticky="nsew", padx=7)
            tk.Label(card, text=label, bg="#0d1b2a", fg="#9cb7d9", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            value = tk.StringVar(value="--")
            tk.Label(card, textvariable=value, bg="#0d1b2a", fg="#7ee7c5", font=("Segoe UI", 20, "bold")).pack(anchor="w", pady=(8, 0))
            self.summary_labels[label] = value

        dashboard = tk.Frame(shell, bg="#07141f")
        dashboard.grid(row=3, column=0, sticky="nsew")
        dashboard.grid_rowconfigure(0, weight=4)
        dashboard.grid_rowconfigure(1, weight=3)
        dashboard.grid_columnconfigure(0, weight=1)

        positions_frame = tk.Frame(dashboard, bg="#0d1b2a", padx=10, pady=10)
        positions_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 14))
        positions_frame.grid_rowconfigure(1, weight=1)
        positions_frame.grid_columnconfigure(0, weight=1)
        self.positions_frame = positions_frame
        tk.Label(positions_frame, text="Open Positions", bg="#0d1b2a", fg="#edf4ff", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 10))

        columns = ("Symbol", "Type", "Size", "Entry", "Current", "PnL")
        self.tree = ttk.Treeview(positions_frame, columns=columns, show="headings", height=9)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=140, minwidth=80, anchor="center", stretch=True)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        positions_frame.bind("<Configure>", self._resize_position_columns)

        log_frame = tk.Frame(dashboard, bg="#0d1b2a", padx=10, pady=10)
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        tk.Label(log_frame, text="System Logs", bg="#0d1b2a", fg="#edf4ff", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 10))

        self.log_text = tk.Text(log_frame, state="disabled", bg="#111827", fg="#d9f99d", font=("Consolas", 10), relief="flat", bd=0)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.root.after(1000, self.update_positions)

    def _resize_position_columns(self, event):
        """Keep the positions table readable as the dashboard is resized."""
        available_width = max(event.width - 36, 480)
        column_width = max(80, available_width // 6)
        for column in self.tree["columns"]:
            self.tree.column(column, width=column_width)

    def setup_logging(self):
        text_handler = TextHandler(self.log_text)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        text_handler.setFormatter(formatter)
        logging.getLogger().addHandler(text_handler)

    def init_bot(self):
        try:
            config = Config()
            data_fetcher = MarketDataFetcher(config)
            strategy_manager = StrategyManager(config)
            self.engine = TradingEngine(config, data_fetcher, strategy_manager)
            return True
        except Exception as exc:
            logging.error("Failed to initialize bot: %s", exc)
            return False

    def start_bot(self):
        if self.init_bot():
            self.status_pill.config(text="Status: Running", bg="#14532d", fg="#d1fae5")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.buy_btn.config(state=tk.NORMAL)
            self.sell_btn.config(state=tk.NORMAL)
            self.summary_labels["Mode"].set("Live")

            self.bot_thread = threading.Thread(target=self.engine.run, daemon=True)
            self.bot_thread.start()

    def stop_bot(self):
        if self.engine:
            logging.info("Stopping bot... Please wait for the current cycle to finish.")
            self.status_pill.config(text="Status: Stopping...", bg="#7c2d12", fg="#ffedd5")
            self.engine.running = False
            self.stop_btn.config(state=tk.DISABLED)

            def cleanup():
                if self.bot_thread:
                    self.bot_thread.join(timeout=30)
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.buy_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.sell_btn.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.summary_labels["Mode"].set("Idle"))
                self.root.after(0, lambda: self.status_pill.config(text="Status: Stopped", bg="#1f2937", fg="#f8fafc"))

            threading.Thread(target=cleanup, daemon=True).start()

    def manual_trade(self, position_type):
        if not self.engine or not getattr(self.engine, "running", False):
            logging.warning("Bot is not running. Cannot execute manual trade.")
            return

        symbol = self.symbol_var.get().strip().upper()
        if not symbol:
            logging.warning("Please enter a symbol.")
            return

        def execute():
            try:
                logging.info("Executing manual %s for %s...", position_type, symbol)
                quotes = self.engine.data_fetcher.get_forex_quotes([symbol])
                if symbol not in quotes:
                    logging.error("Could not fetch current price for %s", symbol)
                    return

                current_price = quotes[symbol]["mid"]
                signal = {"action": "BUY" if position_type == "LONG" else "SELL", "strength": 1.0, "manual": True}
                self.engine._open_position(symbol, current_price, position_type, signal)
            except Exception as exc:
                logging.error("Manual trade failed: %s", exc)

        threading.Thread(target=execute, daemon=True).start()

    def update_positions(self):
        if self.engine and self.engine.running:
            for item in self.tree.get_children():
                self.tree.delete(item)

            total_pnl = 0.0
            for symbol, pos in self.engine.positions.items():
                pnl = pos.get_pnl()
                total_pnl += pnl
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        pos.symbol,
                        pos.position_type,
                        f"{pos.size:.4f}",
                        f"${pos.entry_price:.4f}",
                        f"${pos.current_price:.4f}",
                        f"${pnl:.2f}",
                    ),
                )

            self.summary_labels["Exposure"].set(f"${total_pnl:.2f}")
            self.summary_labels["Balance"].set(f"${self.engine.account_balance:.2f}")
            self.summary_labels["Signals"].set(f"{len(self.engine.positions)} open")

        self.root.after(2000, self.update_positions)
