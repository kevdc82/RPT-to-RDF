"""
Configuration management for RPT to RDF Converter.

Handles loading, validation, and access to configuration settings
from YAML files and environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


@dataclass
class ExtractionDockerConfig:
    """Configuration for Docker-based RPT extraction."""
    image: str = "rpttoxml:latest"


@dataclass
class ExtractionConfig:
    """Configuration for RPT extraction."""
    # Mode: "docker", "java", or "dotnet"
    mode: str = "docker"

    # Docker settings
    docker: ExtractionDockerConfig = field(default_factory=ExtractionDockerConfig)

    # Path to RptToXml (for java/dotnet modes)
    rpttoxml_path: str = "./tools/RptToXmlJava/rpttoxml.sh"
    temp_directory: str = "./temp"
    timeout_seconds: int = 120
    parallel_workers: int = 4
    retry_attempts: int = 2


@dataclass
class OracleDockerConfig:
    """Configuration for Docker-based Oracle Reports."""
    container: str = "oracle-reports"
    oracle_home: str = "/u01/oracle/product/12c"
    db_host: str = "oracle-db"
    db_port: int = 1521
    db_service: str = "XE"


@dataclass
class OracleConfig:
    """Configuration for Oracle Reports."""
    # Mode: "docker" or "native"
    mode: str = "docker"

    # Docker settings
    docker: OracleDockerConfig = field(default_factory=OracleDockerConfig)

    # Native settings
    home: str = ""
    connection: str = ""
    reports_server: str = "localhost:9002"


@dataclass
class PathsConfig:
    """Configuration for file paths."""
    input_directory: str = "./input"
    output_directory: str = "./output"
    log_directory: str = "./logs"


@dataclass
class ConversionConfig:
    """Configuration for conversion behavior."""
    # What to do with unsupported features: placeholder, skip, fail
    on_unsupported_formula: str = "placeholder"
    on_complex_layout: str = "simplify"
    on_subreport: str = "inline"

    # Naming conventions
    formula_prefix: str = "CF_"
    parameter_prefix: str = "P_"
    field_prefix: str = "F_"

    # Layout conversion
    coordinate_unit: str = "points"  # points, inches, cm
    default_font: str = "Arial"
    default_font_size: int = 10


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "./logs/conversion.log"
    console_output: bool = True
    file_output: bool = True


@dataclass
class Config:
    """Main configuration container."""
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    oracle: OracleConfig = field(default_factory=OracleConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    conversion: ConversionConfig = field(default_factory=ConversionConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, config_path: str) -> "Config":
        """Load configuration from a YAML file."""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create configuration from a dictionary."""
        config = cls()

        if "extraction" in data:
            extraction_data = data["extraction"].copy()
            # Handle nested docker config
            docker_data = extraction_data.pop("docker", {})
            config.extraction = ExtractionConfig(**extraction_data)
            if docker_data:
                config.extraction.docker = ExtractionDockerConfig(**docker_data)

        if "oracle" in data:
            oracle_data = data["oracle"].copy()
            # Handle nested docker config
            docker_data = oracle_data.pop("docker", {})
            config.oracle = OracleConfig(**oracle_data)
            if docker_data:
                config.oracle.docker = OracleDockerConfig(**docker_data)

        if "paths" in data:
            config.paths = PathsConfig(**data["paths"])

        if "conversion" in data:
            config.conversion = ConversionConfig(**data["conversion"])

        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])

        return config

    def merge_env_vars(self) -> None:
        """Merge environment variables into configuration.

        Environment variables take precedence over config file values.
        """
        load_dotenv()

        # Oracle configuration from environment
        if os.getenv("ORACLE_HOME"):
            self.oracle.home = os.getenv("ORACLE_HOME")

        if os.getenv("ORACLE_CONNECTION"):
            self.oracle.connection = os.getenv("ORACLE_CONNECTION")

        if os.getenv("ORACLE_REPORTS_SERVER"):
            self.oracle.reports_server = os.getenv("ORACLE_REPORTS_SERVER")

        # Extraction configuration
        if os.getenv("RPTTOXML_PATH"):
            self.extraction.rpttoxml_path = os.getenv("RPTTOXML_PATH")

        if os.getenv("EXTRACTION_WORKERS"):
            self.extraction.parallel_workers = int(os.getenv("EXTRACTION_WORKERS"))

        # Path configuration
        if os.getenv("INPUT_DIRECTORY"):
            self.paths.input_directory = os.getenv("INPUT_DIRECTORY")

        if os.getenv("OUTPUT_DIRECTORY"):
            self.paths.output_directory = os.getenv("OUTPUT_DIRECTORY")

        if os.getenv("LOG_DIRECTORY"):
            self.paths.log_directory = os.getenv("LOG_DIRECTORY")

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Validate Oracle configuration based on mode
        if self.oracle.mode == "docker":
            # Docker mode validation
            if not self.oracle.docker.container:
                errors.append("Docker container name (oracle.docker.container) is required")
            if not self.oracle.docker.oracle_home:
                errors.append("Oracle home in container (oracle.docker.oracle_home) is required")
        elif self.oracle.mode == "native":
            # Native mode validation
            if not self.oracle.home:
                errors.append("Oracle home path (oracle.home) is required for native mode")
            elif not Path(self.oracle.home).exists():
                errors.append(f"Oracle home path does not exist: {self.oracle.home}")
            if not self.oracle.connection:
                errors.append("Oracle connection string (oracle.connection) is required for native mode")
        else:
            errors.append(f"Invalid oracle.mode: {self.oracle.mode}. Must be 'docker' or 'native'")

        # Validate extraction configuration based on mode
        valid_extraction_modes = ["docker", "java", "dotnet"]
        if self.extraction.mode not in valid_extraction_modes:
            errors.append(
                f"Invalid extraction.mode: {self.extraction.mode}. "
                f"Must be one of: {valid_extraction_modes}"
            )
        elif self.extraction.mode == "docker":
            # Docker mode - check that image is specified
            if not self.extraction.docker.image:
                errors.append("Docker image name (extraction.docker.image) is required")
            # Note: We don't check if Docker/image exists here, that's done at runtime
        else:
            # Java or dotnet mode - check RptToXml path
            rpttoxml_path = Path(self.extraction.rpttoxml_path)
            if not rpttoxml_path.exists():
                errors.append(f"RptToXml executable not found: {self.extraction.rpttoxml_path}")

        # Validate conversion options
        valid_unsupported_actions = ["placeholder", "skip", "fail"]
        if self.conversion.on_unsupported_formula not in valid_unsupported_actions:
            errors.append(
                f"Invalid on_unsupported_formula: {self.conversion.on_unsupported_formula}. "
                f"Must be one of: {valid_unsupported_actions}"
            )

        valid_layout_actions = ["simplify", "skip", "fail"]
        if self.conversion.on_complex_layout not in valid_layout_actions:
            errors.append(
                f"Invalid on_complex_layout: {self.conversion.on_complex_layout}. "
                f"Must be one of: {valid_layout_actions}"
            )

        valid_subreport_actions = ["inline", "skip", "reference"]
        if self.conversion.on_subreport not in valid_subreport_actions:
            errors.append(
                f"Invalid on_subreport: {self.conversion.on_subreport}. "
                f"Must be one of: {valid_subreport_actions}"
            )

        return errors

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        directories = [
            self.paths.input_directory,
            self.paths.output_directory,
            self.paths.log_directory,
            self.extraction.temp_directory,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[Config] = None


def load_config(config_path: str = "config/settings.yaml") -> Config:
    """Load configuration from file and environment variables.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Loaded and validated configuration.
    """
    global _config

    try:
        _config = Config.from_yaml(config_path)
    except FileNotFoundError:
        # Use defaults if config file doesn't exist
        _config = Config()

    _config.merge_env_vars()
    return _config


def get_config() -> Config:
    """Get the current configuration.

    Returns:
        Current configuration, loading defaults if not yet loaded.
    """
    global _config

    if _config is None:
        _config = Config()
        _config.merge_env_vars()

    return _config
