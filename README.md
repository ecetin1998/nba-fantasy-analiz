# 🏀 NBA Fantasy Analiz — 5 Takım (MVP v0.2)

Yahoo API veya OAuth gerektirmeyen, Python + Streamlit tabanlı NBA fantasy analiz aracı. Henüz yayınlanmış canlı bir servis değildir.

## Kurulum

Python 3.10+:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Uygulama tarayıcıda `http://localhost:8501` üzerinden açılır. Streamlit Community Cloud'da **repo: nba-fantasy-analiz**, **branch: main**, **main file: app.py** kullan.

## 5 takım

| Fantasy takımı | Format | Yahoo lig ID |
|---|---|---|
| 2fe2d | H2H 9-cat | 27758 |
| benny bilanço | H2H Points | 9421 |
| myopia | H2H 9-cat | 47408 |
| emo361 | H2H Points | 227098 |
| Bilandyczak | H2H 9-cat | 248620 |

Kadro ve IL oyuncularını **NBA istatistiklerini indirmeden**, ana ekrandaki **👥 Kadrom** bölümünde tek tek arayarak veya listede olmayanları isim yazarak ekleyip kaydedebilirsin. NBA istatistiklerini ayrı bir bölümde 'NBA verisini çek / yenile' ile çekebilir veya sezon toplamlarından CSV yükleyebilirsin. NBA bağlantısı çalışmazsa demo (sentetik) verisiyle arayüz denenebilir.

## Kadromu nereden giriyorum?

Uygulamayı açınca **👥 Kadrom** ekranı en üstte görünür; veri çekmek için beklemen gerekmez. Sol üstteki menüden takımı seç, oyuncuları arayıp ekle, IL'yi seç ve **💾 Kadroyu kaydet** butonuna bas. Yeni çaylak gibi dizinde olmayan oyuncuları 'Oyuncu listede yoksa adını yaz' alanından ekleyebilirsin. Kaydedilen adlar, NBA istatistikleri geldiğinde oyuncu adlarına göre eşleştirilir.

**Uyarı:** Bu ilk sürümde Streamlit Cloud kayıtları yerel SQLite'dır. Sunucu restart/deploy sırasında kadrolar kaybolabilir; ayrıca herkese açık uygulamada giriş koruması yoktur. Kalıcı güvenli kadro depolama sonraki sürüm kapsamındadır.

## Neler var?

- 9-cat: PTS, REB, AST, STL, BLK, 3PM, FG%, FT%, TO için z-score, ilk punt taraması ve kategori bazlı kadro uyumu.
- FG%/FT% oyuncu yüzdelerinin basit ortalamasıyla değil; hacme göre FGM−refFG%×FGA ve FTM−refFT%×FTA katkısıyla puanlanır. TO düşük daha iyi olarak çevrilir.
- Points: Yahoo varsayılan `PTS + 1.2 REB + 1.5 AST + 3 STL + 3 BLK − TO`; ekstra 3PM puanı yoktur. Özel katsayılar takım bazında ayarlanabilir.
- NBA geneli oyuncu sıralaması ve takıma göre aday sıralaması.
- Yerel SQLite kadro kayıtları; sezon toplamları CSV cache.

**Sınırlamalar:** Rakip Yahoo lig kadroları ve gerçek waiver sahipliği bilinmiyor; 12 takımlı gerçek lig ortalamaları değil, NBA oyuncu referans havuzu kullanılıyor. Günlük otomatik veri yenileme, 7/15/30 gün trend, maç fikstürü, streaming, sakatlık durumu ve rakibe karşı tahminler sonraki sürümler. NBA stats kaynağı zaman zaman 403/time-out verebilir. Demo istatistikleri gerçek NBA istatistiği değildir.

## Streamlit Cloud için önemli

Ücretsiz barındırmada yerel SQLite/CSV dosyaları deploy veya yeniden başlatma sırasında sıfırlanabilir. Kalıcı kadrolar için Supabase/Postgres gibi dış veritabanı gerekecek. NBA istatistiklerinin **otomatik günlük yenilenmesi henüz kurulmadı**.

## Test

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
```

GitHub Actions `.github/workflows/tests.yml` ana branch'e gönderilen değişikliklerde test çalıştırır.

## Dosya yapısı

```
app.py                 # Streamlit arayüz
analysis.py            # NBA fantasy hesaplamaları
storage.py             # SQLite kadrolar + puan ayarları
data_sources.py        # nba_api + CSV
sample_data/           # sentetik demo + boş şablon
tests/                 # analiz ve kayıt testleri
.github/workflows/     # otomatik test
```

Kadro verisi, ortam dosyaları, secrets ve cache Git'e eklenmez.
