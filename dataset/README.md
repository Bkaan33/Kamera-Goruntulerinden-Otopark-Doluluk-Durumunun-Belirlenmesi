# Veri seti ve ROI hazırlığı

Bu klasör, mevcut `detector/parking_detector.py` ile doğrudan kullanılabilen
12 gerçek PKLot otopark fotoğrafı, 37 park alanının koordinatları ve
12 fotoğrafın kaynak dolu/boş etiketlerini içerir. Görüntüler UFPR04 kamerasının
aynı açı ve çözünürlükteki (1280 × 720) kayıtlarından seçilmiştir.
Güneşli, bulutlu ve yağmurlu grupların her birinde dört fotoğraf vardır.

## Dosyalar

| Yol | İçerik |
|---|---|
| `images/` | Üzerine kutu veya yazı çizilmemiş orijinal JPG fotoğrafları |
| `rois.json` | Detector için `spots` listesi ve görüntü boyutu |
| `labels/` | `tests/evaluate.py` ile uyumlu gerçek doluluk etiketleri |
| `roi_selector.py` | Fareyle ROI seçme, silme, kaydetme ve elle etiketleme |
| `prepare_samples.py` | Fotoğrafları ve kaynak etiketlerini yeniden indirme/dönüştürme |
| `sample_sources.json` | Kaynak depo commit'i ve seçilen dosya yolları |
| `manifest.json` | Kaynak URL, SHA-256, hava durumu, kaynak etiket id'leri ve veri ayrımı |
| `SOURCES.md` | Kaynak, lisans ve dönüşüm açıklaması |

## Hazır fotoğrafı çalıştır

Komutları depo kökünde çalıştır:

```bash
python -m pip install -r requirements.txt
python detector/main.py --source dataset/images/2012-12-11_17_06_09.jpg --rois dataset/rois.json
```

Mevcut detector kodu JSON dosyasındaki `spots` listesini okur. Her elemanda
`id`, `x`, `y`, `width`, `height` vardır. `(x, y)` sol üst köşedir; ölçüler
orijinal fotoğrafın piksel koordinatlarıdır. Ön işleme kodu
`src/preprocessing.py` konumunda kalır.

## Kendi otoparkını işaretle

Yeni kamera için ayrı ROI dosyası oluştur:

```bash
python dataset/roi_selector.py --image dataset/images/kendi_otoparkim.jpg --output dataset/kendi_rois.json
```

- Sol tuşla sürükle: dikdörtgen park alanı ekle.
- Alanın içine sol tıkla: alanı seç.
- Alanın içine sağ tıkla: alanı sil. Kalan alanların id değerleri değişmez.
- Seçili alanda `o`: dolu; `b`: boş. Sarı alan henüz etiketlenmemiştir.
- `s`: JSON dosyasını kaydet. `q` veya ESC: çık.

Pencereyi kapatmadan önce `s` tuşuna bas. Yeniden açıldığında mevcut
`--output` dosyası yüklenir; yanlış görüntü boyutu ve taşan koordinatlar reddedilir.
Önizleme küçültülse de kayıtlar orijinal boyuta dönüştürülür.
Her park yerinin genişlik ve yüksekliği ayrı saklanır.

Fotoğrafın gerçek doluluğunu da kaydetmek için:

```bash
python dataset/roi_selector.py --image dataset/images/kendi_otoparkim.jpg --output dataset/kendi_rois.json --labels dataset/labels/kendi_otoparkim.json --scenario S1
```

`--labels` kullanıldığında her alan için dolu/boş seçimi yapmadan kayıt yapılamaz.
Yeni bir fotoğrafta aynı koordinatları kullanabilirsin; doluluk etiketleri ise
o fotoğrafa özel yeniden belirlenmelidir. Kamera konumu, kadraj veya görüntü
boyutu değiştiğinde ROI'leri yeniden hazırla.

Pencere açmadan kayıtları görsel olarak kontrol et:

```bash
python dataset/roi_selector.py --image dataset/images/2012-12-11_17_06_09.jpg --preview sonuclar/roi_onizleme.png
```

## Tahmin ve değerlendirme

Aynı fotoğrafın tahminini, etiket dosyasıyla aynı adla kaydet:

```bash
python detector/main.py --source dataset/images/2012-12-11_17_06_09.jpg --no-show --save-json sonuclar/predictions/2012-12-11_17_06_09.json --scenario S1
python tests/evaluate.py --labels dataset/labels --predictions sonuclar/predictions
```

Bu örnek yalnızca bir fotoğraf üretir; değerlendirme kalan 11 fotoğrafın
tahminini bulamadığında uyarı verir. Tam ölçüm için her fotoğrafı aynı şekilde
işle. Etiket JSON'larındaki `occupied` değerleri kaynak annotasyonlarından
gelir; algoritmanın tahminleri gerçek etiket yerine kullanılmaz.

`manifest.json` içinde her hava grubunun ilk fotoğrafı `calibration`, kalanları
`test` olarak ayrılmıştır (3 ayar fotoğrafı, 9 test fotoğrafı). Eşiği yalnızca
ayar fotoğrafları üzerinde seç. Ayrılmış test ölçümünde iki klasöre de yalnızca
bu 9 test fotoğrafına ait etiketleri ve tahminleri koy. Tüm 12 fotoğrafla yapılan
kontrol, bağımsız test başarısı olarak raporlanmamalıdır.

Güneşli fotoğraflar S1, bulutlu/yağmurlu fotoğraflar S4 olarak işaretlidir.
Bu küçük örnek seti S2–S3 ve S5–S7 senaryolarını kapsamayı garanti etmez.
Kaynak etiketler döndürülmüş park alanlarına aittir; mevcut detector ile uyum
için bunların eksenlere paralel sınır kutuları kullanılır. Bazı kutular komşu
zemini de içerir ve örtüşebilir. Bu durum piksel sayımının doğruluğunu etkileyebilir.
0.25 varsayılan eşiği bu veri seti için doğrulanmış bir başarı garantisi değildir.

## Doğrulama ve yeniden üretim

```bash
python -m unittest discover -s tests -p test_dataset.py -v
python dataset/prepare_samples.py
```

İlk komut fare olaylarının koordinata dönüşümünü, eksik etiket kontrolünü,
fotoğrafların SHA-256 değerlerini ve detector uyumluluğunu test eder.
İkinci komut internet gerektirir; sabitlenmiş kaynaklardan bu klasördeki örnek
görüntüleri, `rois.json`, etiketleri ve manifesti yeniden yazar.
Kendi işaretlemelerini `kendi_rois.json` gibi ayrı bir dosyada tut.
