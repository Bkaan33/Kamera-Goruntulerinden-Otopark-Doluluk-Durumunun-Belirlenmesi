# Kamera Görüntülerinden Otopark Doluluk Durumunun Belirlenmesi

Fırat Üniversitesi Bilgisayar Mühendisliği Tasarım Dersi kapsamında geliştirilen Grup 38 projesi.

**Ekip adı:** Grup 38. Akıllı Otopark Durum Takibi  
**Takım kaptanı:** Kutay KAYA

## Projenin amacı

Otopark görüntülerindeki önceden tanımlanmış park alanlarını analiz ederek dolu ve boş alanları belirlemek, boş yer sayısını ekranda göstermek. Boş alanların yeşil, dolu alanların kırmızı çerçevelerle gösterilmesi hedeflenmektedir.

## Mevcut aşama

Hafta 1 kapsamındaki problem tanımı, yöntem seçimi, geliştirme planı ve görev dağılımı hazırlanmıştır. Bu belge planlanan sistemi açıklar. Çalışan prototip, deneysel doğruluk ve performans sonuçları henüz bu hazırlık kapsamında sunulmamaktadır.

## Planlanan yöntem

1. Park alanlarını ilgi bölgeleri (ROI) olarak işaretlemek ve koordinatlarını kaydetmek.
2. Görüntüyü gri tona dönüştürmek.
3. Gaussian bulanıklaştırma ve uyarlamalı eşikleme uygulamak.
4. Her ROI içindeki piksel yoğunluğunu ölçerek dolu/boş kararını vermek.
5. Durumları renkli çerçevelerle göstermek ve boş yer sayısını hesaplamak.

Karar eşiği örnek dolu ve boş alanlarla belirlenecek; farklı ışık ve gölge koşullarında doğrulanacaktır. Bu aşamada model doğruluğu için sayısal bir başarı iddiası bulunmamaktadır.

## Kullanılması planlanan teknolojiler

- Python
- OpenCV (`cv2`)
- NumPy
- Video kaydı, webcam veya IP kamera görüntüsü

## Geliştirme sırası

| Aşama | Beklenen çıktı |
|---|---|
| Sabit fotoğraf | ROI koordinatları ve fotoğraf üzerinde doluluk prototipi |
| Video | Kare bazında güncellenen doluluk durumu ve boş yer sayacı |
| Simülasyon ve test | Işık, gölge ve hareket senaryoları için ölçüm tablosu |
| Canlı kamera | Kamera akışında çalışan prototip ve kurulum açıklaması |

## Ekip ve görev dağılımı

| Üye | Ana iş paketleri |
|---|---|
| Berke Kaan KAÇAR | Görüntü ön işleme; canlı kamera entegrasyonu |
| Furkan TAŞKIRAN | Statik görüntüde doluluk tespiti; video ve dinamik sayaç |
| Kutay KAYA | Veri ve ROI hazırlama; simülasyon ve performans testleri; ekip koordinasyonu |

Her üye iki ana iş paketinden sorumludur. Raporlama ve teslim ortak yürütülür; herkes geliştirdiği modülü, yöntemini ve çıktısını belgeler. Ayrıntılı görev tanımları [proje planında](docs/PROJE_PLANI.md) yer alır.

## Başarı ölçütleri

- **Doluluk doğruluğu:** Doğru sınıflandırılan park alanı sayısı / değerlendirilen toplam alan sayısı.
- **Boş yer sayım hatası:** Tahmin edilen ve gerçek boş yer sayıları arasındaki mutlak fark.
- **İşlem süresi:** Kare başına ortalama işlem süresi.
- **Kare hızı:** Video ve canlı kamera aşamalarında işlenen kare sayısı/saniye.

Gerçek doluluk etiketleri elle hazırlanacaktır. Henüz ölçüm sonucu olmadığı için bir doğruluk yüzdesi veya kare hızı belirtilmemektedir.

## Önerilen dosya düzeni

```text
README.md
.gitignore
docs/
  PROJE_PLANI.md
  KAYNAKLAR.md
  raporlar/
    Hafta1_Proje_Raporu.docx
src/
  .gitkeep
data/
  README.md
```

`src/` geliştirme sırasında eklenecek kaynak kodları için ayrılmıştır. Veri örnekleri ve ROI koordinatları `data/` altında düzenlenecektir. Çalıştırma komutları, prototip ve bağımlılıkları eklendikten sonra belgelenecektir.

## Rapor ve kaynaklar

- [Hafta 1 proje raporu](docs/raporlar/Hafta1_Proje_Raporu.docx)
- [Kaynaklar](docs/KAYNAKLAR.md)
- [GitHub proje deposu](https://github.com/Bkaan33/Kamera-Goruntulerinden-Otopark-Doluluk-Durumunun-Belirlenmesi)
