# 📊 Portföy Takip Merkezi

Kendi hisse portföyünü **tamamen ücretsiz** takip etmen için tek sayfalık komuta merkezi.
Pozisyonlarını ekle, kalıcı olarak saklansın; portföyünü etkileyebilecek her şeyi
(fiyat, trend, risk sinyalleri, bilanço tarihleri, piyasa ortamı ve haberler) tek ekrandan izle.

> ⚠️ Eğitim amaçlıdır. Yatırım tavsiyesi değildir, gerçek emir gönderilmez.

## Özellikler

**💼 Portföy Yönetimi**
- BIST (`THYAO.IS`, `ASELS.IS`...) ve ABD (`AAPL`, `NVDA`...) hisseleri bir arada
- Adet + ortalama maliyet ile ekle; aynı sembolü tekrar eklersen maliyet otomatik ortalanır
- Sat/azalt ve sil işlemleri; hisseler ve nakit `data/portfolio.json` dosyasında **kalıcı**
- TRY ve USD pozisyonları otomatik kurla (USD/TRY) tek toplamda birleşir

**🌍 Piyasa Ortamı Şeridi**
S&P 500, Nasdaq, BIST 100, VIX, DXY, ABD 10 yıllık, USD/TRY, Altın, Brent, Bitcoin — hepsi tek bakışta.

**🚨 Risk & Uyarı Motoru** ("önlem al" panosu)
- Maliyete göre %10 / %20 zarar eşikleri
- Günlük sert düşüş (%4 uyarı, %8 kritik)
- 50 ve 200 günlük ortalama kırılımları (trend bozulması)
- RSI aşırı alım / aşırı satım
- **ATR bazlı stop önerisi** (fiyat − 2×ATR) ve stopa yaklaşma uyarısı
- Bilanço tarihi yaklaşıyor (7 gün içinde)
- Tek hissede %35+ konsantrasyon riski
- VIX 25/32 üzeri piyasa stresi

**💵 Nakit**
Portföye TRY ve/veya USD nakit ekleyebilirsin. Nakit toplam değere ve dağılım grafiğine girer,
ağırlıkları doğru hesaplar — ama **kâr/zarara karışmaz** (nominal değerde taşınır, K/Z yüzdeni
yapay olarak seyreltmez). 0 yazarsan silinir.

**📈 Getiri Karşılaştırma**
Portföyün diğer yatırım araçlarına karşı nasıl gitti:
- Kıyas araçları: S&P 500, Nasdaq, BIST 100, Altın, Dolar (USD/TRY), Bitcoin
- Dönem seçimi: 1 ay / 3 ay / 6 ay / yıl başı / 1 yıl
- **Ortak para birimi** (TRY veya USD) — tüm seriler seçtiğin para birimine çevrilir, yoksa
  BIST'i TL, S&P'yi dolar bazında kıyaslamak yanıltıcı olur
- Başlangıç = 100'e endekslenmiş "getiri yarışı" grafiği + sıralama tablosu ("Portföye Fark" sütunuyla)
- Nakit oranın getiriyi ne kadar frenlediğini not olarak gösterir

> Grafikteki portföy çizgisi **bugünkü pozisyonlarının** geçmişe uygulanmasıdır (al-tut simülasyonu):
> "bu sepetle bu dönemde ne olurdu" sorusunu yanıtlar. Gerçekte ödediğin maliyete göre kâr/zararın
> ise aynı sayfanın altında ayrıca gösterilir.

