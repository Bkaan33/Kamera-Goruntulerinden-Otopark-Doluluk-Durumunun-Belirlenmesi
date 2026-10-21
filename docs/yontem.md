# Yöntem Açıklaması ve Kaynak Planı (İP 3)

Sorumlu: Kutay KAYA

Bu doküman, park alanlarının doluluk durumunu belirlemek için izlenecek görüntü işleme adımlarını, kullanılacak araçları ve teknik kaynakları açıklar. Ön işleme adımlarındaki parametreler `src/preprocessing.py` içindeki mevcut uygulamayla uyumludur.

## Kullanılan araçlar

| Araç | Kullanım amacı |
|---|---|
| Python 3 | Ana geliştirme dili |
| OpenCV (`opencv-python`) | Görüntü/video okuma, filtreleme, eşikleme, morfolojik işlemler, çizim |
| NumPy | Piksel dizileri ve sayısal hesaplamalar |
| cvzone | Ekrana metin/çerçeve yazdırma gibi yardımcı görselleştirme işlemleri (planlanan) |

## İşlem hattı

```
Görüntü girişi → ROI'lerin yüklenmesi → Ön işleme → ROI bazında doluluk kararı → Sayaç ve görselleştirme
```

### 1. Görüntü girişi

- Sabit fotoğraf: `cv2.imread`
- Video ve canlı kamera (webcam / IP kamera): `cv2.VideoCapture`

Tüm kaynaklar aynı kare işleme fonksiyonuna verilir; böylece geliştirme aşamaları (fotoğraf → video → kamera) arasında işlem hattı değişmez.

### 2. ROI (ilgi bölgesi) tanımlama

Her park alanının köşe koordinatları bir defaya mahsus fare ile işaretlenir (`cv2.setMouseCallback`) ve bir dosyaya (JSON) kaydedilir. Program her çalıştığında koordinatları bu dosyadan okur. Kamera sabit olduğu sürece ROI'lerin yeniden işaretlenmesi gerekmez.

### 3. Ön işleme (`preprocess_image`)

| Adım | OpenCV fonksiyonu | Parametre | Amaç |
|---|---|---|---|
| Gri tonlama | `cv2.cvtColor` | `COLOR_BGR2GRAY` | Renk bilgisini atıp tek kanala indirmek, işlem yükünü azaltmak |
| Gaussian bulanıklaştırma | `cv2.GaussianBlur` | 3×3 çekirdek, σ = 1 | Sensör gürültüsünü azaltmak [1] |
| Uyarlamalı eşikleme | `cv2.adaptiveThreshold` | Gaussian yöntemi, ters ikili, blok boyutu 25, C = 16 | Eşiği her bölge için yerel olarak hesaplayarak ışık farklarından etkilenmemek [2] |
| Genişletme | `cv2.dilate` | 3×3 çekirdek, 1 iterasyon | Araç kenarlarını kalınlaştırıp belirginleştirmek |

Ters ikili eşikleme sonucunda kenar ve doku içeren bölgeler (araçlar) beyaz, düz zemin siyah görünür.

### 4. Doluluk kararı

Her ROI için işlenmiş görüntüdeki beyaz piksel sayısı `cv2.countNonZero` ile hesaplanır ve ROI alanına oranlanır:

```
doluluk_orani = beyaz_piksel_sayisi / roi_alani
doluluk_orani > esik  →  DOLU
doluluk_orani ≤ esik  →  BOŞ
```

Sabit piksel sayısı yerine oran kullanılması, kararın görüntü çözünürlüğünden ve ROI boyutundan bağımsız olmasını sağlar. Eşik değeri, örnek dolu ve boş alanların oran dağılımına bakılarak belirlenecek ve test aşamasında doğrulanacaktır.

### 5. Sayaç ve görselleştirme

- Boş alanlar yeşil, dolu alanlar kırmızı çerçeve ile çizilir.
- Toplam boş yer sayısı ekranda metin olarak gösterilir ("Boş: 7 / 20" gibi).

### 6. Video ve kamerada kararlılık

Video ve canlı kamerada, geçen bir yaya veya anlık ışık değişimi tek bir karede yanlış karara yol açabilir. Bunu önlemek için her alanın durumu son N karedeki kararların çoğunluğuna göre belirlenir.

### 7. Hata yönetimi

Aşağıdaki durumlarda program çökmek yerine anlaşılır bir mesaj vererek sonlanır veya devam eder:

- Görüntü/video dosyasının bulunamaması
- Kameranın açılamaması
- ROI dosyasının eksik veya bozuk olması
- Video akışından boş kare gelmesi

## Ekibe öneri

Uyarlamalı eşikleme sonrasında küçük tuz-biber gürültüsü kalabilir. Genişletmeden önce `cv2.medianBlur(thresh, 5)` eklenmesi, tek tük beyaz noktaların boş alanı "dolu" göstermesini azaltabilir. Etkisi test aşamasında karşılaştırmalı olarak ölçülebilir.

## Kaynaklar

README'deki numaralandırma korunmuş ve devam ettirilmiştir.

1. OpenCV. *Smoothing Images*. https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html
2. OpenCV. *Image Thresholding*. https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
3. OpenCV. *Getting Started with Videos*. https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html
4. de Almeida ve diğerleri (2015). *PKLot – A robust dataset for parking lot classification*. Expert Systems with Applications, 42(11), 4937–4949. https://doi.org/10.1016/j.eswa.2015.02.009
5. OpenCV. *Morphological Transformations*. https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
6. OpenCV. *Mouse as a Paint-Brush*. https://docs.opencv.org/4.x/db/d5b/tutorial_py_mouse_handling.html
7. NumPy Documentation. https://numpy.org/doc/stable/
8. R. C. Gonzalez, R. E. Woods. *Digital Image Processing*. Pearson.
