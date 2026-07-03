import pytest
from chunker import MarkdownAdaptiveChunker

def test_chunk_preserve_code_block():
    chunker = MarkdownAdaptiveChunker()
    md = "# Titre\n\nVoici du code :\n```python\nprint('hello')\nx = 42\n```\nSuite."
    chunks = chunker.chunk_document("TestProj", "test.md", md)
    
    # Le bloc de code doit être resté unifié dans un chunk
    assert any("print('hello')\nx = 42" in c for c in chunks), "Le bloc de code a été brisé"

def test_chunk_preserve_list():
    chunker = MarkdownAdaptiveChunker()
    md = "# Liste\n\n* Élément 1\n* Élément 2\n* Élément 3"
    chunks = chunker.chunk_document("TestProj", "test.md", md)
    
    # La liste doit être intacte
    assert any("* Élément 1\n* Élément 2\n* Élément 3" in c for c in chunks), "La liste a été coupée"

def test_chunk_without_title():
    chunker = MarkdownAdaptiveChunker()
    md = "Juste un texte orphelin sans titre Markdown."
    chunks = chunker.chunk_document("TestProj", "test.md", md)
    
    assert len(chunks) == 1
    assert "Section: Introduction" in chunks[0]

def test_chunk_guillotine_max_chars():
    chunker = MarkdownAdaptiveChunker()
    # On génère un énorme bloc de texte sans espace pour simuler du base64
    md = "# Titre\n\n" + ("A" * 1500)
    chunks = chunker.chunk_document("TestProj", "test.md", md)
    
    # La guillotine (800) doit avoir tranché le monstre
    assert len(chunks) >= 2, "La guillotine n'a pas découpé le texte massif"
    assert all(len(c) <= 800 for c in chunks), "Un chunk a dépassé la limite MAX_CHARS"