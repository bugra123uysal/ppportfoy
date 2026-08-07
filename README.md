# 📊 Portföy Takip Merkezi

Kendi hisse portföyünü **tamamen ücretsiz** takip etmen için tek sayfalık komuta merkezi.
Pozisyonlarını ekle, kalıcı olarak saklansın; portföyünü etkileyebilecek her şeyi
(fiyat, trend, risk sinyalleri, sektör rotasyonu, indikatör taraması ve haberler) tek yerden izle.

> ⚠️ Eğitim amaçlıdır. Yatırım tavsiyesi değildir, gerçek emir gönderilmez.

## Özellikler

**💼 Portföy Yönetimi**
- BIST (`THYAO.IS`, `ASELS.IS`...) ve ABD (`AAPL`, `NVDA`...) hisseleri bir arada
- Adet + ortalama maliyet ile ekle; aynı sembolü tekrar eklersen maliyet otomatik ortalanır
- Sat/azalt ve sil işlemleri; hisseler ve nakit kalıcı olarak saklanır
- TRY ve USD pozisyonları otomatik kurla (USD/TRY) tek toplamda birleşir

**🚨 Risk & Uyarı Motoru**
- Maliyete göre %10 / %20 zarar eşikleri
- Günlük sert düşüş (%4 uyarı, %8 kritik)
- 50 ve 200 günlük ortalama kırılımları (trend bozulması)
- RSI aşırı alım / aşırı satım, ATR bazlı stop önerisi
- Bilanço tarihi yaklaşıyor, tek hissede %35+ konsantrasyon riski, VIX piyasa stresi

**📈 Getiri Karşılaştırma**
Portföyün S&P 500, Nasdaq, BIST 100, Altın, Dolar, Bitcoin'e karşı nasıl gitti — ortak para
birimine çevrilmiş "getiri yarışı" grafiği ve sıralama tablosu.

**🔄 Sektör Rotasyonu (RRG)**
Para hangi sektörden çıkıp hangisine giriyor: 11 SPDR sektör ETF'i, S&P 500'e karşı Göreceli
Güç/Momentum eksenlerinde dört bölgede (İyileşen → Lider → Zayıflayan → Geride) gösterilir.
Sektör başına en iyi 5 hisse ve kendi holdinglerini haritaya ekleme dahil.

**🧭 Piyasa Pusulası**
Makro ortam, piyasa genişliği (breadth), korku/iştah skoru, para akışı özeti ve ekonomik
takvim (FOMC/NFP/bilanço) tek sayfada.

**⚡ My Trade**
İndikatör bazlı hisse tarama (4 farklı sinyal grubu: momentum+hacim+Bollinger, trend+sapma+
StochRSI, ATR dönüş+trend rengi, StochRSI+EMA+Medyan) ve stop-loss/pozisyon boyutu (%1 kuralı)
hesaplayıcısı.

**🚀 Günün Hareketlileri (Movers)**
ABD piyasası, arka planda ~20 dakikada bir taranır (bkz. `.github/workflows/movers-scan.yml`):
Yahoo'nun günlük "en çok yükselenler" sıralaması + fiyatı henüz büyük hareket etmemişken hacmi
3 aylık ortalamasının kat kat üstüne çıkmış "hacim öncüllüğü" adayları. Her iki liste My Trade'in
indikatör taramasına (Grup 1-4) karşı da kontrol edilir, öne çıkan isimler için son haber
başlıkları otomatik eklenir — "neden yükseliyor" sorusuna hızlı bir cevap.

**🎯 Opsiyon Radarı**
ABD hisse/ETF'lerinde opsiyon akışı (Yahoo Finance, ~15 dk gecikmeli, ücretsiz): call/put
hacmi, put/call oranı, en çok işlem gören kontratlar.

**📰 Portföy Haberleri**
Yahoo Finance + Google News RSS (API anahtarı gerekmez), hisseye göre filtrelenebilir.

## Mimari

İki servisten oluşur, ikisi de aynı Vercel projesinde deploy edilir:

```
web/                    # Next.js (App Router) — arayüz, kullanıcının gördüğü her şey
api/                     # Flask — salt-JSON API, sadece web'in internal service binding'i
                         # üzerinden erişilir, public internete açık değil
portfoy/                # Paylaşılan Python çekirdeği (hem api/ hem testler kullanır)
├── config.py           # eşikler, semboller, sabitler
├── security.py         # doğrulama + kaçışlama
├── storage.py          # kalıcı JSON depolama (atomik yazma, Upstash fallback)
├── data.py             # yfinance veri katmanı (önbellekli)
├── indicators.py       # RSI, SMA, EMA, ATR, Bollinger, CCI, SMI, StochRSI... (saf)
├── risk.py             # metrikler + uyarı motoru (saf, test edilebilir)
├── rotation.py         # sektör rotasyonu / RRG matematiği (saf)
├── trade_scan.py       # My Trade indikatör tarama grupları (saf)
├── movers.py           # Günün hareketlileri: day gainers + hacim öncüllüğü taraması
├── performance.py      # getiri karşılaştırma, para birimi çevrimi (saf)
├── options.py          # opsiyon hacmi toplama, put/call oranı (saf)
├── breadth.py          # piyasa genişliği: SMA üstü %, A/D, zirve/dip (saf)
├── sentiment.py        # korku/iştah bileşik skoru (saf)
├── calendar_events.py  # FOMC/NFP/bilanço takvimi (saf)
├── news.py             # Yahoo + Google News RSS
└── api_data.py         # api/index.py'nin çağırdığı, saf dataclass/dict döndüren katman
```

