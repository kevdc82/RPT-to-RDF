"""
CLI Entry Point for RPT to RDF Converter.

Provides command-line interface for batch converting Crystal Reports
to Oracle Reports.
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .config import load_config, Config
from .pipeline import Pipeline
from .utils.logger import setup_logger
from .utils.file_utils import get_rpt_files


console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="rpt-to-rdf")
def cli():
    """Crystal Reports to Oracle Reports Batch Converter.

    Converts Crystal Reports 14 (.rpt) files to Oracle Reports 12c (.rdf) files.
    """
    pass


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.argument("output_path", type=click.Path())
@click.option(
    "--config", "-c",
    default="config/settings.yaml",
    help="Path to configuration file.",
)
@click.option(
    "--workers", "-w",
    default=4,
    type=int,
    help="Number of parallel workers for batch processing.",
)
@click.option(
    "--recursive/--no-recursive", "-r",
    default=True,
    help="Recursively process subdirectories.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Analyze files without converting.",
)
@click.option(
    "--mock",
    is_flag=True,
    help="Use mock extractors/converters for testing.",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output.",
)
def convert(input_path, output_path, config, workers, recursive, dry_run, mock, verbose):
    """Convert RPT files to RDF format.

    INPUT_PATH can be a single .rpt file or a directory containing .rpt files.

    OUTPUT_PATH is the destination for converted .rdf files.

    \b
    Examples:
        rpt-to-rdf convert report.rpt output/report.rdf
        rpt-to-rdf convert ./input/ ./output/ --workers 8
        rpt-to-rdf convert ./input/ ./output/ --dry-run
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logger(
        name="rpt_to_rdf",
        level=log_level,
        log_file="logs/conversion.log",
    )

    # Load configuration
    try:
        cfg = load_config(config)
    except FileNotFoundError:
        console.print(f"[yellow]Config file not found: {config}. Using defaults.[/]")
        cfg = Config()

    # Create pipeline
    pipeline = Pipeline(config=cfg, use_mock=mock)

    # Validate configuration
    if not mock:
        errors = pipeline.validate_configuration()
        if errors:
            console.print("[red]Configuration errors:[/]")
            for error in errors:
                console.print(f"  - {error}")
            if not dry_run:
                sys.exit(1)

    input_path = Path(input_path)
    output_path = Path(output_path)

    if dry_run:
        # Dry run - just analyze
        console.print("[bold]Dry run mode - analyzing files without converting[/]")

        if input_path.is_file():
            console.print(f"Would convert: {input_path} -> {output_path}")
        else:
            analysis = pipeline.analyze_reports(input_path, recursive=recursive)
            _display_analysis(analysis)
        return

    # Perform conversion
    if input_path.is_file():
        # Single file conversion
        result = pipeline.process_file(input_path, output_path)

        if result.status == "success":
            console.print(f"[green]Successfully converted:[/] {output_path}")
        elif result.status == "partial":
            console.print(f"[yellow]Partially converted:[/] {output_path}")
            for warning in result.warnings:
                console.print(f"  [yellow]Warning:[/] {warning}")
        else:
            console.print(f"[red]Failed to convert:[/] {input_path}")
            for error in result.errors:
                console.print(f"  [red]Error:[/] {error}")
            sys.exit(1)
    else:
        # Directory conversion
        report = pipeline.process_directory(
            input_path,
            output_path,
            recursive=recursive,
            workers=workers,
        )

        # Display summary
        _display_summary(report)

        # Save reports
        html_path, csv_path, json_path = report.save_reports(
            str(Path(cfg.paths.log_directory))
        )
        console.print(f"\n[bold]Reports saved:[/]")
        console.print(f"  HTML: {html_path}")
        console.print(f"  CSV:  {csv_path}")
        console.print(f"  JSON: {json_path}")

        # Exit with error if any failures
        if report.failed > 0:
            sys.exit(1)


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--recursive/--no-recursive", "-r",
    default=True,
    help="Recursively analyze subdirectories.",
)
@click.option(
    "--mock",
    is_flag=True,
    help="Use mock extractor for testing.",
)
def analyze(input_path, recursive, mock):
    """Analyze RPT files and generate complexity report.

    INPUT_PATH can be a single .rpt file or a directory.

    \b
    Examples:
        rpt-to-rdf analyze ./reports/
        rpt-to-rdf analyze report.rpt
    """
    setup_logger(name="rpt_to_rdf", level="INFO")

    cfg = Config()
    pipeline = Pipeline(config=cfg, use_mock=mock)

    input_path = Path(input_path)

    if input_path.is_file():
        rpt_files = [input_path]
    else:
        rpt_files = list(get_rpt_files(input_path, recursive=recursive))

    console.print(f"[bold]Analyzing {len(rpt_files)} RPT files...[/]\n")

    if input_path.is_dir():
        analysis = pipeline.analyze_reports(input_path, recursive=recursive)
        _display_analysis(analysis)
    else:
        console.print(f"File: {input_path.name}")


