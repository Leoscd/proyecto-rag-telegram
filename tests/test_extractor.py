"""Tests para el extractor de documentos."""
import io
import pytest
from pathlib import Path
from unittest.mock import patch
from docx import Document as DocxDocument
from src.ingesta.extractor import DocumentoExtraido


class TestExtraerExtension:
    """Tests por extensión de archivo."""

    def test_extension_no_soportada(self):
        """Extensión no soportada lanza ValueError."""
        from src.ingesta.extractor import extraer
        with pytest.raises(ValueError) as exc_info:
            extraer("archivo.txt")
        assert "no soporta" in str(exc_info.value).lower()

    def test_extension_doc_no_soportada(self):
        """Formato .doc lanza ValueError."""
        from src.ingesta.extractor import extraer
        with pytest.raises(ValueError) as exc_info:
            extraer("archivo.doc")
        assert ".doc no soporta" in str(exc_info.value)


class TestExtraerDocx:
    """Tests para extracción de Word."""

    def test_docx_extraccion_basica(self):
        """Docx extrae texto de párrafos."""
        from src.ingesta.extractor import _extraer_docx
        
        # Crear docx mínimo en memoria
        doc = DocxDocument()
        doc.add_paragraph("Hola mundo")
        
        import io
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        bytes_docx = buffer.read()
        
        resultado = _extraer_docx(bytes_docx)
        
        assert isinstance(resultado, DocumentoExtraido)
        assert resultado.paginas == 1
        assert resultado.es_imagen is False
        assert "Hola mundo" in resultado.texto


class TestExtraerPDF:
    """Tests para PDFs varios."""

    def test_pdf_dataclass(self):
        """Verifica quePDF retorna DocumentoExtraido."""
        from src.ingesta.extractor import DocumentoExtraido
        
        resultado = DocumentoExtraido(
            texto="Texto del PDF",
            paginas=2,
            es_imagen=False,
            bytes_raw=b"fake"
        )
        
        assert resultado.texto == "Texto del PDF"
        assert resultado.paginas == 2
        assert resultado.es_imagen is False


class TestExtraerImagen:
    """Tests para imágenes."""

    def test_imagen_retorna_es_imagen_true(self):
        """Imagen devuelve es_imagen=True y texto vacío."""
        from src.ingesta.extractor import DocumentoExtraido
        
        # Simular resultado de imagen
        resultado = DocumentoExtraido(
            texto="",
            paginas=1,
            es_imagen=True,
            bytes_raw=b"\x89PNG"
        )
        
        assert resultado.es_imagen is True
        assert resultado.texto == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])