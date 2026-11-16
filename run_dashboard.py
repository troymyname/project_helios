# ------------------------------------------------------------------------------
# PROJECT NAME: 'Helios'
# AUTHOR:       Tonmoy Roy
# LICENSE:      GNU LGPLv3
# ------------------------------------------------------------------------------
# REFERENCES:
# [1] https://panel.holoviz.org/
# ------------------------------------------------------------------------------

"""Panel dashboard for generating and viewing ticker analysis reports."""

# import dependencies
import sys
sys.path.append("..")

import html
import logging
import panel as pn
import queue
import re
import subprocess
import sys
import threading
import time

from pathlib import Path

# import custom configs and utils
from config import ROOT_PATH
from utils.w2_generateDateStringYYYYMMDD import w2_generateDateStringYYYYMMDD

# Load Panel extensions (required for Panel to work)
pn.extension()

TICKER_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9.-]{0,14}")

# Set Panel theme and template
pn.config.background = "#f5f7f9"
pn.config.title = "Ticker Prices Dashboard"


# --- Tab: Inspect Stocks ---

def inspect_stocks_tab(terminal_output):
    """Create the 'Inspect Stocks' tab for generating and displaying ticker analysis."""
    ticker_input = pn.widgets.TextInput(
        name = "Ticker Symbol",
        placeholder = "Enter Ticker Symbol",
        sizing_mode = "stretch_width",
    )
    analyze_button = pn.widgets.Button(
        name = "Analyze", 
        button_type = "primary"
    )
    status_pane = pn.pane.Markdown("Enter a ticker symbol to begin.")
    report_pane = pn.pane.HTML(
        "<p>The analysis report will appear here.</p>",
        height = 900,
        sizing_mode = "stretch_width",
    )

    def analyze_ticker(_event):
        """Generate the Bokeh report for the entered ticker and display it."""
        del _event
        ticker = ticker_input.value.strip().upper()
        if not TICKER_PATTERN.fullmatch(ticker):
            status_pane.object = (
                "Enter a valid ticker symbol (letters, numbers, dots, or hyphens)."
            )
            return

        analyze_button.disabled = True
        status_pane.object = f"Generating analysis for **{ticker}**..."
        report_pane.object = "<p>Generating report...</p>"
        document = pn.state.curdoc
        if document is None:
            analyze_button.disabled = False
            status_pane.object = "Analysis requires an active Panel session."
            return

        report_path = (
            Path(ROOT_PATH)
            / "reports"
            / "analyses"
            / f"{w2_generateDateStringYYYYMMDD()}_{ticker}.html"
        )
        started_at_ns = time.time_ns()
        output_events = queue.Queue()
        output_lines = [f"Starting analysis for {ticker}..."]
        terminal_text = "\n".join(output_lines)
        terminal_output.object = f"<pre>{html.escape(terminal_text)}</pre>"

        def generate_report_process():
            try:
                command = [
                    sys.executable,
                    "-u",
                    "-c",
                    (
                        "import sys; "
                        "from reports.w1_generateAnalysisReport import "
                        "w1_generateAnalysisReport; "
                        "w1_generateAnalysisReport(ticker_str=sys.argv[1])"
                    ),
                    ticker,
                ]
                process = subprocess.Popen(
                    command,
                    cwd = ROOT_PATH,
                    stdout = subprocess.PIPE,
                    stderr = subprocess.STDOUT,
                    text = True,
                    bufsize = 1,
                )
                if process.stdout is not None:
                    for line in process.stdout:
                        output_events.put(("line", line.rstrip("\n")))
                return_code = process.wait()

                if return_code != 0:
                    output_events.put(
                        ("complete", None, f"Analysis process exited with status {return_code}.")
                    )
                    return

                if not report_path.is_file() or report_path.stat().st_mtime_ns < started_at_ns:
                    output_events.put(
                        (
                            "complete",
                            None,
                            "The script finished but did not create a new HTML report.",
                        )
                    )
                    return

                report_html = report_path.read_text(encoding = "utf-8")
                report_iframe = (
                    '<iframe '
                    f'srcdoc="{html.escape(report_html, quote = True)}" '
                    f'title="{html.escape(ticker, quote = True)} analysis report" '
                    'style="width:100%;height:900px;border:0"></iframe>'
                )
                output_events.put(
                    ("complete", report_iframe, f"Analysis report ready for **{ticker}**.")
                )
            except Exception as exc:
                logging.exception("Failed to generate analysis report for %s", ticker)
                output_events.put(
                    ("line", f"Dashboard error: {type(exc).__name__}: {exc}")
                )
                output_events.put(
                    ("complete", None, f"Analysis failed for **{ticker}**: {exc}")
                )

        def update_output():
            completed = False
            while True:
                try:
                    event = output_events.get_nowait()
                except queue.Empty:
                    break

                if event[0] == "line":
                    output_lines.append(event[1])
                    output_lines[:] = output_lines[-2000:]
                else:
                    _, report_iframe, message = event
                    status_pane.object = message
                    if report_iframe is not None:
                        report_pane.object = report_iframe
                    completed = True

            terminal_output.object = "\n".join(output_lines)
            if completed:
                analyze_button.disabled = False
                callback.stop()

        callback = pn.state.add_periodic_callback(update_output, period = 100)
        threading.Thread(
            target = generate_report_process, 
            daemon = True
        ).start()

    analyze_button.on_click(analyze_ticker)

    return pn.Column(
        pn.pane.Markdown("## Inspect Stocks"),
        pn.pane.Markdown(
            "Enter a ticker symbol and select **Analyze** to generate its report."
        ),
        pn.Row(ticker_input, sizing_mode = "stretch_width"),
        pn.Row(analyze_button),
        status_pane,
        report_pane,
        sizing_mode = "stretch_width",
    )


