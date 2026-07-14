from dis_mevzuat.chunking import chunk_legal_text


def test_splits_turkish_articles():
    text = """
    BİRİNCİ BÖLÜM
    Amaç ve kapsam

    MADDE 1- Bu Yönetmeliğin amacı sağlık alanındaki bilgilendirmeyi düzenlemektir.

    MADDE 2- Fiyat ve kampanya bilgisine yer verilemez.

    GEÇİCİ MADDE 1- Önceki hükümler bir ay süreyle uygulanır.
    """
    chunks = chunk_legal_text(text)
    assert len(chunks) == 4
    assert chunks[1].article_no == "1"
    assert chunks[2].article_no == "2"
    assert chunks[3].article_no == "1"
    assert "Fiyat ve kampanya" in chunks[2].text


def test_long_text_is_split():
    text = "MADDE 1- " + "Diş sağlığı hakkında bilgilendirme.\n\n" * 300
    chunks = chunk_legal_text(text, max_chars=1000, overlap=50)
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 1200 for chunk in chunks)


def test_single_long_paragraph_is_bounded():
    text = "Bu uzun bir hukuk cümlesidir. " * 600
    chunks = chunk_legal_text(text, max_chars=1000, overlap=100)
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 1000 for chunk in chunks)
