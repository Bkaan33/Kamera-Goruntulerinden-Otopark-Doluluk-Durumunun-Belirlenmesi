# Görüntü ve etiket kaynakları

Görüntüler PKLot veri setinin UFPR04 bölümüne aittir. Bu depoda yalnızca
eğitim projesinin ilk testleri için 12 fotoğraflık küçük bir alt küme bulunur.

Orijinal çalışma: de Almeida, P. R. L., Oliveira, L. S., Britto Jr., A. S.,
Silva Jr., E. J. ve Koerich, A. L. (2015). PKLot – A robust dataset for
parking lot classification. Expert Systems with Applications, 42(11), 4937–4949.
https://doi.org/10.1016/j.eswa.2015.02.009

Orijinal veri seti sayfası:
https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/

Görüntüleri ve doluluk etiketlerini aldığımız kaynak:
https://github.com/DSBD-Research/MetaPKLot-Dataset

MetaPKLot çalışması: de Almeida ve diğerleri (2026). MetaPKLot – new challenges
and protocols for vision-based parking lot management. Neural Computing and
Applications, 38, Article 704. https://doi.org/10.1007/s00521-026-12398-0

Kaynak deponun PKLot için bildirdiği lisans: **CC BY 4.0**.
Lisans metni: https://creativecommons.org/licenses/by/4.0/legalcode
Bu atıf ve lisans bağlantısını görüntülerle birlikte koruyun.

Kaynak commit'i `sample_sources.json` içinde sabitlenmiştir. Her görüntünün
doğrudan indirme URL'si, SHA-256 özeti, kaynak görüntü id'si ve kaynak
annotasyon id'leri `manifest.json` içindedir. Görüntü baytları değiştirilmemiş,
yeniden boyutlandırılmamış ve üzerlerine kutu çizilmemiştir.

## Yapılan dönüşüm

MetaPKLot `annotations/original/spots/PKLot/ufpr04_spots.tar.xz` arşivindeki
COCO benzeri JSON kayıtları kullanılmıştır. `category_id=0` boş,
`category_id=1` dolu anlamındadır. Bu etiketler elle yeniden oluşturulmamıştır.

Kaynak `bbox` koordinatları mevcut detectorün beklediği
`x, y, width, height` biçimine dönüştürülmüştür. Kutular görüntü sınırlarına
kırpılmıştır. Aynı kamera geometrisi için kutular koordinatlarına göre
sıralanıp 0–36 arasında sabit id verilmiştir. Etiketlerde de aynı id eşlemesi
kullanılmıştır. Kaynağın görüntüye özel annotasyon id'leri ayrıca manifestte
saklanır; bunlar doğrudan park yeri id'si değildir.

Kamera açısı değişen sonraki kayıtlar bu alt kümeye alınmamıştır.
