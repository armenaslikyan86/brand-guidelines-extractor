from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image

from design_data_analyzer.analyzer import aggregate
from design_data_analyzer.extraction import extract_from_path
from design_data_analyzer.guidelines import build_document, render_markdown


def create_test_image(path: Path) -> None:
    image = Image.new("RGB", (120, 120), "white")
    for y in range(120):
        for x in range(120):
            if y < 60:
                image.putpixel((x, y), (0, 161, 222))
            else:
                image.putpixel((x, y), (200, 48, 48))
    image.save(path)


def test_guideline_generation(tmp_path):
    sample_path = tmp_path / "sample.png"
    create_test_image(sample_path)

    extraction = extract_from_path(sample_path)
    assert extraction.colors, "expected color extraction results"

    evidence = aggregate([extraction])
    document = build_document(evidence, brand_name="TestBrand")
    markdown = render_markdown(document)

    assert "TestBrand Brand Guidelines" in markdown
    assert "Tone of Voice" in markdown
    assert "Color" in markdown
