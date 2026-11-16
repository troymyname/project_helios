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
import json
import logging
import nbformat
import panel as pn
import plotly.io as pio
import queue
import re
import subprocess
import sys
import threading
import time
import uuid

from nbclient import NotebookClient
from pathlib import Path

# import custom configs and utils
from config import ROOT_PATH
from utils.w2_generateDateStringYYYYMMDD import w2_generateDateStringYYYYMMDD

# load Panel extensions (required for Panel to work)
pn.extension()

TICKER_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9.-]{0,14}")
SEC_COMPANY_NOTEBOOK_PATH = (
    Path(ROOT_PATH) / "reports" / "notebooks" / "generateSECCompanyStatusReport.ipynb"
)
PRECIOUS_METALS_NOTEBOOK_PATH = (
    Path(ROOT_PATH)
    / "reports"
    / "notebooks"
    / "generatePreciousMetalsStatusReport.ipynb"
)

# set Panel theme and template
pn.config.background = "#f5f7f9"
pn.config.title = "Ticker Prices Dashboard"


def generate_notebook_plotly_report(
    notebook_path,
    output_html_path,
    report_title,
    ticker = None,
    ticker_variable = None,
    create_raw_directory = False,
):
    """Execute a notebook and export its Plotly figures as an HTML report."""
    notebook_path = Path(notebook_path)
    output_html_path = Path(output_html_path)
    notebook = nbformat.read(notebook_path, as_version = 4)

    # if a ticker variable is specified, replace its assignment in the notebook with the provided ticker value.
    ticker_cell_found = ticker_variable is None
    javascript_cell_prefix = "%%javascript"
    executable_cells = []
    for cell in notebook.cells:
        if cell.cell_type == "code" and cell.source.lstrip().startswith(
            javascript_cell_prefix
        ):
            continue
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
            if ticker_variable and re.search(
                rf"(?m)^\s*{re.escape(ticker_variable)}\s*=", cell.source
            ):
                cell.source = re.sub(
                    rf"(?m)^\s*{re.escape(ticker_variable)}\s*=.*$",
                    f"{ticker_variable} = {ticker!r}",
                    cell.source,
                    count=1,
                )
                ticker_cell_found = True
        executable_cells.append(cell)

    # if a ticker variable was specified but not found in the notebook, raise an error
    if not ticker_cell_found:
        raise ValueError(
            f"No {ticker_variable} assignment found in {notebook_path}."
        )
    notebook.cells = executable_cells

    if create_raw_directory:
        (notebook_path.parent / "raw").mkdir(parents = True, exist_ok = True)

    def stream_cell_output(cell, cell_index):
        print(f"Completed notebook cell {cell_index + 1}.", flush = True)
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                print(output.text, end="", flush=True)
            elif output.output_type == "error":
                print("\n".join(output.traceback), flush=True)

    notebook_client = NotebookClient(
        notebook,
        timeout = 1800,
        kernel_name = notebook.metadata.get("kernelspec", {}).get(
            "name", "python3"
        ),
        on_cell_complete = stream_cell_output,
    )
    executed_notebook = notebook_client.execute(cwd=str(notebook_path.parent))

    plotly_outputs = []
    for cell in executed_notebook.cells:
        for output in cell.get("outputs", []):
            figure_json = output.get("data", {}).get(
                "application/vnd.plotly.v1+json"
            )
            if figure_json is not None:
                plotly_outputs.append(figure_json)

    if not plotly_outputs:
        raise RuntimeError(
            f"The notebook produced no Plotly figures: {notebook_path}."
        )

    figure_html = []
    for index, figure_json in enumerate(plotly_outputs):
        figure_spec = {
            key: figure_json[key]
            for key in ("data", "layout", "frames")
            if key in figure_json
        }
        figure = pio.from_json(json.dumps(figure_spec))
        figure_html.append(
            pio.to_html(
                figure,
                full_html = False,
                include_plotlyjs = "cdn" if index == 0 else False,
            )
        )

    output_html_path.parent.mkdir(parents = True, exist_ok = True)
    output_html_path.write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(report_title)}</title>"
        "<style>body{font-family:Arial,sans-serif;margin:1rem}"
        ".plot{width:100%;margin-bottom:2rem}</style></head><body>"
        f"<h1>{html.escape(report_title)}</h1>"
        + "".join(f'<section class="plot">{plot}</section>' for plot in figure_html)
        + "</body></html>",
        encoding="utf-8",
    )
    print(
        f"Created report with {len(plotly_outputs)} Plotly figures: "
        f"{output_html_path}",
        flush=True,
    )


