# Type Hints Quick Reference Guide

## Table of Contents
1. [Basic Type Hints](#basic-type-hints)
2. [Function Type Hints](#function-type-hints)
3. [Class and Method Type Hints](#class-and-method-type-hints)
4. [Advanced Type Hints](#advanced-type-hints)
5. [Common Patterns in This Project](#common-patterns-in-this-project)
6. [Running Type Checks](#running-type-checks)

## Basic Type Hints

### Simple Types
```python
# Built-in types
name: str = "example"
count: int = 10
price: float = 99.99
is_active: bool = True

# None type
result: None = None

# Path type
from pathlib import Path
file_path: Path = Path("data.txt")
```

### Collections
```python
from typing import List, Dict, Set, Tuple

# Lists
names: List[str] = ["Alice", "Bob"]
numbers: List[int] = [1, 2, 3]

# Dictionaries
config: Dict[str, Any] = {"key": "value"}
scores: Dict[str, int] = {"Alice": 95, "Bob": 87}

# Sets
tags: Set[str] = {"python", "typing"}

# Tuples (fixed length)
coordinates: Tuple[float, float] = (10.0, 20.0)
result: Tuple[bool, str, int] = (True, "success", 200)
```

### Optional Types
```python
from typing import Optional

# Optional means the value can be None
def find_user(user_id: int) -> Optional[User]:
    # Returns User or None
    ...

# Equivalent to Union[User, None]
name: Optional[str] = None  # Can be str or None
```

### Union Types
```python
from typing import Union

# Can be one of multiple types
def process(data: Union[str, int, float]) -> bool:
    ...

# Multiple options
Result = Union[Success, Error, Warning]
```

## Function Type Hints

### Basic Function
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

def calculate(x: int, y: int) -> int:
    return x + y
```

### Function with Optional Parameters
```python
def create_user(
    name: str,
    email: str,
    age: Optional[int] = None,
    active: bool = True
) -> User:
    ...
```

### Function Returning None
```python
def log_message(message: str) -> None:
    print(message)
    # No return statement or returns None
```

### Function Returning Multiple Types
```python
from typing import Union

def get_data(key: str) -> Union[str, int, None]:
    # Can return str, int, or None
    ...
```

### Function with Callable Parameter
```python
from typing import Callable

def process_items(
    items: List[str],
    processor: Callable[[str], str]
) -> List[str]:
    return [processor(item) for item in items]
```

## Class and Method Type Hints

### Basic Class
```python
class User:
    def __init__(self, name: str, age: int) -> None:
        self.name: str = name
        self.age: int = age

    def get_info(self) -> str:
        return f"{self.name}, {self.age}"
```

### Dataclass
```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Report:
    name: str
    status: str = "pending"
    errors: List[str] = field(default_factory=list)
    result: Optional[dict] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "errors": self.errors
        }
```

### Class Variables and Instance Variables
```python
from typing import Dict, ClassVar

class Config:
    # Class variable (shared across all instances)
    DEFAULT_TIMEOUT: ClassVar[int] = 30
    MAPPINGS: ClassVar[Dict[str, str]] = {"a": "b"}

    # Instance variables
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.timeout: int = Config.DEFAULT_TIMEOUT
```

## Advanced Type Hints

### Type Aliases
```python
from typing import Dict, List, Tuple

# Create type aliases for complex types
ColumnData = Dict[str, List[Any]]
Coordinates = Tuple[float, float]
ErrorList = List[Tuple[str, int]]

def process_columns(data: ColumnData) -> ErrorList:
    ...
```

### Generic Types
```python
from typing import TypeVar, Generic, List

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

# Usage
stack: Stack[int] = Stack()
stack.push(10)
```

### Literal Types
```python
from typing import Literal

def set_mode(mode: Literal["read", "write", "append"]) -> None:
    # mode can only be one of these exact strings
    ...
```

### Protocol (Structural Subtyping)
```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None:
        ...

def render(obj: Drawable) -> None:
    obj.draw()
```

## Common Patterns in This Project

### Parser Return Types
```python
from pathlib import Path
from typing import Optional

class CrystalParser:
    def parse_file(
        self,
        xml_path: Path,
        rpt_path: Optional[Path] = None
    ) -> ReportModel:
        ...
```

### Translator Patterns
```python
from typing import List, Tuple

class FormulaTranslator:
    def _translate_expression(
        self,
        expression: str
    ) -> Tuple[str, List[str]]:
        # Returns (translated_expr, warnings)
        ...

    def batch_translate(
        self,
        formulas: List[Formula]
    ) -> List[TranslatedFormula]:
        ...
```

### Mapper Patterns
```python
from typing import Dict, Optional

class TypeMapper:
    DEFAULT_MAPPINGS: Dict[DataType, OracleType] = {...}

    def map_type(
        self,
        crystal_type: DataType,
        length: Optional[int] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None
    ) -> OracleType:
        ...
```

### Pipeline Patterns
```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class PipelineResult:
    rpt_path: Path
    rdf_path: Optional[Path]
    status: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
```

### Error Handling Patterns
```python
from typing import Optional

@dataclass
class ConversionError:
    message: str
    category: ErrorCategory
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        ...
```

## Running Type Checks

### Install mypy
```bash
source venv/bin/activate
pip install mypy
```

### Basic Type Checking
```bash
# Check entire project
mypy src/

# Check specific file
mypy src/parsing/crystal_parser.py

# Check with verbose output
mypy --verbose src/
```

### Generate Reports
```bash
# HTML report (visual coverage)
mypy src/ --html-report .mypy_html
# Open .mypy_html/index.html in browser

# Text report
mypy src/ --txt-report .mypy_txt
```

### Common mypy Options
```bash
# Show error codes
mypy --show-error-codes src/

# Show column numbers
mypy --show-column-numbers src/

# Pretty output
mypy --pretty src/

# Strict mode
mypy --strict src/

# Ignore missing imports
mypy --ignore-missing-imports src/
```

### Configuration
The project uses `mypy.ini` for configuration. Key settings:
- Python version: 3.9
- Warnings enabled for better code quality
- Ignores missing imports from external libraries
- Generates both HTML and text reports

## Best Practices

### 1. Always Type Function Signatures
```python
# Good
def process_data(data: str) -> Dict[str, Any]:
    ...

# Bad (untyped)
def process_data(data):
    ...
```

### 2. Use Optional for Nullable Values
```python
# Good
def find_item(id: int) -> Optional[Item]:
    ...

# Avoid
def find_item(id: int) -> Item:
    # Might return None, causing type errors
    ...
```

### 3. Type Complex Return Values
```python
# Good
def get_stats() -> Tuple[int, int, float]:
    return (total, count, average)

# Less clear
def get_stats():
    return (total, count, average)
```

### 4. Use Type Aliases for Readability
```python
# Good
QueryResult = Dict[str, List[Any]]

def execute_query(sql: str) -> QueryResult:
    ...

# Less readable
def execute_query(sql: str) -> Dict[str, List[Any]]:
    ...
```

### 5. Document with Type Hints
```python
# Type hints serve as documentation
def convert_report(
    input_path: Path,
    output_path: Path,
    config: Optional[Config] = None,
    on_progress: Optional[Callable[[int, int], None]] = None
) -> ConversionResult:
    """
    The function signature already documents:
    - What types of inputs are expected
    - What will be returned
    - Which parameters are optional
    """
    ...
```

## Common Issues and Solutions

### Issue 1: List vs list
```python
# Python 3.9 - use typing module
from typing import List
data: List[str] = []

# Python 3.10+ - built-in generics
data: list[str] = []
```

### Issue 2: Circular Imports
```python
# Use string literals for forward references
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .other_module import OtherClass

def process(obj: 'OtherClass') -> None:
    ...
```

### Issue 3: Any vs Unknown Type
```python
from typing import Any

# Use Any sparingly - it disables type checking
data: Any = ...  # Can be anything

# Prefer specific types when possible
data: Union[str, int, dict] = ...
```

### Issue 4: Mutable Default Arguments
```python
from dataclasses import dataclass, field
from typing import List

# Good - use field(default_factory)
@dataclass
class Report:
    errors: List[str] = field(default_factory=list)

# Bad - mutable default
@dataclass
class Report:
    errors: List[str] = []  # Same list shared across instances!
```

## Resources

- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 561 - Distributing Type Information](https://www.python.org/dev/peps/pep-0561/)
- [Real Python - Type Checking](https://realpython.com/python-type-checking/)