## Kurulum (yerel geliştirme)

İki servisi ayrı terminallerde çalıştır:

```bash
# 1) Flask API
pip install -r requirements.txt
PORTFOY_API_KEY=devkey python -c "from api.index import app; app.run(host='127.0.0.1', port=5001)"

# 2) Next.js web
cd web
npm install
npm run dev
```

`web/.env.local` içinde şunlar tanımlı olmalı (yerel geliştirme için):

```
SITE_PASSWORD=devpass
PORTFOY_API_URL=http://127.0.0.1:5001
PORTFOY_API_KEY=devkey
```

Tarayıcıda `http://localhost:3000` açılır, `SITE_PASSWORD` ile giriş yapılır. Veriler
`data/` klasöründe yerel dosya olarak saklanır (bulut yok, hesap yok, ücret yok) — Vercel'e
deploy edildiğinde bu, Upstash Redis'e döner (bkz. `portfoy/storage.py` docstring'i).

### Günün Hareketlileri (Movers) kurulumu — production

Movers taraması periyodik olarak GitHub Actions tarafından tetiklenir (Vercel'in ücretsiz
planında native Cron Jobs günde 2 kere ile sınırlı, gün içi tarama için yetersiz). Kurulum:

1. Vercel projesine bir `CRON_SECRET` environment variable ekle (rastgele, en az 16 karakter
   uzun bir string — `openssl rand -hex 32` ile üretilebilir).
2. GitHub reposunda **Settings → Secrets and variables → Actions**:
   - **Variables** sekmesine `SITE_URL` ekle (örn. `https://your-project.vercel.app`, sonunda
     `/` olmadan).
   - **Secrets** sekmesine `CRON_SECRET` ekle — Vercel'e girdiğin değerin **aynısı**.
3. `.github/workflows/movers-scan.yml` piyasa saatlerinde 20 dakikada bir
   `/api/cron/movers-scan`'i tetikler; bu route kendi başına `CRON_SECRET` ile doğrulanır
   (site şifresiyle korunan sayfaların dışındadır, bkz. `web/src/proxy.ts`), sonra dahili
   servis bağlantısı üzerinden Flask'taki gerçek taramayı çalıştırıp Upstash'e yazar.
4. İlk tarama tetiklenene kadar (veya Upstash hiç yapılandırılmamışsa) sayfa isteği anında
   taze bir tarama hesaplar — hiçbir zaman boş kalmaz, sadece daha yavaş yüklenir.

Yerel geliştirmede bu adım gerekmez: `/api/movers` her istekte taze hesaplanır (Upstash yoksa
kalıcı önbellek de yok).

## Testler

```bash
python -m pytest -q
```

400+ test: girdi doğrulama/güvenlik, göstergeler, depolama (nakit dahil), uyarı motoru,
sektör rotasyonu (RRG), My Trade tarama grupları, getiri karşılaştırma (para birimi + saat
dilimi), opsiyon hacmi, breadth, korku/iştah skoru ve ekonomik takvim.

## Güvenlik

- Tüm kullanıcı girdileri doğrulanır (sembol regex'i, sayısal sınırlar, not uzunluğu)
- HTML'e giren her değer kaçışlanır (XSS koruması); haber linkleri yalnızca `http(s)` olabilir
- RSS, güvenli XML ayrıştırıcıyla (defusedxml) okunur; tüm isteklerde zaman aşımı vardır
- Atomik dosya yazımı — çökme anında bile portföy dosyası bozulmaz
- Flask API, `web/` dışından erişilemez (Vercel internal service binding); `X-API-Key`
  header'ı bu bağlantının kazara dışa açılmasına karşı ek bir savunma katmanıdır
- Web arayüzü tek bir paylaşılan şifre (`SITE_PASSWORD`) ile korunur, oturum httpOnly cookie'de
- `/api/cron/movers-scan` tek istisna: şifre gate'inin dışında (dış zamanlayıcının session
  cookie'si yok), kendi başına `CRON_SECRET` ile (timing-safe karşılaştırma) korunur
