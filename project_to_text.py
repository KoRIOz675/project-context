import os
import sys
from pathlib import Path
from datetime import datetime

# ── Recognized text file extensions ──────────────────────────────────────────
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".r",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env",
    ".xml", ".svg", ".graphql", ".sql",
    ".md", ".mdx", ".rst", ".txt", ".tex",
    ".dockerfile", ".makefile", ".gitignore", ".gitattributes",
    ".editorconfig", ".prettierrc", ".eslintrc", ".babelrc",
    ""  # files with no extension (Makefile, Dockerfile, etc.)
}

# ── Directories to ignore by default ─────────────────────────────────────────
IGNORED_DIRS = {
    ".git", ".svn", ".hg", ".mvn", ".claude", "neo4j",
    "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    "venv", ".venv", "env", ".env",
    "dist", "build", "out", ".next", ".nuxt", "target",
    ".idea", ".vscode",
    "coverage", ".coverage",
}

DEFAULT_PROMPT = """You are an expert software development assistant.
Below is the complete source code of a project. Analyze it in detail:
- Understand the overall architecture and the role of each file
- Identify dependencies between modules
- Spot potential areas for improvement (performance, readability, security)
- Be ready to answer any questions about this code

The project is presented below with its structure and the contents of each file."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def is_text_file(path: Path) -> bool:
    """Check if a file is a text file based on its extension."""
    suffix = path.suffix.lower()
    name_lower = path.name.lower()
    # Known extension-less files
    if name_lower in {"makefile", "dockerfile", "rakefile", "gemfile",
                      "procfile", "readme", "license", "changelog"}:
        return True
    return suffix in TEXT_EXTENSIONS


def build_tree(root: Path, prefix: str = "", ignored_dirs: set = None) -> list[str]:
    """Generate the ASCII directory tree of the project."""
    if ignored_dirs is None:
        ignored_dirs = IGNORED_DIRS

    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return [f"{prefix}[Permission denied]"]

    entries = [e for e in entries if not (e.is_dir() and e.name in ignored_dirs)]

    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        extension = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{connector}{entry.name}{extension}")
        if entry.is_dir():
            new_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_tree(entry, new_prefix, ignored_dirs))
    return lines


def collect_files(root: Path, ignored_dirs: set = None) -> list[Path]:
    """Recursively collect all text files in the project."""
    if ignored_dirs is None:
        ignored_dirs = IGNORED_DIRS

    collected = []
    for entry in sorted(root.rglob("*")):
        # Skip excluded directories at any depth
        if any(part in ignored_dirs for part in entry.parts):
            continue
        if entry.is_file() and is_text_file(entry):
            collected.append(entry)
    return collected


def read_file_safe(path: Path) -> tuple[str, bool]:
    """Safely read a file. Returns (content, success)."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            return path.read_text(encoding=enc), True
        except (UnicodeDecodeError, PermissionError):
            continue
    return "[Unable to read this file: unsupported encoding or permission denied]", False


def format_separator(title: str, char: str = "=", width: int = 80) -> str:
    return f"\n{char * width}\n{title}\n{char * width}\n"


# ── Main function ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("   Project → Text Converter")
    print("=" * 60)

    # ── 1. Project path ───────────────────────────────────────────────────────
    while True:
        folder_input = input("\n📁 Project folder path: ").strip()
        # Strip any quotes (from drag & drop on some OSes)
        folder_input = folder_input.strip('"').strip("'")
        project_path = Path(folder_input).expanduser().resolve()

        if project_path.is_dir():
            print(f"   ✅ Folder found: {project_path}")
            break
        else:
            print(f"   ❌ Path not found or not a directory. Please try again.")

    # ── 2. Prompt selection ───────────────────────────────────────────────────
    print("\n📝 Prompt selection:")
    print("   [1] Default prompt")
    print("   [2] Custom prompt")

    while True:
        choice = input("\nYour choice (1 or 2): ").strip()
        if choice == "1":
            prompt = DEFAULT_PROMPT
            print("   ✅ Default prompt selected.")
            break
        elif choice == "2":
            print("\nEnter your prompt (finish with a line containing only 'END'):")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            prompt = "\n".join(lines).strip()
            if not prompt:
                print("   ⚠️  Empty prompt, using the default prompt instead.")
                prompt = DEFAULT_PROMPT
            else:
                print("   ✅ Custom prompt saved.")
            break
        else:
            print("   ❌ Please enter 1 or 2.")

    # ── 3. File collection ────────────────────────────────────────────────────
    print("\n🔍 Analyzing project...")
    files = collect_files(project_path)
    print(f"   {len(files)} text file(s) found.")

    # ── 4. Build document ─────────────────────────────────────────────────────
    project_name = project_path.name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output_lines = []

    # Header
    output_lines.append(f"PROJECT: {project_name}")
    output_lines.append(f"Generated on: {timestamp}")
    output_lines.append(f"Source path: {project_path}")
    output_lines.append("")

    # Prompt
    output_lines.append(format_separator("PROMPT"))
    output_lines.append(prompt)
    output_lines.append("")

    # Directory tree
    output_lines.append(format_separator("PROJECT STRUCTURE"))
    output_lines.append(f"{project_name}/")
    tree_lines = build_tree(project_path)
    output_lines.extend(tree_lines)
    output_lines.append("")

    # File contents
    output_lines.append(format_separator("FILE CONTENTS"))

    for file_path in files:
        relative_path = file_path.relative_to(project_path)
        output_lines.append(format_separator(f"📄 {relative_path}", char="-", width=60))
        content, success = read_file_safe(file_path)
        output_lines.append(content)
        output_lines.append("")

    full_output = "\n".join(output_lines)

    # ── 5. Save output ────────────────────────────────────────────────────────
    output_path = project_path / f"{project_name}_context.txt"

    try:
        output_path.write_text(full_output, encoding="utf-8")
        size_kb = output_path.stat().st_size / 1024
        print(f"\n✅ Document generated successfully!")
        print(f"   📄 File    : {output_path}")
        print(f"   📦 Size    : {size_kb:.1f} KB")
        print(f"   📋 Files included: {len(files)}")
    except Exception as e:
        print(f"\n❌ Error writing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
