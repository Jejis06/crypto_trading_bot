import sys
import json
import os
from datetime import datetime, timedelta
from threading import Thread, Lock
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTreeWidget, QTreeWidgetItem, QTextEdit, 
                            QGroupBox, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QMutex
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QLineSeries, QValueAxis
from bot_manager import BotManager
from portfolio_bot import PortfolioBot
from credentials_manager import CredentialsManager
from bot_loader import BotLoader
import pyqtgraph as pg
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class UpdateSignals(QObject):
    price_updated = pyqtSignal(str, str)  # symbol, price
    trade_updated = pyqtSignal(str, str)  # symbol, trade_info
    portfolio_updated = pyqtSignal(dict)  # portfolio data
    bot_status_updated = pyqtSignal(str, dict)  # symbol, status

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        layout.addWidget(self.plot_widget)
        
        # Initialize data
        self.times = []
        self.prices = []
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color='b', width=2))
        
        self.setLayout(layout)
        
    def update_data(self, price, max_points=100):
        current_time = datetime.now().timestamp()
        
        self.times.append(current_time)
        self.prices.append(price)
        
        # Keep only last max_points
        if len(self.times) > max_points:
            self.times = self.times[-max_points:]
            self.prices = self.prices[-max_points:]
        
        self.curve.setData(x=self.times, y=self.prices)
        