def generate_sec_company_report(ticker, output_html_path, notebook_path = None):
    """Execute the SEC status notebook for a ticker and export its Plotly figures."""
    generate_notebook_plotly_report(
        notebook_path or SEC_COMPANY_NOTEBOOK_PATH,
        output_html_path,
        f"SEC Company Status: {ticker}",
        ticker=ticker,
        ticker_variable="__tickSymb",
    )


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
        pn.pane.Markdown("## Stocks"),
        pn.pane.Markdown(
            "Enter a ticker symbol and select **Analyze** to generate its report."
        ),
        pn.Row(ticker_input, sizing_mode = "stretch_width"),
        pn.Row(analyze_button),
        status_pane,
        report_pane,
        sizing_mode = "stretch_width",
    )


def inspect_companies_tab(terminal_output):
    """Run the SEC company-status notebook for a ticker and show its report."""
    ticker_input = pn.widgets.TextInput(
        name = "Ticker Symbol",
        placeholder = "Enter Ticker Symbol",
        sizing_mode = "stretch_width",
    )
    analyze_button = pn.widgets.Button(name = "Analyze", button_type = "primary")
    status_pane = pn.pane.Markdown("Enter a ticker symbol to begin.")
    report_pane = pn.pane.HTML(
        "<p>The SEC company report will appear here.</p>",
        height = 900,
        sizing_mode = "stretch_width",
    )

    def analyze_company(_event):
        del _event
        ticker = ticker_input.value.strip().upper()
        if not TICKER_PATTERN.fullmatch(ticker):
            status_pane.object = (
                "Enter a valid ticker symbol (letters, numbers, dots, or hyphens)."
            )
            return

        document = pn.state.curdoc
        if document is None:
            status_pane.object = "Analysis requires an active Panel session."
            return

        analyze_button.disabled = True
        status_pane.object = f"Running SEC company status notebook for **{ticker}**..."
        report_pane.object = "<p>Executing notebook and generating report...</p>"

        report_path = (
            Path(ROOT_PATH)
            / "reports"
            / "analyses"
            / f"{w2_generateDateStringYYYYMMDD()}_{ticker}_SEC_{uuid.uuid4().hex[:8]}.html"
        )
        output_events = queue.Queue()
        output_lines = [f"Starting SEC company report for {ticker}..."]
        terminal_output.object = f"<pre>{html.escape(output_lines[0])}</pre>"

        def execute_notebook():
            try:
                command = [
                    sys.executable,
                    "-u",
                    "-c",
                    (
                        "import sys; "
                        "from launch_dashboard import generate_sec_company_report; "
                        "generate_sec_company_report(sys.argv[1], sys.argv[2])"
                    ),
                    ticker,
                    str(report_path),
                ]
                process = subprocess.Popen(
                    command,
                    cwd=ROOT_PATH,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                if process.stdout is not None:
                    for line in process.stdout:
                        output_events.put(("line", line.rstrip("\n")))
                return_code = process.wait()
                if return_code != 0:
                    output_events.put(
                        (
                            "complete",
                            None,
                            f"SEC company report failed (process exited with status {return_code}).",
                        )
                    )
                    return

                if not report_path.is_file():
                    output_events.put(
                        ("complete", None, "Notebook completed without creating a report.")
                    )
                    return

                report_html = report_path.read_text(encoding="utf-8")
                report_iframe = (
                    '<iframe '
                    f'srcdoc="{html.escape(report_html, quote=True)}" '
                    f'title="{html.escape(ticker, quote=True)} SEC company report" '
                    'style="width:100%;height:900px;border:0"></iframe>'
                )
                output_events.put(
                    ("complete", report_iframe, f"SEC company report ready for **{ticker}**.")
                )
            except Exception as exc:
                logging.exception(
                    "Failed to execute SEC company status notebook for %s", ticker
                )
                output_events.put(
                    ("line", f"Dashboard error: {type(exc).__name__}: {exc}")
                )
                output_events.put(
                    ("complete", None, f"SEC company report failed for **{ticker}**: {exc}")
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

            terminal_output.object = (
                f"<pre>{html.escape(chr(10).join(output_lines))}</pre>"
            )
            if completed:
                analyze_button.disabled = False
                callback.stop()

        callback = pn.state.add_periodic_callback(update_output, period=100)
        threading.Thread(target=execute_notebook, daemon=True).start()

    analyze_button.on_click(analyze_company)

    return pn.Column(
        pn.pane.Markdown("## Company Performance"),
        pn.pane.Markdown(
            "Enter a ticker and select **Analyze** to execute the SEC company status notebook."
        ),
        pn.Row(ticker_input, analyze_button, sizing_mode = "stretch_width"),
        status_pane,
        report_pane,
        sizing_mode = "stretch_width",
    )


def inspect_precious_metals_tab(terminal_output):
    """Run the precious-metals notebook and display its Plotly report."""
    analyze_button = pn.widgets.Button(name="Analyze", button_type="primary")
    status_pane = pn.pane.Markdown("Select **Analyze** to begin.")
    report_pane = pn.pane.HTML(
        "<p>The precious-metals report will appear here.</p>",
        height=900,
        sizing_mode = "stretch_width",
    )

    def analyze_metals(_event):
        del _event
        document = pn.state.curdoc
        if document is None:
            status_pane.object = "Analysis requires an active Panel session."
            return

        analyze_button.disabled = True
        status_pane.object = "Running precious-metals status notebook..."
        report_pane.object = "<p>Executing notebook and generating report...</p>"

        report_path = (
            Path(ROOT_PATH)
            / "reports"
            / "analyses"
            / f"{w2_generateDateStringYYYYMMDD()}_PreciousMetals_{uuid.uuid4().hex[:8]}.html"
        )
        output_events = queue.Queue()
        output_lines = ["Starting precious-metals report..."]
        terminal_output.object = f"<pre>{html.escape(output_lines[0])}</pre>"

        def execute_notebook():
            try:
                command = [
                    sys.executable,
                    "-u",
                    "-c",
                    (
                        "import sys; "
                        "from launch_dashboard import generate_notebook_plotly_report; "
                        "generate_notebook_plotly_report("
                        "sys.argv[1], sys.argv[2], sys.argv[3], "
                        "create_raw_directory=True)"
                    ),
                    str(PRECIOUS_METALS_NOTEBOOK_PATH),
                    str(report_path),
                    "Precious Metals Status",
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
                        (
                            "complete",
                            None,
                            "Precious-metals report failed "
                            f"(process exited with status {return_code}).",
                        )
                    )
                    return

                if not report_path.is_file():
                    output_events.put(
                        ("complete", None, "Notebook completed without creating a report.")
                    )
                    return

                report_html = report_path.read_text(encoding="utf-8")
                report_iframe = (
                    '<iframe '
                    f'srcdoc="{html.escape(report_html, quote=True)}" '
                    'title="Precious metals status report" '
                    'style="width:100%;height:900px;border:0"></iframe>'
                )
                output_events.put(
                    (
                        "complete",
                        report_iframe,
                        "Precious-metals report is ready.",
                    )
                )
            except Exception as exc:
                logging.exception("Failed to execute precious-metals status notebook")
                output_events.put(
                    ("line", f"Dashboard error: {type(exc).__name__}: {exc}")
                )
                output_events.put(
                    ("complete", None, f"Precious-metals report failed: {exc}")
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

            terminal_output.object = (
                f"<pre>{html.escape(chr(10).join(output_lines))}</pre>"
            )
            if completed:
                analyze_button.disabled = False
                callback.stop()

        callback = pn.state.add_periodic_callback(update_output, period = 100)
        threading.Thread(target = execute_notebook, daemon = True).start()

    analyze_button.on_click(analyze_metals)

    return pn.Column(
        pn.pane.Markdown("## Metals"),
        pn.pane.Markdown(
            "Select **Analyze** to execute the precious-metals status notebook "
            "and display its gold, silver, platinum, and palladium charts."
        ),
        pn.Row(analyze_button, sizing_mode = "stretch_width"),
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
            **Panel dashboard for ticker and company analysis**
            
            ## Features
            - Enter a ticker symbol in the Inspect Stocks tab
            - Select **Analyze** to fetch data and generate a Bokeh report
            - Enter a ticker symbol in Inspect Companies to execute the SEC status notebook
            - View generated company charts in the dashboard
            - Generate precious-metals status charts for gold, silver, platinum, and palladium
            
            ## Data Source
            - Analysis is generated by `reports/w1_generateAnalysisReport.py`
            - Company status is generated from `reports/notebooks/generateSECCompanyStatusReport.ipynb`
            - Precious-metals status is generated from `reports/notebooks/generatePreciousMetalsStatusReport.ipynb`
            - Historical data is retrieved through the Helios Interactive Brokers API wrappers
            - The HTML report is saved under `reports/analyses/`
            
            ## Technical Details
            - Built with [Panel](https://panel.holoviz.org/) (v1.9.4)
            - Bokeh HTML is embedded in the Inspect Stocks tab after generation
            
            ## Usage
            1. Run: `python launch_dashboard.py`
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
        ("Stocks", inspect_stocks_tab(terminal_output)),
        ("Companies", inspect_companies_tab(terminal_output)),
        ("Metals", inspect_precious_metals_tab(terminal_output)),
        ("Settings", settings_tab()),
        ("About", about_tab()),
        # location = "sidebar",  # Sidebar tab location
        sizing_mode = "stretch_width",
        margin = (0, 0, 10, 0),
    )
    
    # Header image
    header = pn.pane.Image(
        str(Path(ROOT_PATH) / "helios.png"),
        width = 390,
        align = "center",
        margin = (0, 0, 10, 0),
    )

    # Create main layout
    layout = pn.Column(
        header,
        tabs,
        terminal_section,
        sizing_mode = "stretch_width",
        margin = 10,
    )
    
    # Show the dashboard
    layout.show()


if __name__ == "__main__":
    main()