# --- Other Tabs (placeholders for future expansion) ---

def settings_tab():
    """Placeholder for future dashboard settings."""
    return pn.Column(
        pn.pane.Markdown("# Settings & Configuration", styles = {'font-size': '1.3em'}),
        pn.pane.Markdown("Dashboard settings will be added here."),
        sizing_mode = "stretch_width",
        margin = (0, 0, 10, 0),
    )


def about_tab():
    """About tab with dashboard information."""
    return pn.Column(
        pn.pane.Markdown("# About This Dashboard", styles = {'font-size': '1.3em'}),
        pn.pane.Markdown(
            """
            **Panel dashboard for ticker analysis**
            
            ## Features
            - Enter a ticker symbol in the Inspect Stocks tab
            - Select **Analyze** to fetch data and generate a Bokeh report
            - View the generated HTML report in the dashboard
            
            ## Data Source
            - Analysis is generated by `reports/w1_generateAnalysisReport.py`
            - Historical data is retrieved through the Helios Interactive Brokers API wrappers
            - The HTML report is saved under `reports/analyses/`
            
            ## Technical Details
            - Built with [Panel](https://panel.holoviz.org/) (v1.9.4)
            - Bokeh HTML is embedded in the Inspect Stocks tab after generation
            
            ## Usage
            1. Run: `python dashboard.py`
            2. Enter a ticker symbol in Inspect Stocks
            3. Click **Analyze** and wait for the report to load
            
            ## Requirements
            - Python 3.8+
            - Panel and Bokeh packages
            """,
            styles = {'font-size': '13px', 'line-height': '1.5'}
        ),
        sizing_mode = "stretch_width",
        margin = (0, 0, 10, 0),
    )


# --- Main Application ---

def main():
    """Create and show the Panel dashboard."""

    terminal_output = pn.pane.HTML(
        "<pre>Script output will appear here.</pre>",
        height = 300,
        sizing_mode = "stretch_width",
        styles = {
            "overflow-y": "auto",
            "white-space": "pre-wrap",
            "font-family": "monospace",
        },
    )
    terminal_section = pn.Accordion(
        ("Terminal Output", terminal_output),
        active = [],
        sizing_mode = "stretch_width",
    )

    # Create tabs with sidebar location
    tabs = pn.Tabs(
        ("Inspect Stocks", inspect_stocks_tab(terminal_output)),
        ("Settings", settings_tab()),
        ("About", about_tab()),
        # location = "sidebar",  # Sidebar tab location
        sizing_mode = "stretch_width",
        margin = (0, 0, 10, 0),
    )
    
    # Create main layout
    layout = pn.Column(
        tabs,
        terminal_section,
        sizing_mode = "stretch_width",
        margin = 10,
    )
    
    # Show the dashboard
    # In VS Code, this will open in the integrated browser
    # In standalone mode, it opens a browser window
    layout.show()


if __name__ == "__main__":
    main()