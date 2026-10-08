# Kamera Görüntülerinden Otopark Doluluk Durumunun Belirlenmesi

Kamera görüntülerinden park alanlarının doluluk durumunu analiz etmeyi ve güncel boş yer sayısını göstermeyi amaçlayan bir görüntü işleme projesi.

## Amaç

Otopark görüntüsünde önceden tanımlanan park alanlarını dolu veya boş olarak sınıflandırmak. Boş alanların yeşil, dolu alanların kırmızı çerçevelerle gösterilmesi ve toplam boş yer sayısının ekrana yansıtılması hedeflenmektedir.

## Projenin mevcut aşaması

Proje planlama ve yöntem belirleme aşamasındadır. Çalışan prototip ve deneysel sonuçlar henüz bu depoda sunulmamaktadır.

## Kullanılması planlanan teknolojiler

- Python
- OpenCV (`cv2`)
- NumPy
- Video kaydı, webcam veya IP kamera görüntüsü

## Planlanan yöntem

1. Park alanlarını ilgi bölgeleri (ROI) olarak işaretlemek ve koordinatlarını kaydetmek.
2. Görüntüyü gri tona dönüştürmek.
3. Gaussian bulanıklaştırma ile gürültüyü azaltmak.
4. Uyarlamalı eşikleme uygulamak.
5. Her ROI içindeki piksel yoğunluğunu ölçerek dolu/boş kararı vermek.
6. Alanların durumunu renkli çerçevelerle göstermek ve boş yer sayısını hesaplamak.

Karar eşiğinin değeri ve yönü örnek dolu ve boş alanlarla belirlenecek; farklı ışık ve gölge koşullarında doğrulanacaktır.

## Geliştirme aşamaları

| Aşama | Beklenen çıktı |
|---|---|
| Sabit fotoğraf | ROI koordinatları ve fotoğraf üzerinde doluluk tespiti |
| Video | Kare bazında güncellenen doluluk durumu ve boş yer sayacı |
| Simülasyon ve test | Işık, gölge ve hareket senaryoları için ölçüm tablosu |
| Canlı kamera | Kamera akışında çalışan prototip ve kurulum açıklaması |

## Başarı ölçütleri

- **Doluluk doğruluğu:** Doğru sınıflandırılan park alanı sayısının değerlendirilen toplam alan sayısına oranı.
- **Boş yer sayım hatası:** Tahmin edilen ve gerçek boş yer sayıları arasındaki mutlak fark.
- **İşlem süresi:** Kare başına ortalama işlem süresi.
- **Kare hızı:** Video ve canlı kamera aşamalarında saniyede işlenen kare sayısı.

Gerçek doluluk etiketleri elle hazırlanacaktır. Sayısal başarı ve performans değerleri testler tamamlandıktan sonra raporlanacaktır.

## Kaynaklar

1. OpenCV. [Smoothing Images](https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html).
2. OpenCV. [Image Thresholding](https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html).
3. OpenCV. [Getting Started with Videos](https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html).
4. de Almeida ve diğerleri (2015). *PKLot - A robust dataset for parking lot classification*. Expert Systems with Applications, 42(11), 4937-4949. [DOI: 10.1016/j.eswa.2015.02.009](https://doi.org/10.1016/j.eswa.2015.02.009).

PKLot çalışması, farklı otopark ve hava koşullarında park alanı sınıflandırmasının değerlendirilmesi için bir literatür örneğidir. Bu kaynağın listelenmesi, projede veri setinin kullanıldığı veya makaledeki algoritmanın uygulandığı anlamına gelmez.