class BotDetailDialog(QDialog):
    def __init__(self, symbol, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.setWindowTitle(f"{symbol} Details")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Add price chart
        self.price_chart = ChartWidget()
        layout.addWidget(self.price_chart)
        
        # Add trade history table
        self.trade_table = QTableWidget()
        self.trade_table.setColumnCount(6)
        self.trade_table.setHorizontalHeaderLabels([
            "Time", "Type", "Price", "Quantity", "Value", "P/L"
        ])
        layout.addWidget(self.trade_table)
        
        self.setLayout(layout)
        
    def update_price(self, price):
        self.price_chart.update_data(float(price))
        
    def add_trade(self, trade):
        row = self.trade_table.rowCount()
        self.trade_table.insertRow(row)
        
        self.trade_table.setItem(row, 0, QTableWidgetItem(trade['time'].strftime("%Y-%m-%d %H:%M:%S")))
        self.trade_table.setItem(row, 1, QTableWidgetItem(trade['type']))
        self.trade_table.setItem(row, 2, QTableWidgetItem(f"${trade['price']:.8f}"))
        self.trade_table.setItem(row, 3, QTableWidgetItem(f"{trade['quantity']:.8f}"))
        self.trade_table.setItem(row, 4, QTableWidgetItem(f"${trade['value']:.2f}"))
        
        if 'profit_loss' in trade:
            pl_item = QTableWidgetItem(f"${trade['profit_loss']:.2f}")
            pl_item.setForeground(Qt.green if trade['profit_loss'] > 0 else Qt.red)
            self.trade_table.setItem(row, 5, pl_item)
        else:
            self.trade_table.setItem(row, 5, QTableWidgetItem("-"))

class TradingBotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crypto Trading Bot")
        self.setGeometry(100, 100, 1200, 800)
        
        self.bot_manager = None
        self.portfolio_bot = None
        self.credentials_manager = CredentialsManager()
        self.update_signals = UpdateSignals()
        self.price_update_timer = QTimer()
        self.price_update_timer.timeout.connect(self._update_data)
        self.price_update_timer.setInterval(5000)  # Update every 5 seconds
        
        self.portfolio_value_history = []
        self.update_lock = Lock()
        self.symbol_items = {}  # Cache for tree widget items
        self.bot_dialogs = {}
        
        self._create_gui_elements()
        self._setup_logging()
        self._connect_signals()
        self._load_saved_credentials()

    def _create_gui_elements(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create connection section
        self._create_connection_section(main_layout)
        
        # Create tabbed view for different sections
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Create bot status tab
        bot_status_widget = QWidget()
        bot_status_layout = QVBoxLayout(bot_status_widget)
        self._create_bot_status_section(bot_status_layout)
        tab_widget.addTab(bot_status_widget, "Bot Status")
        
        # Create portfolio tab
        portfolio_widget = QWidget()
        portfolio_layout = QVBoxLayout(portfolio_widget)
        self._create_portfolio_section(portfolio_layout)
        tab_widget.addTab(portfolio_widget, "Portfolio")
        
        # Create log section
        self._create_log_section(main_layout)

    def _create_connection_section(self, parent_layout):
        connection_group = QGroupBox("API Credentials")
        layout = QHBoxLayout()
        
        # API Key
        key_layout = QVBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        key_layout.addWidget(self.api_key_input)
        layout.addLayout(key_layout)
        
        # API Secret
        secret_layout = QVBoxLayout()
        secret_layout.addWidget(QLabel("API Secret:"))
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        secret_layout.addWidget(self.api_secret_input)
        layout.addLayout(secret_layout)
        
        # Connect button
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self._connect)
        layout.addWidget(connect_btn)
        
        connection_group.setLayout(layout)
        parent_layout.addWidget(connection_group)

    def _create_bot_status_section(self, parent_layout):
        status_group = QGroupBox("Bot Status")
        layout = QVBoxLayout()
        
        # Create tree widget for bot status
        self.status_tree = QTreeWidget()
        self.status_tree.setHeaderLabels([
            "Symbol", "Strategy", "Current Price", "Position Size", 
            "Entry Price", "Current Value", "P/L", "P/L %", "Status"
        ])
        self.status_tree.setColumnCount(9)
        self.status_tree.setAlternatingRowColors(True)
        layout.addWidget(self.status_tree)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        start_btn = QPushButton("Start All")
        start_btn.clicked.connect(self._start_all_bots)
        stop_btn = QPushButton("Stop All")
        stop_btn.clicked.connect(self._stop_all_bots)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_status)
        
        btn_layout.addWidget(start_btn)
        btn_layout.addWidget(stop_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        status_group.setLayout(layout)
        parent_layout.addWidget(status_group)

    def _create_portfolio_section(self, parent_layout):
        portfolio_group = QGroupBox("Portfolio")
        layout = QVBoxLayout()
        
        # Portfolio chart
        self.portfolio_chart = ChartWidget()
        layout.addWidget(self.portfolio_chart)
        
        # Portfolio stats
        stats_layout = QHBoxLayout()
        self.total_value_label = QLabel("Total Value: $0.00")
        self.daily_pl_label = QLabel("24h P/L: $0.00 (0.00%)")
        stats_layout.addWidget(self.total_value_label)
        stats_layout.addWidget(self.daily_pl_label)
        layout.addLayout(stats_layout)
        
        portfolio_group.setLayout(layout)
        parent_layout.addWidget(portfolio_group)
        
        # Charts layout
        charts_layout = QHBoxLayout()
        
        # Portfolio composition pie chart
        self.portfolio_pie_chart = QChart()
        self.portfolio_pie_chart.setTitle("Portfolio Composition")
        pie_view = QChartView(self.portfolio_pie_chart)
        pie_view.setMinimumHeight(300)
        charts_layout.addWidget(pie_view)
        
        # Portfolio value line chart
        self.portfolio_line_chart = QChart()
        self.portfolio_line_chart.setTitle("Portfolio Value Over Time")
        line_view = QChartView(self.portfolio_line_chart)
        line_view.setMinimumHeight(300)
        charts_layout.addWidget(line_view)
        
        parent_layout.addLayout(charts_layout)
        
        # Holdings table
        self.holdings_tree = QTreeWidget()
        self.holdings_tree.setHeaderLabels(["Symbol", "Quantity", "Current Price", "Value", "Profit/Loss"])
        self.holdings_tree.setAlternatingRowColors(True)
        parent_layout.addWidget(self.holdings_tree)

    def _create_log_section(self, parent_layout):
        log_group = QGroupBox("Logs")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        log_group.setLayout(layout)
        parent_layout.addWidget(log_group)

    def _setup_logging(self):
        """Set up logging to the GUI's text widget."""
        class QTextEditLogger(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                self.text_widget.append(f"{msg}")
        
        # Create and add the custom handler
        handler = QTextEditLogger(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to the root logger so we capture all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
        # Make sure we capture all logs
        root_logger.setLevel(logging.INFO)

    def _connect_signals(self):
        """Connect update signals to UI update methods."""
        self.update_signals.price_updated.connect(self._update_price_in_tree)
        self.update_signals.trade_updated.connect(self._update_trade_in_tree)
        self.update_signals.portfolio_updated.connect(self._update_portfolio_display)
        self.update_signals.bot_status_updated.connect(self._update_bot_status)
    
    def _load_saved_credentials(self):
        """Load saved API credentials if they exist."""
        api_key, api_secret = self.credentials_manager.load_credentials()
        if api_key and api_secret:
            self.api_key_input.setText(api_key)
            self.api_secret_input.setText(api_secret)
            self._connect()

    def _update_price_in_tree(self, symbol, price):
        """Update price in tree widget (called in GUI thread)."""
        if symbol in self.symbol_items:
            self.symbol_items[symbol].setText(2, price)
    
    def _update_trade_in_tree(self, symbol, trade_info):
        """Update trade info in tree widget (called in GUI thread)."""
        if symbol in self.symbol_items:
            self.symbol_items[symbol].setText(3, trade_info)
    
    def _update_portfolio_display(self, portfolio_data):
        """Update portfolio display with new data."""
        total_value = portfolio_data['total_value']
        self.total_value_label.setText(f"Total Value: ${total_value:.2f}")
        
        if 'daily_pl' in portfolio_data:
            daily_pl = portfolio_data['daily_pl']
            daily_pl_pct = portfolio_data['daily_pl_percent']
            self.daily_pl_label.setText(f"24h P/L: ${daily_pl:.2f} ({daily_pl_pct:.2f}%)")
            self.daily_pl_label.setStyleSheet(
                "color: green;" if daily_pl > 0 else "color: red;" if daily_pl < 0 else ""
            )
        
        self.portfolio_chart.update_data(total_value)
        
        # Update holdings table
        self.holdings_tree.clear()
        for holding in portfolio_data['holdings']:
            item = QTreeWidgetItem(self.holdings_tree)
            item.setText(0, holding['symbol'])
            item.setText(1, f"{holding['quantity']:.8f}")
            item.setText(2, f"${holding['current_price']:.2f}")
            item.setText(3, f"${holding['value']:.2f}")
            item.setText(4, f"${holding['profit_loss']:.2f}")
            
            if holding['profit_loss'] > 0:
                item.setForeground(4, Qt.green)
            elif holding['profit_loss'] < 0:
                item.setForeground(4, Qt.red)

    def _connect(self):
        api_key = self.api_key_input.text().strip()
        api_secret = self.api_secret_input.text().strip()
        
        if not api_key or not api_secret:
            QMessageBox.critical(self, "Error", "Please enter both API key and secret")
            return
        
        try:
            logger.info("Creating BotManager instance...")
            self.bot_manager = BotManager(api_key, api_secret)
            self.credentials_manager.save_credentials(api_key, api_secret)
            
            # Use bot loader to load all bots
            logger.info("Creating BotLoader instance...")
            bot_loader = BotLoader(self.bot_manager.client)
            
            logger.info("Loading bot configurations...")
            trading_bots, self.portfolio_bot = bot_loader.load_all_bots()
            logger.info(f"Loaded {len(trading_bots)} trading bots and {'a' if self.portfolio_bot else 'no'} portfolio bot")
            
            if not trading_bots and not self.portfolio_bot:
                raise ValueError("No valid bots were loaded. Please check your configuration files.")
            
            # Add trading bots to manager
            for bot in trading_bots:
                try:
                    self.bot_manager.add_bot(bot)
                    self._add_bot_to_tree(bot.config)
                    logger.info(f"Added bot to manager: {bot.config.get('name', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Failed to add bot to manager: {str(e)}", exc_info=True)
            
            QMessageBox.information(self, "Success", "Connected to Binance testnet successfully!")
            self.price_update_timer.start()
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to connect: {str(e)}\n\nDetails:\n{traceback.format_exc()}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Error", error_msg)

    def _add_bot_to_tree(self, config):
        """Add bot to tree widget and cache the item."""
        item = QTreeWidgetItem(self.status_tree)
        symbol = config.get('symbol', 'Unknown')
        item.setText(0, symbol)
        item.setText(1, config.get('strategy', 'simple'))
        item.setText(2, "Loading...")  # Current Price
        item.setText(3, "No Position")  # Position Size
        item.setText(4, "-")  # Entry Price
        item.setText(5, "-")  # Current Value
        item.setText(6, "-")  # P/L
        item.setText(7, "-")  # P/L %
        item.setText(8, "Stopped")  # Status
        
        self.symbol_items[symbol] = item
        
        # Adjust column widths
        for i in range(9):
            self.status_tree.resizeColumnToContents(i)

    def _update_bot_status(self, symbol, status):
        """Update bot status in tree widget."""
        if symbol not in self.symbol_items:
            return
            
        item = self.symbol_items[symbol]
        item.setText(2, f"${status['current_price']:.8f}")
        
        if status.get('position'):
            pos = status['position']
            item.setText(3, f"{pos['quantity']:.8f}")
            item.setText(4, f"${pos['entry_price']:.8f}")
            item.setText(5, f"${pos['current_value']:.2f}")
            item.setText(6, f"${pos['unrealized_pl']:.2f}")
            item.setText(7, f"{pos['unrealized_pl_percent']:.2f}%")
            
            # Set color based on P/L
            if pos['unrealized_pl'] > 0:
                item.setForeground(6, Qt.green)
                item.setForeground(7, Qt.green)
            elif pos['unrealized_pl'] < 0:
                item.setForeground(6, Qt.red)
                item.setForeground(7, Qt.red)
        else:
            item.setText(3, "No Position")
            item.setText(4, "-")
            item.setText(5, "-")
            item.setText(6, "-")
            item.setText(7, "-")
            
        item.setText(8, "Running" if status['is_running'] else "Stopped")

    def _update_data(self):
        """Update all data in a separate thread."""
        if not self.bot_manager:
            return
        
        Thread(target=self._fetch_updates, daemon=True).start()

    def _fetch_updates(self):
        """Fetch updates in background thread."""
        with self.update_lock:
            try:
                # Update trading bot data
                for symbol, item in self.symbol_items.items():
                    try:
                        # Get bot status
                        bot = next(b for b in self.bot_manager.bots if b.symbol == symbol)
                        status = bot.get_status()
                        if status:
                            self.update_signals.bot_status_updated.emit(symbol, status)
                    except Exception as e:
                        logger.error(f"Error updating {symbol}: {str(e)}")
                
                # Update portfolio data
                if self.portfolio_bot:
                    portfolio_data = self.portfolio_bot.get_portfolio_value()
                    self.update_signals.portfolio_updated.emit(portfolio_data)
                    self.portfolio_bot.analyze_and_trade()
                    
            except Exception as e:
                logger.error(f"Error in update thread: {str(e)}")

    def _update_portfolio_charts(self, portfolio_data):
        if not self.portfolio_bot:
            return
        
        # Update pie chart
        self.portfolio_pie_chart.removeAllSeries()
        if portfolio_data['holdings']:
            series = QPieSeries()
            for holding in portfolio_data['holdings']:
                series.append(holding['symbol'], holding['value'])
            self.portfolio_pie_chart.addSeries(series)
        
        # Update line chart
        self.portfolio_value_history.append(portfolio_data['total_value'])
        if len(self.portfolio_value_history) > 50:  # Keep last 50 points
            self.portfolio_value_history = self.portfolio_value_history[-50:]
        
        self.portfolio_line_chart.removeAllSeries()
        series = QLineSeries()
        for i, value in enumerate(self.portfolio_value_history):
            series.append(i, value)
        self.portfolio_line_chart.addSeries(series)
        
        # Add axes if not already present
        if not self.portfolio_line_chart.axes():
            axis_x = QValueAxis()
            axis_y = QValueAxis()
            self.portfolio_line_chart.addAxis(axis_x, Qt.AlignBottom)
            self.portfolio_line_chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

    def _start_all_bots(self):
        if not self.bot_manager:
            QMessageBox.critical(self, "Error", "Please connect to Binance first")
            return
        
        self.bot_manager.start()
        root = self.status_tree.invisibleRootItem()
        for i in range(root.childCount()):
            root.child(i).setText(8, "Running")

    def _stop_all_bots(self):
        if not self.bot_manager:
            return
        
        self.bot_manager.stop()
        root = self.status_tree.invisibleRootItem()
        for i in range(root.childCount()):
            root.child(i).setText(8, "Stopped")

    def _refresh_status(self):
        if not self.bot_manager:
            return
        self._update_data()

    def _show_bot_details(self, item):
        """Show detailed bot information dialog."""
        symbol = item.text(0)
        if symbol not in self.bot_dialogs:
            dialog = BotDetailDialog(symbol, self)
            self.bot_dialogs[symbol] = dialog
        
        dialog = self.bot_dialogs[symbol]
        if not dialog.isVisible():
            dialog.show()

    def closeEvent(self, event):
        """Handle application shutdown."""
        if self.bot_manager:
            self.bot_manager.stop()
        self.price_update_timer.stop()
        for dialog in self.bot_dialogs.values():
            dialog.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = TradingBotGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 