# 🏀 NBA Fantasy Analiz — 5 Takım (MVP v0.4)

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

## 2026–27 projeksiyon motoru (v0.4)

Varsayılan analiz sezonu **2026–27**. Açılışta mevcutsa kayıtlı projeksiyon kullanılır; yoksa uygulama doğrudan [FantasyPros 2026–27 uzman konsensüsü](https://www.fantasypros.com/nba/projections/avg-overall.php) sayfasındaki herkese açık **maç başı** tahminleri yüklemeyi dener. Kayıt 24 saati geçtiğinde kullanıcı oturumunda bir kez tazeleme denenir. **Bu arka planda zamanlanmış bir görev değildir**; uygulama açıkken çalışır. Kaynak Cloud IP'sinden erişime izin vermeyebilir veya sayfa formatını değiştirebilir. Son başarılı veri bozulmadan kalır; olmazsa CSV yüklemek gerekir. Kaynak verileri GitHub deposuna konulmaz.

Kadro girişinden bağımsız **🔮 Sezon Projeksiyonları** alanında "Getir / güncelle", CSV import ve CSV şablon indirme var. Verileri kendi projeksiyon kaynağından almak istersen `sample_data/projection_template.csv` başlıklarını kullan. Her satırdaki `GP` sezonluk beklenen maç, diğer alanlar **maç başına** tahmin olmalı; `FG_PCT` ve `FT_PCT` yüzde değil 0–1 arasında oran girilmeli. `FGA_PG`, `FTA_PG` şut hacmi için önemli.

**Yüzde metriklerinin kısıtı:** FantasyPros'un açık konsensüs tablosunda FGA/FTA yok. Bu nedenle geçici FTA = PTS × 0.22 ve FGA = (PTS − 3PM − FT isabeti) / (2 × FG%) tahminlerini kullanıyoruz. Bunlar kaynağın gerçek hacim projeksiyonu **değil**; model içi vekil değerlerdir. Kesin FG%/FT% z-score veya punt kararı olarak yorumlama. Gerçek şut denemeleri ya da ayrıntılı başka projeksiyon CSV'siyle değiştirilebilir.

Maçlar oynandığında 2026–27 **gerçek sezon** CSV'si / NBA API verisi geldiği takdirde tahminler oyuncu bazında kademeli harmanlanır: 5 maçta %20, 10 maçta %40, 20 maçta %65, 30+ maçta %85 gerçek veri. Beklenen dakika/maç sayısı, tahmini rol bandı ve gerçekleşen dakikadaki değişim gösterilir. Şu anda gerçek verinin otomatik olarak güvenilir biçimde günlük toplanması **tamamlanmadı**; stats.nba.com Streamlit Cloud'dan zaman aşımı verebilir.

[Hashtag Basketball](https://hashtagbasketball.com/fantasy-basketball-points-league-projections) ve [DARKO](https://www.darko.app/projections) rol/üretim karşılaştırması için incelendi; tam yeniden dağıtım izni ve erişilebilir veri kaynağı doğrulanmadığından hiçbir ücretli tablo depoya kopyalanmadı. FantasyPros API için farklı kullanım / lisans koşulları bulunuyor; bu kişisel deneme sürümünü yeniden dağıtılan ticari veri servisi gibi kullanmamalısın.

## Neler var?

- 9-cat: PTS, REB, AST, STL, BLK, 3PM, FG%, FT%, TO için z-score, ilk punt taraması ve kategori bazlı kadro uyumu.
- FG%/FT% oyuncu yüzdelerinin basit ortalamasıyla değil; hacme göre FGM−refFG%×FGA ve FTM−refFT%×FTA katkısıyla puanlanır. TO düşük daha iyi olarak çevrilir.
- Points: Yahoo varsayılan `PTS + 1.2 REB + 1.5 AST + 3 STL + 3 BLK − TO`; ekstra 3PM puanı yoktur. Özel katsayılar takım bazında ayarlanabilir.
- NBA geneli oyuncu sıralaması **1. sıradan bütün oyunculara kadar** gösterilir. 36–185 aralığı ve ilk 50/120 sınırları kaldırıldı; isimle arama var.
- Takıma özel öneriler, mevcut kadro oyuncularını çıkararak tüm oyuncu havuzunu değerlendirir. 9-cat'de ihtiyaç ağırlıklı skor, Points'de beklenen FPTS kullanılır.
- Oyuncu pozisyonu/slotu özelliği şu an eklenmiyor; bu geliştirme isteği iptal edildi.
- 2026–27 oyuncu bazlı sezon projeksiyonları, dakika ve oynanması beklenen maçlar.
- Gerçek maçlar gelmeye başladığında oyuncu başına tahmin/gerçek karışımı.
- Yerel SQLite kadro kayıtları; sezon toplamları CSV cache.

**Sınırlamalar:** Rakip Yahoo lig kadroları ve gerçek waiver sahipliği bilinmiyor; 12 takımlı gerçek lig ortalamaları değil, NBA oyuncu referans havuzu kullanılıyor. Arka planda otomatik veri yenileme, 7/15/30 gün trend, maç fikstürü, streaming, sakatlık durumu ve rakibe karşı tahminler sonraki sürümler. NBA stats kaynağı zaman zaman 403/time-out verebilir. Demo istatistikleri gerçek NBA istatistiği değildir.

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
data_sources.py        # nba_api + sezon toplamları CSV
projection_engine.py  # 2026–27 projeksiyon okuma + geçiş ağırlıkları
roster_catalog.py     # NBA oyuncu ad/ID kataloğu
sample_data/           # sentetik demo + boş şablon
tests/                 # analiz ve kayıt testleri
.github/workflows/     # otomatik test
```

Kadro verisi, ortam dosyaları, secrets ve cache Git'e eklenmez.