**🔄 Sektör Rotasyonu (RRG)**
Para hangi sektörden çıkıp hangisine giriyor — tek haritada:
- 11 SPDR sektör ETF'i, S&P 500'e karşı **Göreceli Güç** (yatay) ve **Momentum** (dikey) eksenlerinde
- Dört bölge: 🔵 İyileşen → 🟢 Lider → 🟡 Zayıflayan → 🔴 Geride (sektörler normalde saat yönünde döner)
- Her sektörün **son 8 haftalık yolu kuyruk**, bugünkü konumu **ok ucu** ile gösterilir — hareketin yönü bir bakışta görünür
- "Bu hafta hangi hareket var?" listesi: `XLE: Geride ➡️ İyileşen · doğal rotasyon` gibi bölge değişimlerini yazıyla da verir
- Risk iştahı özeti (döngüsel sektörler mi, defansifler mi önde?)
- 1 hafta / 1 ay / 3 ay sektör performans sıralaması
- İsteğe bağlı: **kendi hisselerini de aynı haritaya** ekleyip sektörlere göre nerede durduklarını görebilirsin

> Not: Orijinal JdK RS-Ratio formülü ticari/kapalıdır. Burada sektörlerin birbirine karşı puanlandığı
> (cross-sectional) açık yaklaşım kullanılır; yön ve bölge geçişleri ticari sürümle uyumludur,
> mutlak değerler birebir aynı olmayabilir. Ölçek her zaman sektörlerle belirlenir — kendi hisselerini
> eklemek sektörlerin yerini **değiştirmez**.

**🧭 Piyasa Pusulası**
Piyasayı okumanın 5 katmanı + ekonomik takvim, tek sayfada — her bölümün altında
"🧒 Basit anlatım" kutusu (çocuğa anlatır gibi benzetmelerle):
1. **Makro Ortam** — faiz, dolar, emtia şeridi ("hava durumu")
2. **Piyasa İçi Göstergeler (breadth)** — 60 büyük hisselik örneklemde SMA50/200 üstü %,
   yükselen/düşen sayısı, 20 günlük zirve/dip + 1 yıllık katılım grafiği ("halat çekme yarışı")
3. **Duygu & Volatilite** — VIX + momentum + breadth + SPY put/call'dan hesaplanan
   0-100 korku/iştah skoru, ibreli gösterge ("okul bahçesinin gürültü ölçeri")
4. **Para Akışı** — lider/geride sektör özeti, RRG sayfasına bağlanır ("AVM güvenlik kamerası")
5. **Tek Hisse Katmanı** — portföyündeki uyarılar, SMA200 altındakiler, yaklaşan bilançolar
   ("saksı bitkisi bakımı")