@cli.command()
@click.argument("report_file", type=click.Path(exists=True))
def validate(report_file):
    """Validate a converted RDF file.

    REPORT_FILE is the path to the .rdf file to validate.

    \b
    Examples:
        rpt-to-rdf validate output/report.rdf
    """
    report_path = Path(report_file)

    if not report_path.exists():
        console.print(f"[red]File not found:[/] {report_path}")
        sys.exit(1)

    # Check file extension
    if report_path.suffix.lower() not in [".rdf", ".xml"]:
        console.print(f"[yellow]Warning:[/] Expected .rdf or .xml file")

    # Check file size
    size = report_path.stat().st_size
    if size < 100:
        console.print(f"[red]File appears too small ({size} bytes) - may be corrupt[/]")
        sys.exit(1)

    console.print(f"[green]File validation passed:[/] {report_path}")
    console.print(f"  Size: {size:,} bytes")


@cli.command()
@click.option(
    "--config", "-c",
    default="config/settings.yaml",
    help="Path to configuration file.",
)
def check_config(config):
    """Check configuration and environment setup.

    \b
    Examples:
        rpt-to-rdf check-config
        rpt-to-rdf check-config -c custom_config.yaml
    """
    console.print("[bold]Checking configuration...[/]\n")

    try:
        cfg = load_config(config)
        console.print(f"[green]Config file loaded:[/] {config}")
    except FileNotFoundError:
        console.print(f"[yellow]Config file not found:[/] {config}")
        console.print("[yellow]Using default configuration[/]")
        cfg = Config()

    # Validate configuration
    errors = cfg.validate()

    # Display configuration summary
    table = Table(title="Configuration Summary")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="green")

    # Oracle settings
    oracle_status = "[green]OK[/]" if cfg.oracle.home and Path(cfg.oracle.home).exists() else "[red]Missing[/]"
    table.add_row("Oracle Home", cfg.oracle.home or "(not set)", oracle_status)

    conn_status = "[green]OK[/]" if cfg.oracle.connection else "[red]Missing[/]"
    table.add_row("Oracle Connection", cfg.oracle.connection or "(not set)", conn_status)

    # RptToXml
    rpt_status = "[green]OK[/]" if Path(cfg.extraction.rpttoxml_path).exists() else "[yellow]Not found[/]"
    table.add_row("RptToXml Path", cfg.extraction.rpttoxml_path, rpt_status)

    # Directories
    table.add_row("Input Directory", cfg.paths.input_directory, "[green]OK[/]")
    table.add_row("Output Directory", cfg.paths.output_directory, "[green]OK[/]")
    table.add_row("Log Directory", cfg.paths.log_directory, "[green]OK[/]")

    # Workers
    table.add_row("Parallel Workers", str(cfg.extraction.parallel_workers), "[green]OK[/]")

    console.print(table)

    if errors:
        console.print("\n[red]Configuration Errors:[/]")
        for error in errors:
            console.print(f"  - {error}")
        console.print("\n[yellow]Note:[/] Some errors may be acceptable for --mock mode")
    else:
        console.print("\n[green]Configuration is valid![/]")


def _display_summary(report):
    """Display conversion summary table."""
    table = Table(title="Conversion Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="white", justify="right")

    table.add_row("Total Files", str(report.total_files))
    table.add_row("[green]Successful[/]", f"[green]{report.successful}[/]")
    table.add_row("[yellow]Partial[/]", f"[yellow]{report.partial}[/]")
    table.add_row("[red]Failed[/]", f"[red]{report.failed}[/]")

    if report.duration:
        table.add_row("Duration", f"{report.duration:.1f}s")

    table.add_row("Success Rate", f"{report.success_rate:.1f}%")

    console.print(table)


def _display_analysis(analysis):
    """Display analysis results."""
    # Summary table
    table = Table(title="Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="white", justify="right")

    table.add_row("Total Files", str(analysis["total_files"]))
    table.add_row("[green]Simple (score 1-3)[/]", str(analysis["complexity_distribution"]["simple"]))
    table.add_row("[yellow]Medium (score 4-6)[/]", str(analysis["complexity_distribution"]["medium"]))
    table.add_row("[red]Complex (score 7-10)[/]", str(analysis["complexity_distribution"]["complex"]))

    console.print(table)

    # Feature usage
    console.print("\n[bold]Feature Usage:[/]")
    for feature, count in analysis["feature_usage"].items():
        console.print(f"  {feature.capitalize()}: {count} reports")

    # Per-file details (first 20)
    if analysis["files"]:
        console.print("\n[bold]File Details (first 20):[/]")
        file_table = Table()
        file_table.add_column("File", style="cyan")
        file_table.add_column("Score", justify="right")
        file_table.add_column("Formulas", justify="right")
        file_table.add_column("Params", justify="right")
        file_table.add_column("Groups", justify="right")
        file_table.add_column("Subreports", justify="right")

        for file_info in analysis["files"][:20]:
            score = file_info["complexity_score"]
            score_style = (
                "green" if score <= 3
                else "yellow" if score <= 6
                else "red"
            )
            file_table.add_row(
                file_info["name"],
                f"[{score_style}]{score}[/]",
                str(file_info["formulas"]),
                str(file_info["parameters"]),
                str(file_info["groups"]),
                str(file_info["subreports"]),
            )

        console.print(file_table)

        if len(analysis["files"]) > 20:
            console.print(f"\n  ... and {len(analysis['files']) - 20} more files")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
