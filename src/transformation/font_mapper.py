"""
Font Mapper for RPT to RDF Converter.

Maps Crystal Reports fonts to Oracle-compatible fonts.
"""

from pathlib import Path
from typing import Optional

import yaml

from ..utils.logger import get_logger


class FontMapper:
    """Maps Crystal Reports fonts to Oracle Reports compatible fonts."""

    # Common Crystal to Oracle font mappings
    DEFAULT_FONT_MAP = {
        "Arial": "Arial",
        "Times New Roman": "Times",
        "Courier New": "Courier",
        "Verdana": "Helvetica",
        "Tahoma": "Helvetica",
        "Comic Sans MS": "Helvetica",
        "Georgia": "Times",
        "Trebuchet MS": "Helvetica",
        "Impact": "Helvetica",
        "Calibri": "Helvetica",
        "Cambria": "Times",
        "Consolas": "Courier",
        "Lucida Console": "Courier",
        "Lucida Sans Unicode": "Helvetica",
        "Palatino Linotype": "Times",
        "Book Antiqua": "Times",
        "Century Gothic": "Helvetica",
        "Franklin Gothic Medium": "Helvetica",
        "Garamond": "Times",
        "MS Sans Serif": "Helvetica",
        "MS Serif": "Times",
        "Symbol": "Symbol",
        "Wingdings": "Symbol",
    }

    # Default font settings
    DEFAULT_FONT = "Arial"
    DEFAULT_SIZE = 10

    def __init__(
        self,
        config_path: Optional[str] = None,
        default_font: Optional[str] = None,
        default_size: Optional[int] = None,
    ):
        """Initialize the font mapper.

        Args:
            config_path: Optional path to font_mappings.yaml configuration file.
            default_font: Override default font (default: Arial).
            default_size: Override default size (default: 10).
        """
        self.logger = get_logger("font_mapper")

        # Initialize with default mappings
        self.font_map = self.DEFAULT_FONT_MAP.copy()
        self.default_font = self.DEFAULT_FONT
        self.default_size = self.DEFAULT_SIZE

        # Track if constructor params were explicitly provided
        explicit_font = default_font is not None
        explicit_size = default_size is not None

        # Load custom mappings from config if provided
        if config_path:
            self._load_config(config_path)
        else:
            # Try to load default config location
            default_config = Path(__file__).parent.parent.parent / "config" / "font_mappings.yaml"
            if default_config.exists():
                self._load_config(str(default_config))

        # Constructor params override config values
        if explicit_font:
            self.default_font = default_font
        if explicit_size:
            self.default_size = default_size

    def _load_config(self, config_path: str) -> None:
        """Load font mappings from YAML configuration file.

        Args:
            config_path: Path to font_mappings.yaml file.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                self.logger.warning(f"Empty config file: {config_path}")
                return

            # Update font mappings
            if "fonts" in config:
                custom_fonts = config["fonts"]
                if isinstance(custom_fonts, dict):
                    self.font_map.update(custom_fonts)
                    self.logger.info(f"Loaded {len(custom_fonts)} custom font mappings")

            # Update default font
            if "default_font" in config:
                self.default_font = config["default_font"]
                self.logger.info(f"Set default font to: {self.default_font}")

            # Update default size
            if "default_size" in config:
                self.default_size = config["default_size"]
                self.logger.info(f"Set default size to: {self.default_size}")

        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}")
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML config: {e}")
        except Exception as e:
            self.logger.error(f"Error loading font config: {e}")

    def map_font(self, crystal_font: str) -> str:
        """Map Crystal font to Oracle-compatible font.

        Args:
            crystal_font: Crystal Reports font name.

        Returns:
            Oracle-compatible font name.
        """
        if not crystal_font:
            return self.default_font

        # Try exact match (case-sensitive)
        if crystal_font in self.font_map:
            mapped = self.font_map[crystal_font]
            self.logger.debug(f"Mapped font: {crystal_font} -> {mapped}")
            return mapped

        # Try case-insensitive match
        crystal_lower = crystal_font.lower()
        for key, value in self.font_map.items():
            if key.lower() == crystal_lower:
                self.logger.debug(f"Mapped font (case-insensitive): {crystal_font} -> {value}")
                return value

        # Try partial match (e.g., "Arial Unicode MS" -> "Arial")
        for key, value in self.font_map.items():
            if key.lower() in crystal_lower or crystal_lower.startswith(key.lower()):
                self.logger.debug(f"Mapped font (partial match): {crystal_font} -> {value}")
                return value

        # No match found - log warning and use default
        self.logger.warning(
            f"No mapping for font '{crystal_font}', using default: {self.default_font}"
        )
        return self.default_font

    def map_font_style(
        self,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
    ) -> str:
        """Generate Oracle font style string.

        Args:
            bold: Whether text is bold.
            italic: Whether text is italic.
            underline: Whether text is underlined.

        Returns:
            Oracle font style string (plain, bold, italic, bolditalic).

        Note:
            Oracle Reports doesn't have a separate underline style,
            so underline is tracked but not reflected in the style string.
        """
        if bold and italic:
            return "bolditalic"
        elif bold:
            return "bold"
        elif italic:
            return "italic"
        else:
            return "plain"

    def map_font_size(self, crystal_size: Optional[int]) -> int:
        """Convert Crystal font size to Oracle font size.

        Args:
            crystal_size: Crystal Reports font size in points.

        Returns:
            Oracle Reports font size in points.

        Note:
            Crystal and Oracle both use points for font size,
            so this is typically a 1:1 mapping. However, we validate
            and constrain the size to reasonable bounds.
        """
        if crystal_size is None or crystal_size <= 0:
            return self.default_size

        # Constrain to reasonable bounds (4pt to 144pt)
        if crystal_size < 4:
            self.logger.warning(f"Font size {crystal_size} too small, using 4pt")
            return 4
        elif crystal_size > 144:
            self.logger.warning(f"Font size {crystal_size} too large, using 144pt")
            return 144

        return crystal_size

    def get_font_info(
        self,
        crystal_font: Optional[str],
        crystal_size: Optional[int],
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
    ) -> dict[str, any]:
        """Get complete font information for Oracle Reports.

        Args:
            crystal_font: Crystal Reports font name.
            crystal_size: Crystal Reports font size.
            bold: Whether text is bold.
            italic: Whether text is italic.
            underline: Whether text is underlined.

        Returns:
            Dictionary with oracle_font, oracle_size, oracle_style, and underline.
        """
        return {
            "oracle_font": self.map_font(crystal_font or self.default_font),
            "oracle_size": self.map_font_size(crystal_size),
            "oracle_style": self.map_font_style(bold, italic, underline),
            "underline": underline,  # Track separately for potential future use
        }

    def add_custom_mapping(self, crystal_font: str, oracle_font: str) -> None:
        """Add a custom font mapping at runtime.

        Args:
            crystal_font: Crystal Reports font name.
            oracle_font: Oracle Reports font name.
        """
        self.font_map[crystal_font] = oracle_font
        self.logger.info(f"Added custom font mapping: {crystal_font} -> {oracle_font}")

    def get_all_mappings(self) -> dict[str, str]:
        """Get all current font mappings.

        Returns:
            Dictionary of all font mappings.
        """
        return self.font_map.copy()

    def get_unmapped_fonts(self) -> set[str]:
        """Get set of fonts that have been requested but not mapped.

        This is useful for reporting which fonts in the Crystal report
        don't have explicit mappings and are falling back to defaults.

        Note: This requires tracking usage, which would be implemented
        by storing requested fonts that weren't found.

        Returns:
            Set of unmapped font names.
        """
        # This is a placeholder for future enhancement
        # where we track unmapped fonts during conversion
        return set()