**📅 Ekonomik Takvim** — FOMC faiz kararları (Fed'in resmî 2026 takvimi), NFP istihdam
raporu (her ayın ilk cuması, otomatik hesaplanır) ve portföyündeki hisselerin bilanço
tarihleri; kaç gün kaldığıyla birlikte. Tarihi oynayan veriler (CPI gibi) tahmin edilmez.

**🎯 Opsiyon Radarı**
ABD hisse/ETF'lerinde opsiyon akışı (Yahoo Finance, ~15 dk gecikmeli, ücretsiz):
- 16 likit isim (SPY, QQQ, NVDA, TSLA...) + portföyündeki ABD hisseleri otomatik taranır
- En yakın vadede **call ve put hacmi** (bugün işlem gören kontrat), yığılmış çubuk grafikle sıralama
- **Put/Call oranı** ve eğilim etiketi (put ağırlıklı = korunma/düşüş, call ağırlıklı = yükseliş spekülasyonu)
- Özet kartlar: en yüksek hacimli hisse, en yüksek/en düşük P/C
- Hisse seçince **en çok işlem gören kontratlar** (tür, kullanım fiyatı, hacim, açık pozisyon, IV)
- BIST hisselerinde Yahoo opsiyon verisi olmadığı için yalnızca ABD sembolleri taranır

**📰 Portföy Haberleri**
Yahoo Finance + Google News RSS (API anahtarı gerekmez). BIST hisseleri için Türkçe kaynaklar,
ABD hisseleri için İngilizce kaynaklar; hisseye göre filtrelenebilir.

**📈 Grafikler**
Mum grafik + SMA50/200 + maliyet çizgin + stop önerisi, portföy dağılımı,
pozisyon bazında K/Z ve zaman içinde portföy değeri.

**🌐 TR / EN arayüz** — kenar çubuğundan anında dil değişimi.

## Kurulum

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tarayıcıda `http://localhost:8501` açılır. İlk açılışta portföy boştur;
**Pozisyonlar** sayfasından hisselerini ekle. Veriler `data/` klasöründe yerel olarak saklanır
(bulut yok, hesap yok, ücret yok).

## Canlıya Alma (Streamlit Community Cloud)

Streamlit sürekli açık bir sunucu gerektirdiği için Vercel gibi serverless platformlarda
çalışmaz; ücretsiz resmî barındırma [share.streamlit.io](https://share.streamlit.io) üzerinden yapılır.

1. Bu depoyu GitHub'a push et (aşağıda `data/` **push edilmez** — kişisel portföyün asla
   herkese açık repoya girmez, `.gitignore` bunu garanti eder).
2. share.streamlit.io → **New app** → bu GitHub reposunu seç → `app.py` giriş dosyası.
3. **Settings → Secrets** kısmına ekle:
   ```
   PORTFOY_DEMO = "1"
   ```
   Bu, uygulamayı **demo moduna** alır: her ziyaretçi kendi tarayıcı oturumunda, örnek bir
   portföy üzerinde deneme yapar; hiçbir değişiklik diske yazılmaz, ziyaretçiler birbirinin
   verisini görmez/değiştiremez, sekme kapanınca oturum sıfırlanır.
4. Deploy'a bas. Birkaç dakika içinde `xxx.streamlit.app` adresin hazır olur.

> `PORTFOY_DEMO` ayarlanmazsa uygulama normal (tek kullanıcılı, kalıcı dosya) modda çalışır —
> bu mod yalnızca kendi bilgisayarında tek başına çalıştırdığın senaryo için uygundur, herkese
> açık bir deploy'da **kullanılmamalıdır**.

## Testler

```bash
python -m pytest tests -q
```

248 test: girdi doğrulama/güvenlik, göstergeler (RSI, ATR, SMA), depolama (nakit + demo mod dahil),
uyarı motoru, sektör rotasyonu (RRG), getiri karşılaştırma (para birimi + saat dilimi),
opsiyon hacmi, breadth, korku/iştah skoru ve ekonomik takvim.

## Güvenlik

- Tüm kullanıcı girdileri doğrulanır (sembol regex'i, sayısal sınırlar, not uzunluğu)
- HTML'e giren her değer kaçışlanır (XSS koruması); haber linkleri yalnızca `http(s)` olabilir
- RSS, güvenli XML ayrıştırıcıyla (defusedxml) okunur; tüm isteklerde zaman aşımı vardır
- Atomik dosya yazımı — çökme anında bile portföy dosyası bozulmaz
- Hiçbir API anahtarı/sır yoktur ve gerekmez; Streamlit XSRF koruması açıktır

## Mimari

```
app.py                  # giriş noktası + sayfa yönlendirme
portfoy/
├── config.py           # eşikler, semboller, sabitler
├── security.py         # doğrulama + kaçışlama
├── storage.py          # kalıcı JSON depolama (atomik yazma)
├── data.py             # yfinance veri katmanı (önbellekli)
├── indicators.py       # RSI, SMA, ATR (saf fonksiyonlar)
├── risk.py             # metrikler + uyarı motoru (saf, test edilebilir)
├── rotation.py         # sektör rotasyonu / RRG matematiği (saf)
├── performance.py      # getiri karşılaştırma, para birimi çevrimi (saf)
├── options.py          # opsiyon hacmi toplama, put/call oranı (saf)
├── breadth.py          # piyasa genişliği: SMA üstü %, A/D, zirve/dip (saf)
├── sentiment.py        # korku/iştah bileşik skoru (saf)
├── calendar_events.py  # FOMC/NFP/bilanço takvimi (saf)
├── news.py             # Yahoo + Google News RSS
├── charts.py           # Plotly grafikleri
├── i18n.py             # TR/EN metinler
└── views/              # Streamlit sayfaları
```
