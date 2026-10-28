"""The Tkinter window: statistics, data table, charts, forecast and report."""
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import analysis
import charts
import data_loader
import forecast
import report

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"

NAVY = "#1F3A5F"
TABS = ["Data Table", "Price & Volume", "Returns & Volatility",
        "Compare Stocks", "Risk & Return", "Forecast", "Report"]


class QuantPilotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QuantPilot - Stock Market Data Analytics System")
        self.root.geometry("1180x780")
        self.stocks = {}
        self.forecast_result = None
        self.source_text = tk.StringVar(value="No data loaded")
        self.selected = tk.StringVar()
        self.stat_vars = {}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=22)
        style.configure("TNotebook.Tab", padding=(12, 6))

        self.build_header()
        self.build_statistics()
        self.build_tabs()
        tk.Label(self.root, text="Note: " + report.DISCLAIMER, fg="#555555",
                 font=("Segoe UI", 9, "italic")).pack(side="bottom", pady=4)
        self.load_sample()

    # ------------------------------------------------------------ layout
    def build_header(self):
        header = tk.Frame(self.root, bg=NAVY)
        header.pack(fill="x")
        tk.Label(header, text="QuantPilot", bg=NAVY, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=14, pady=8)
        tk.Label(header, textvariable=self.source_text, bg=NAVY, fg="#C9D6EA",
                 font=("Segoe UI", 10)).pack(side="left", padx=6)
        ttk.Button(header, text="Generate Report", command=self.generate_report).pack(side="right", padx=8)
        ttk.Button(header, text="Load Sample Data", command=self.load_sample).pack(side="right", padx=4)
        ttk.Button(header, text="Upload CSV Files", command=self.upload_files).pack(side="right", padx=4)

    def build_statistics(self):
        box = ttk.LabelFrame(self.root, text="Summary Statistics")
        box.pack(fill="x", padx=10, pady=(8, 4))
        top = tk.Frame(box)
        top.grid(row=0, column=0, columnspan=5, sticky="w", padx=8, pady=4)
        tk.Label(top, text="Stock:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.combo = ttk.Combobox(top, textvariable=self.selected, state="readonly", width=14)
        self.combo.pack(side="left", padx=6)
        self.combo.bind("<<ComboboxSelected>>", lambda event: self.update_selected())

        names = ["Last Close", "Total Return %", "Annual Return %", "Annual Volatility %", "Sharpe Ratio",
                 "Max Drawdown %", "VaR 95% (1-day) %", "Best Day %", "Worst Day %", "Average Volume"]
        for i, name in enumerate(names):
            var = tk.StringVar(value="-")
            self.stat_vars[name] = var
            cell = tk.Frame(box)
            cell.grid(row=1 + i // 5, column=i % 5, sticky="w", padx=14, pady=3)
            tk.Label(cell, text=name, fg="#555555", font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(cell, textvariable=var, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        for column in range(5):
            box.columnconfigure(column, weight=1)

    def build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=6)
        self.frames = {}
        for name in TABS:
            frame = tk.Frame(self.notebook, bg="white")
            self.notebook.add(frame, text=name)
            self.frames[name] = frame

        columns = ("Date", "Open", "High", "Low", "Close", "Volume", "Daily Return %", "20-day Avg")
        self.table = ttk.Treeview(self.frames["Data Table"], columns=columns, show="headings")
        for column in columns:
            self.table.heading(column, text=column)
            self.table.column(column, width=120, anchor="center")
        scroll = ttk.Scrollbar(self.frames["Data Table"], orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)

        self.report_text = tk.Text(self.frames["Report"], font=("Consolas", 10), wrap="none")
        self.report_text.pack(fill="both", expand=True)
        self.report_text.insert("1.0", "Press 'Generate Report' to create the analytical report.")

        self.forecast_label = tk.Label(self.frames["Forecast"], bg="white", justify="left",
                                       font=("Segoe UI", 10), anchor="w")
        self.forecast_label.pack(fill="x", padx=10, pady=(6, 0))
        self.forecast_chart_frame = tk.Frame(self.frames["Forecast"], bg="white")
        self.forecast_chart_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------ loading
    def upload_files(self):
        paths = filedialog.askopenfilenames(title="Choose stock CSV files",
                                            filetypes=[("CSV files", "*.csv")])
        if paths:
            self.load_files(paths, "Uploaded files")

    def load_sample(self):
        self.load_files(sorted(SAMPLE_DIR.glob("*.csv")), "Sample data (simulated)")

    def load_files(self, paths, source):
        stocks, errors = data_loader.load_many(paths)
        if errors:
            messagebox.showerror("Could not load some files", "\n".join(errors))
        if not stocks:
            return                                  # keep the old data on the screen
        self.stocks = stocks
        self.source_text.set(f"{source}: {', '.join(stocks)}")
        self.combo["values"] = list(stocks)
        self.selected.set(next(iter(stocks)))
        self.update_all()

    # ------------------------------------------------------------ refresh
    def show_figure(self, parent, fig):
        for child in parent.winfo_children():
            child.destroy()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_all(self):
        self.show_figure(self.frames["Compare Stocks"], charts.create_comparison_chart(self.stocks))
        self.show_figure(self.frames["Risk & Return"], charts.create_risk_return_chart(self.stocks))
        self.update_selected()

    def update_selected(self):
        ticker = self.selected.get()
        df = self.stocks[ticker]
        self.update_statistics(df)
        self.update_table(df)
        self.show_figure(self.frames["Price & Volume"], charts.create_price_volume_chart(df, ticker))
        self.show_figure(self.frames["Returns & Volatility"], charts.create_returns_chart(df, ticker))
        self.update_forecast(df, ticker)

    def update_statistics(self, df):
        summary = analysis.risk_summary(df)
        for name, value in summary.items():
            if name == "Average Volume":
                text = f"{value:,.0f}"
            elif name in ("Last Close", "Sharpe Ratio"):
                text = f"{value:.2f}"
            else:
                text = f"{value:.2f}%"
            self.stat_vars[name].set(text)

    def update_table(self, df):
        self.table.delete(*self.table.get_children())
        data = analysis.add_indicators(df)
        for _, row in data.iloc[::-1].iterrows():              # newest day first
            ret = "-" if row["Daily_Return"] != row["Daily_Return"] else f"{row['Daily_Return'] * 100:.2f}"
            sma = "-" if row["SMA_20"] != row["SMA_20"] else f"{row['SMA_20']:.2f}"
            self.table.insert("", "end", values=(
                f"{row['Date']:%Y-%m-%d}", f"{row['Open']:.2f}", f"{row['High']:.2f}",
                f"{row['Low']:.2f}", f"{row['Close']:.2f}", f"{int(row['Volume']):,}", ret, sma))

    def update_forecast(self, df, ticker):
        try:
            self.forecast_result = forecast.run_forecast(df)
        except Exception as error:
            self.forecast_result = None
            self.forecast_label.config(text=f"Forecast not available: {error}")
            return
        r = self.forecast_result
        self.forecast_label.config(text=(
            f"Linear Regression, one day ahead. Test MAE {r['model']['MAE']:.2f}, RMSE {r['model']['RMSE']:.2f}, "
            f"MAPE {r['model']['MAPE %']:.2f}%, R2 {r['model']['R2']:.3f}.  "
            f"Baseline (tomorrow = today) MAE {r['naive']['MAE']:.2f}.  "
            f"Direction correct on {r['directional_accuracy']:.1f}% of days.\n"
            f"Estimate for the next trading day: {r['next_day']:.2f} "
            f"({r['next_day_change %']:+.2f}% from the last close).  {report.DISCLAIMER}"))
        self.show_figure(self.forecast_chart_frame, charts.create_forecast_chart(r, ticker))

    # ------------------------------------------------------------ report
    def generate_report(self, notify=True):
        if not self.stocks or self.forecast_result is None:
            messagebox.showwarning("No data", "Load a valid stock file first.")
            return None
        text = report.build_report(self.stocks, self.selected.get(), self.forecast_result)
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", text)
        path = report.save_report(text, REPORT_DIR / f"QuantPilot_Report_{datetime.now():%Y-%m-%d}.txt")
        self.notebook.select(self.frames["Report"])
        if notify:
            messagebox.showinfo("Report saved", f"The report was saved as:\n{path}")
        return path
