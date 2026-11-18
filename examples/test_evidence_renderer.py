"""Tests for faithful and safe terminal evidence rendering."""

from scripts.capture_demo_evidence import render_terminal_svg


def test_svg_renderer_escapes_terminal_text():
    svg = render_terminal_svg("example", "<script>alert('x')</script> & output\n")
    assert "&lt;script&gt;" in svg
    assert "&amp; output" in svg
    assert "<script>" not in svg


def test_svg_renderer_includes_every_output_line_and_title():
    svg = render_terminal_svg("safe project", "first line\nsecond line\n")
    assert "safe project / captured stdout" in svg
    assert "first line" in svg
    assert "second line" in svg
    assert svg.count('class="line"') == 2


def test_svg_renderer_handles_empty_output_explicitly():
    svg = render_terminal_svg("empty", "")
    assert "(no standard output)" in svg
