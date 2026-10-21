# Test ve Kabul Planı (İP 6)

Sorumlu: Kutay KAYA

Bu doküman, sistemin nasıl test edileceğini, hangi metriklerin ölçüleceğini ve sistemin hangi koşullarda kabul edilmiş sayılacağını tanımlar. Buradaki sayısal değerler **hedeftir**; gerçek sonuçlar testler tamamlandıktan sonra raporlanacaktır.

## Test verisi

- Ekip tarafından çekilen otopark fotoğrafları ve videoları
- Gerekirse farklı hava koşullarını temsil etmek için PKLot benzeri açık veri setlerinden örnek görüntüler [4]

Her test görüntüsü için park alanlarının gerçek durumu (dolu/boş) elle etiketlenir ve `data/labels/` klasöründe JSON olarak saklanır. Video testlerinde belirli aralıklarla seçilen kareler etiketlenir.

### Etiket dosyası formatı

Etiket dosyası ile sistem çıktısı aynı formattadır; değerlendirme scripti ikisini karşılaştırır.

```json
{
  "image": "otopark_01.jpg",
  "scenario": "S1",
  "spots": [
    {"id": 0, "occupied": true},
    {"id": 1, "occupied": false}
  ]
}
```

`id` değerleri ROI dosyasındaki park alanı sırasıyla aynıdır.

## Ölçülecek metrikler

| Metrik | Tanım |
|---|---|
| Doğruluk | Doğru sınıflandırılan alan sayısı / toplam alan sayısı |
| Sayım hatası | \|tahmin edilen boş alan sayısı − gerçek boş alan sayısı\|, görüntüler üzerinden ortalama |
| İşlem süresi | Kare başına ortalama işlem süresi (ms), `time.perf_counter` ile |
| Kare hızı | Saniyede işlenen kare sayısı (FPS) |

Ek olarak dolu alanın "boş" sanılması (yanlış boş) ayrıca raporlanır; çünkü sürücüyü dolu yere yönlendirmek, boş alanı dolu göstermekten daha rahatsız edici bir hatadır.

## Test senaryoları

| No | Senaryo | Amaç |
|---|---|---|
| S1 | Normal gün ışığı | Temel performansı ölçmek |
| S2 | Bina veya ağaç gölgesinin park alanlarına düşmesi | Gölgenin yanlış "dolu" kararına yol açıp açmadığını görmek |
| S3 | Aracın gölgesinin komşu boş alana düşmesi | Komşu alan etkisini ölçmek |
| S4 | Bulutlu / yağmurlu hava | Düşük kontrast koşulunu test etmek |
| S5 | Akşam / düşük ışık | Karanlıkta eşiklemenin davranışını görmek |
| S6 | Güneş parlaması / yansıma | Aşırı parlak bölgelerin etkisini ölçmek |
| S7 | Alandan geçen yaya veya araç (video) | Zamansal kararlılığı test etmek |
| S8 | Hatalı giriş (olmayan dosya, açılamayan kamera, eksik ROI dosyası) | Hata yönetimini doğrulamak |

## Kabul ölçütleri (hedef)

| Ölçüt | Hedef |
|---|---|
| Normal ışıkta (S1) doğruluk | ≥ %95 |
| Gölge, hava ve ışık senaryolarında (S2–S6) doğruluk | ≥ %85 |
| Ortalama sayım hatası | ≤ 1 alan / görüntü |
| 720p karede işlem süresi | ≤ 100 ms (≥ 10 FPS), standart dizüstü bilgisayarda |
| Hatalı girişler (S8) | Program çökmez, anlaşılır hata mesajı verir |

Hedefler, sabit fotoğraf aşamasındaki ilk ölçümlerden sonra ekipçe gözden geçirilebilir.

## Testlerin çalıştırılması

Sistem çıktıları etiketlerle aynı formatta `data/predictions/` klasörüne yazıldıktan sonra:

```bash
python tests/evaluate.py --labels data/labels --predictions data/predictions
```

İşlem süresini ölçmek için:

```bash
python tests/evaluate.py --benchmark data/images
```

## Sonuç tablosu (testler sonrası doldurulacak)

| Senaryo | Görüntü sayısı | Doğruluk | Ort. sayım hatası | Yanlış boş | Ort. süre (ms) |
|---|---|---|---|---|---|
| S1 | | | | | |
| S2 | | | | | |
| S3 | | | | | |
| S4 | | | | | |
| S5 | | | | | |
| S6 | | | | | |
| S7 | | | | | |
