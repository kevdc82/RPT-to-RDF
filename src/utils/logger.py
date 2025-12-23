"""
Logging configuration for RPT to RDF Converter.

Provides structured logging with both console and file output,
including support for rich formatting and progress tracking.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

# Module-level logger cache
_loggers: dict[str, logging.Logger] = {}
_console: Optional[Console] = None


def get_console() -> Console:
    """Get or create the rich console instance."""
    global _console
    if _console is None:
        _console = Console()
    return _console


def setup_logger(
    name: str = "rpt_to_rdf",
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """Set up and configure a logger.

    Args:
        name: Logger name.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Path to log file. If None, uses default.
        log_format: Format string for log messages.
        console_output: Whether to output to console.
        file_output: Whether to output to file.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Clear existing handlers
    logger.handlers.clear()

    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Console handler with rich formatting
    if console_output:
        console_handler = RichHandler(
            console=get_console(),
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
        )
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

    # File handler
    if file_output and log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    # Cache the logger
    _loggers[name] = logger

    return logger


def get_logger(name: str = "rpt_to_rdf") -> logging.Logger:
    """Get an existing logger or create a new one with defaults.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    return setup_logger(name)


class ConversionProgressTracker:
    """Tracks and displays progress of batch conversion with ETA."""

    def __init__(
        self,
        total_files: int,
        description: str = "Converting reports",
        show_eta: bool = True,
        show_rate: bool = True,
    ):
        """Initialize the progress tracker.

        Args:
            total_files: Total number of files to process.
            description: Description text for the progress bar.
            show_eta: Whether to show estimated time remaining.
            show_rate: Whether to show processing rate.
        """
        self.total_files = total_files
        self.description = description
        self.show_eta = show_eta
        self.show_rate = show_rate
        self.console = get_console()
        self.progress: Optional[Progress] = None
        self.task_id = None

        self.successful = 0
        self.partial = 0
        self.failed = 0
        self.processed = 0
        self.start_time: Optional[datetime] = None

    def __enter__(self) -> "ConversionProgressTracker":
        """Enter context manager and start progress display."""
        self.start_time = datetime.now()

        # Build progress columns
        columns = [
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TaskProgressColumn(),
        ]

        if self.show_eta:
            columns.append(TimeRemainingColumn())

        columns.extend(
            [
                TextColumn("•"),
                TextColumn("[green]{task.fields[successful]} OK[/]"),
                TextColumn("[yellow]{task.fields[partial]} partial[/]"),
                TextColumn("[red]{task.fields[failed]} failed[/]"),
            ]
        )

        if self.show_rate:
            columns.append(TextColumn("({task.fields[rate]})"))

        self.progress = Progress(
            *columns,
            console=self.console,
            refresh_per_second=2,
        )
        self.progress.__enter__()
        self.task_id = self.progress.add_task(
            self.description,
            total=self.total_files,
            successful=0,
            partial=0,
            failed=0,
            rate="-- files/min",
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and display summary."""
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)

        # Display summary
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            elapsed_seconds = elapsed.total_seconds()

            # Calculate rate
            rate = (self.processed / elapsed_seconds * 60) if elapsed_seconds > 0 else 0

            self.console.print()
            self.console.print("[bold]Conversion Summary[/]")
            self.console.print(f"  Total files:   {self.total_files}")
            self.console.print(f"  [green]Successful:    {self.successful}[/]")
            self.console.print(f"  [yellow]Partial:       {self.partial}[/]")
            self.console.print(f"  [red]Failed:        {self.failed}[/]")
            self.console.print(f"  Time elapsed:  {self._format_duration(elapsed_seconds)}")
            self.console.print(f"  Average rate:  {rate:.1f} files/min")

            if self.processed > 0:
                success_rate = (self.successful / self.processed) * 100
                self.console.print(f"  Success rate:  {success_rate:.1f}%")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def _calculate_rate(self) -> str:
        """Calculate current processing rate."""
        if not self.start_time or self.processed == 0:
            return "-- files/min"

        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed < 1:
            return "-- files/min"

        rate = self.processed / elapsed * 60
        return f"{rate:.1f} files/min"

    def update(
        self,
        status: str,
        current_file: Optional[str] = None,
    ) -> None:
        """Update progress with a file result.

        Args:
            status: Result status - 'success', 'partial', or 'failed'.
            current_file: Name of the current file being processed.
        """
        self.processed += 1

        if status == "success":
            self.successful += 1
        elif status == "partial":
            self.partial += 1
        elif status == "failed":
            self.failed += 1

        if self.progress and self.task_id is not None:
            description = self.description
            if current_file:
                # Truncate long filenames
                if len(current_file) > 30:
                    current_file = current_file[:27] + "..."
                description = f"{self.description}: {current_file}"

            self.progress.update(
                self.task_id,
                advance=1,
                description=description,
                successful=self.successful,
                partial=self.partial,
                failed=self.failed,
                rate=self._calculate_rate(),
            )


class StageLogger:
    """Logger for tracking conversion stages with timing."""

    def __init__(self, logger: logging.Logger):
        """Initialize stage logger.

        Args:
            logger: Parent logger to use.
        """
        self.logger = logger
        self.stage_start: Optional[datetime] = None
        self.current_stage: Optional[str] = None

    def start_stage(self, stage_name: str, details: Optional[str] = None) -> None:
        """Mark the start of a conversion stage.

        Args:
            stage_name: Name of the stage.
            details: Optional additional details.
        """
        self.current_stage = stage_name
        self.stage_start = datetime.now()

        msg = f"Starting stage: {stage_name}"
        if details:
            msg += f" ({details})"
        self.logger.info(msg)

    def end_stage(self, success: bool = True, details: Optional[str] = None) -> None:
        """Mark the end of a conversion stage.

        Args:
            success: Whether the stage completed successfully.
            details: Optional additional details.
        """
        elapsed = None
        if self.stage_start:
            elapsed = datetime.now() - self.stage_start

        status = "completed" if success else "failed"
        msg = f"Stage {self.current_stage} {status}"
        if elapsed:
            msg += f" (took {elapsed.total_seconds():.2f}s)"
        if details:
            msg += f" - {details}"

        if success:
            self.logger.info(msg)
        else:
            self.logger.error(msg)

        self.current_stage = None
        self.stage_start = None

    def log_element(
        self,
        element_type: str,
        element_name: str,
        status: str,
        details: Optional[str] = None,
    ) -> None:
        """Log processing of a report element.

        Args:
            element_type: Type of element (formula, field, section, etc.).
            element_name: Name of the element.
            status: Processing status.
            details: Optional additional details.
        """
        msg = f"  [{element_type}] {element_name}: {status}"
        if details:
            msg += f" - {details}"

        if status in ("success", "converted", "mapped"):
            self.logger.debug(msg)
        elif status in ("partial", "placeholder", "simplified"):
            self.logger.warning(msg)
        else:
            self.logger.error(msg)
