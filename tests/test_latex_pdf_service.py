from pathlib import Path

from clibaseapp.services.latex_pdf_service import build_pdf_from_latex


def test_build_pdf_fails_without_tex_extension(tmp_path: Path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("hola", encoding="utf-8")

    result = build_pdf_from_latex(source)

    assert not result.success
    assert result.pdf_path is None
    assert "extensión .tex" in result.message


def test_build_pdf_fails_when_pdflatex_missing(tmp_path: Path, monkeypatch) -> None:
    tex_file = tmp_path / "main.tex"
    tex_file.write_text("\\documentclass{article}\\begin{document}OK\\end{document}", encoding="utf-8")
    monkeypatch.setattr("clibaseapp.services.latex_pdf_service.shutil.which", lambda _: None)

    result = build_pdf_from_latex(tex_file)

    assert not result.success
    assert "pdflatex" in result.message
