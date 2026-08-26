import sys
import fitz
from pathlib import Path


# Ensure the project root is in sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from pdf_alchemy_templ.cmdline import Cmdline
from pdf_alchemy_templ.parseargs import PDFArgumentParser

ASSET_PDF = PROJECT_ROOT / "pdf_alchemy" / "tests" / "assets" / "test_alchemy.pdf"


def run_cmdline(args_list, capsys):
    """Helper to parse arguments, run Cmdline, and capture output."""
    parser = PDFArgumentParser()
    args = parser.parser.parse_args(args_list)
    app = Cmdline(args)
    # Dispatch based on args similar to main logic
    if args.total_pages:
        app.get_num_pages()
    elif args.split:
        app.split_pdf()
    elif args.delete:
        app.del_range()
    elif args.crop_half:
        app.crop_half()
    elif args.command == "add":
        app.add_pdf()
    elif args.command == "summarize":
        app.summarize_pdf()
    elif args.command == "translate":
        app.translate_pdf()
    else:
        print("No arguments used")
    return capsys.readouterr().out


def test_get_num_pages(capsys):
    out = run_cmdline(["-f", str(ASSET_PDF), "-o", "out", "-tp"], capsys)
    assert "Total pages" in out


def test_split_pdf(tmp_path, capsys):
    # Split first two pages and the rest
    out_dir = tmp_path / "split"
    out_dir.mkdir()
    run_cmdline([
        "-f", str(ASSET_PDF),
        "-o", str(out_dir),
        "-s", "1-2", "3-4"
    ], capsys)
    # Expect two files part_1.pdf and part_2.pdf
    part1 = out_dir / "part_1.pdf"
    part2 = out_dir / "part_2.pdf"
    assert part1.is_file() and part2.is_file()
    # Verify page counts
    doc1 = fitz.open(part1)
    doc2 = fitz.open(part2)
    assert doc1.page_count == 2
    # remaining pages count may vary depending on original pdf length
    assert doc2.page_count >= 1
    doc1.close()
    doc2.close()


def test_del_range(tmp_path, capsys):
    out_pdf = tmp_path / "deleted.pdf"
    run_cmdline([
        "-f", str(ASSET_PDF),
        "-o", str(out_pdf),
        "-d", "1-2"
    ], capsys)
    assert out_pdf.is_file()
    src_doc = fitz.open(ASSET_PDF)
    out_doc = fitz.open(out_pdf)
    assert out_doc.page_count == src_doc.page_count - 2
    src_doc.close()
    out_doc.close()


def test_add_pdf(tmp_path, capsys):
    # Create a small PDF to insert (1 page)
    insert_pdf = tmp_path / "insert.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(insert_pdf)
    doc.close()

    out_pdf = tmp_path / "added.pdf"
    run_cmdline([
        "-f", str(ASSET_PDF),
        "-o", str(out_pdf),
        "add", str(insert_pdf),
        "--after", "1"
    ], capsys)
    assert out_pdf.is_file()
    src_doc = fitz.open(ASSET_PDF)
    out_doc = fitz.open(out_pdf)
    # Inserting 1 page after page 1 should increase total pages by 1
    assert out_doc.page_count == src_doc.page_count + 1
    src_doc.close()
    out_doc.close()


def test_crop_half(tmp_path, capsys):
    out_pdf = tmp_path / "cropped.pdf"
    # Crop first page only
    run_cmdline([
        "-f", str(ASSET_PDF),
        "-o", str(out_pdf),
        "-ch", "1"
    ], capsys)
    assert out_pdf.is_file()
    src_doc = fitz.open(ASSET_PDF)
    out_doc = fitz.open(out_pdf)
    # Original page count plus one extra page for the cropped one
    assert out_doc.page_count == src_doc.page_count + 1
    src_doc.close()
    out_doc.close()

# Don't modify above,
# Add your tests for the 2 new functionalities below

def test_summarize_pdf(tmp_path, capsys):
    out_file = tmp_path / "resumen.txt"
    run_cmdline([
        "-f", str(ASSET_PDF),
        "-o", str(out_file),
        "summarize"
    ], capsys)
    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert "Puntos clave" in content
    assert len(content.strip()) > 0


def test_translate_pdf(tmp_path, capsys):
    out_file = tmp_path / "traducido.txt"
    run_cmdline([
        "-f", str(ASSET_PDF),
        "-o", str(out_file),
        "translate", "--target-lang", "en"
    ], capsys)
    assert out_file.is_file()
    content = out_file.read_text(encoding="utf-8")
    assert len(content.strip()) > 0