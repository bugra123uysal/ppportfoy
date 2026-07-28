"""Turkish / English UI strings. t(key, lang, **kwargs) formats templates."""

from __future__ import annotations

_STRINGS: dict[str, dict[str, str]] = {
    # navigation / general
    "app_title": {"tr": "📊 Portföy Takip Merkezi", "en": "📊 Portfolio Command Center"},
    "nav_overview": {"tr": "Genel Bakış", "en": "Overview"},
    "nav_positions": {"tr": "Pozisyonlar", "en": "Positions"},
    "nav_alerts": {"tr": "Risk & Uyarılar", "en": "Risk & Alerts"},
    "nav_market": {"tr": "Piyasa Pusulası", "en": "Market Compass"},
    "nav_compare": {"tr": "Getiri Karşılaştırma", "en": "Performance"},
    "nav_options": {"tr": "Opsiyon Radarı", "en": "Options Radar"},
    "nav_rotation": {"tr": "Sektör Rotasyonu", "en": "Sector Rotation"},
    "nav_news": {"tr": "Haberler", "en": "News"},
    "language": {"tr": "Dil / Language", "en": "Language / Dil"},
    "refresh": {"tr": "🔄 Verileri Yenile", "en": "🔄 Refresh Data"},
    "last_update": {"tr": "Veriler ~5 dk önbelleklenir", "en": "Data cached for ~5 min"},
    "disclaimer": {
        "tr": "⚠️ Eğitim amaçlıdır, yatırım tavsiyesi değildir.",
        "en": "⚠️ Educational tool only. Not investment advice.",
    },
    "demo_banner": {
        "tr": "🧪 **Demo mod** — örnek portföyle serbestçe oyna; değişiklikler yalnızca "
              "senin oturumunda kalır, kimseyle paylaşılmaz ve sekmeyi kapatınca sıfırlanır.",
        "en": "🧪 **Demo mode** — play freely with the sample portfolio; changes stay in "
              "your session only, are never shared, and reset when you close the tab.",
    },
    "empty_portfolio": {
        "tr": "Portföyün henüz boş. **Pozisyonlar** sayfasından ilk hisseni ekle 👇",
        "en": "Your portfolio is empty. Add your first position on the **Positions** page 👇",
    },
    "data_error": {
        "tr": "Veri alınamadı (Yahoo Finance erişimi). Birazdan tekrar dene.",
        "en": "Could not fetch data (Yahoo Finance). Try again shortly.",
    },
    # overview
    "macro_strip": {"tr": "🌍 Piyasa Ortamı", "en": "🌍 Market Context"},
    "total_value": {"tr": "Toplam Değer", "en": "Total Value"},
    "total_cost": {"tr": "Toplam Maliyet", "en": "Total Cost"},
    "total_pnl": {"tr": "Toplam K/Z", "en": "Total P/L"},
    "daily_change": {"tr": "Günlük Değişim", "en": "Daily Change"},
    "allocation": {"tr": "Portföy Dağılımı", "en": "Allocation"},
    "pnl_by_position": {"tr": "Pozisyon Bazında K/Z (%)", "en": "P/L by Position (%)"},
    "value_history": {"tr": "Portföy Değeri (zaman içinde)", "en": "Portfolio Value Over Time"},
    "history_hint": {
        "tr": "Uygulamayı her açtığında o günün değeri kaydedilir; grafik zamanla oluşur.",
        "en": "Each time you open the app, today's value is snapshotted; the chart builds over time.",
    },
    "risk_summary": {"tr": "🚨 Aktif Uyarılar", "en": "🚨 Active Alerts"},
    "no_alerts": {"tr": "✅ Şu an kritik uyarı yok.", "en": "✅ No critical alerts right now."},
    "see_alerts": {"tr": "Tümünü Risk & Uyarılar sayfasında gör", "en": "See all on the Risk & Alerts page"},
    # positions page
    "add_position": {"tr": "➕ Pozisyon Ekle", "en": "➕ Add Position"},
    "symbol": {"tr": "Sembol", "en": "Symbol"},
    "symbol_help": {
        "tr": "BIST için .IS ekle (örn: THYAO.IS, ASELS.IS). ABD: AAPL, NVDA...",
        "en": "Add .IS for Istanbul stocks (e.g. THYAO.IS). US: AAPL, NVDA...",
    },
    "quantity": {"tr": "Adet", "en": "Quantity"},
    "avg_cost": {"tr": "Ortalama Maliyet", "en": "Average Cost"},
    "notes": {"tr": "Not (opsiyonel)", "en": "Note (optional)"},
    "add_btn": {"tr": "Portföye Ekle", "en": "Add to Portfolio"},
    "added_ok": {"tr": "✅ {symbol} eklendi.", "en": "✅ {symbol} added."},
    "symbol_not_found": {
        "tr": "⚠️ {symbol} için fiyat bulunamadı — sembolü kontrol et.",
        "en": "⚠️ No price found for {symbol} — check the symbol.",
    },
    "holdings": {"tr": "📋 Pozisyonlarım", "en": "📋 My Holdings"},
    "col_price": {"tr": "Fiyat", "en": "Price"},
    "col_value": {"tr": "Değer", "en": "Value"},
    "col_pnl": {"tr": "K/Z", "en": "P/L"},
    "col_pnl_pct": {"tr": "K/Z %", "en": "P/L %"},
    "col_daily": {"tr": "Günlük %", "en": "Daily %"},
    "col_weight": {"tr": "Ağırlık", "en": "Weight"},
    "sell_reduce": {"tr": "➖ Sat / Azalt", "en": "➖ Sell / Reduce"},
    "sell_qty": {"tr": "Satılacak adet", "en": "Quantity to sell"},
    "sell_btn": {"tr": "Sat", "en": "Sell"},
    "removed_ok": {"tr": "✅ İşlem kaydedildi.", "en": "✅ Recorded."},
    "delete_btn": {"tr": "🗑️ Pozisyonu Sil", "en": "🗑️ Delete Position"},
    "detail_chart": {"tr": "📈 Detay Grafiği", "en": "📈 Detail Chart"},
    "choose_symbol": {"tr": "Hisse seç", "en": "Pick a holding"},
    "cost_line": {"tr": "Maliyetin", "en": "Your cost"},
    "stop_line": {"tr": "ATR Stop Önerisi", "en": "ATR Stop Suggestion"},
    # alerts page
    "alerts_title": {"tr": "🚨 Risk & Uyarı Motoru", "en": "🚨 Risk & Alert Engine"},
    "alerts_intro": {
        "tr": "Portföyünü etkileyebilecek sinyaller aşağıda. Kırmızılar önlem gerektirir.",
        "en": "Signals that can affect your portfolio. Red ones need action.",
    },
    "severity_crit": {"tr": "KRİTİK", "en": "CRITICAL"},
    "severity_warn": {"tr": "UYARI", "en": "WARNING"},
    "severity_info": {"tr": "BİLGİ", "en": "INFO"},
    "stop_table": {"tr": "🛑 ATR Bazlı Stop Önerileri", "en": "🛑 ATR-Based Stop Suggestions"},
    "stop_help": {
        "tr": "Stop = fiyat − {mult}×ATR({period}). Fiyat bu seviyenin altına inerse pozisyonu gözden geçir.",
        "en": "Stop = price − {mult}×ATR({period}). If price falls below, review the position.",
    },
    # alert templates
    "al_below_sma_slow": {
        "tr": "{symbol}: Fiyat 200 günlük ortalamanın ALTINDA — uzun vadeli trend kırık.",
        "en": "{symbol}: Price is BELOW the 200-day average — long-term trend broken.",
    },
    "al_below_sma_fast": {
        "tr": "{symbol}: Fiyat 50 günlük ortalamanın altında — momentum zayıflıyor.",
        "en": "{symbol}: Price below the 50-day average — momentum weakening.",
    },
    "al_rsi_over": {
        "tr": "{symbol}: RSI {value} — aşırı alım bölgesi, kâr realizasyonu gelebilir.",
        "en": "{symbol}: RSI {value} — overbought, pullback risk.",
    },
    "al_rsi_under": {
        "tr": "{symbol}: RSI {value} — aşırı satım bölgesi.",
        "en": "{symbol}: RSI {value} — oversold territory.",
    },
    "al_daily_drop": {
        "tr": "{symbol}: Bugün %{value} düştü — haber akışını kontrol et.",
        "en": "{symbol}: Down {value}% today — check the news flow.",
    },
    "al_loss": {
        "tr": "{symbol}: Maliyetine göre %{value} zararda — stop planını gözden geçir.",
        "en": "{symbol}: {value}% below your cost — review your stop plan.",
    },
    "al_earnings": {
        "tr": "{symbol}: Bilanço tarihi yaklaşıyor ({date}) — oynaklık artabilir.",
        "en": "{symbol}: Earnings coming up ({date}) — expect volatility.",
    },
    "al_concentration": {
        "tr": "{symbol} portföyün %{value}'ini oluşturuyor — konsantrasyon riski.",
        "en": "{symbol} is {value}% of your portfolio — concentration risk.",
    },
    "al_vix": {
        "tr": "VIX {value} — piyasa geneli stres yüksek, pozisyon boyutlarına dikkat.",
        "en": "VIX at {value} — market-wide stress elevated, mind position sizes.",
    },
    "al_near_stop": {
        "tr": "{symbol}: Fiyat ATR stop seviyesine çok yakın ({value}).",
        "en": "{symbol}: Price is very close to its ATR stop ({value}).",
    },
    # cash
    "cash_section": {"tr": "💵 Nakit", "en": "💵 Cash"},
    "cash_hint": {
        "tr": "Nakit portföy toplamına dahil edilir ama kâr/zarara girmez. 0 yazarsan silinir.",
        "en": "Cash counts toward total value but never toward P/L. Enter 0 to remove it.",
    },
    "cash_currency": {"tr": "Para birimi", "en": "Currency"},
    "cash_amount": {"tr": "Tutar", "en": "Amount"},
    "cash_save": {"tr": "Nakdi Kaydet", "en": "Save Cash"},
    "cash_saved": {"tr": "✅ Nakit güncellendi.", "en": "✅ Cash updated."},
    "cash_total": {"tr": "Nakit", "en": "Cash"},
    "cash_weight": {"tr": "Portföyün %{value}'i nakit", "en": "{value}% of the portfolio is cash"},
    "invested": {"tr": "Yatırımda", "en": "Invested"},
    # compare page
    "cmp_title": {"tr": "📈 Getiri Karşılaştırma", "en": "📈 Performance Comparison"},
    "cmp_intro": {
        "tr": "Portföyün diğer yatırım araçlarına göre nasıl gitti? Hepsi aynı para biriminde, başlangıç = 100.",
        "en": "How did your portfolio do versus the alternatives? Same currency for all, start = 100.",
    },
    "cmp_base": {"tr": "Karşılaştırma para birimi", "en": "Compare in"},
    "cmp_period": {"tr": "Dönem", "en": "Period"},
    "per_1m": {"tr": "1 Ay", "en": "1 Month"},
    "per_3m": {"tr": "3 Ay", "en": "3 Months"},
    "per_6m": {"tr": "6 Ay", "en": "6 Months"},
    "per_ytd": {"tr": "Yıl Başı", "en": "YTD"},
    "per_1y": {"tr": "1 Yıl", "en": "1 Year"},
    "cmp_chart": {"tr": "Getiri Yarışı", "en": "Return Race"},
    "cmp_ranking": {"tr": "Sıralama", "en": "Ranking"},
    "cmp_rank_col": {"tr": "Sıra", "en": "Rank"},
    "cmp_asset": {"tr": "Varlık", "en": "Asset"},
    "cmp_return": {"tr": "Getiri", "en": "Return"},
    "cmp_vs": {"tr": "Portföye Fark", "en": "vs Portfolio"},
    "cmp_verdict_win": {
        "tr": "🏆 Portföyün bu dönemde **{beaten}/{total}** kıyas aracını geçti (%{value}).",
        "en": "🏆 Your portfolio beat **{beaten}/{total}** benchmarks this period ({value}%).",
    },
    "cmp_realized": {"tr": "💰 Maliyetine Göre Gerçek K/Z", "en": "💰 Realised P/L vs Your Cost"},
    "cmp_realized_hint": {
        "tr": "Yukarıdaki grafik bugünkü portföyünü geçmişe uygular (al-tut simülasyonu). "
              "Aşağıdaki ise gerçekte ödediğin maliyete göre kâr/zararın.",
        "en": "The chart above replays today's basket over the window (buy-and-hold simulation). "
              "Below is your actual profit against what you really paid.",
    },
    "cmp_no_data": {
        "tr": "Karşılaştırma verisi alınamadı. 🔄 Verileri Yenile ile tekrar dene.",
        "en": "Could not load comparison data. Try 🔄 Refresh Data.",
    },
    "cmp_cash_note": {
        "tr": "ℹ️ Portföyünün %{value}'i nakit — bu, getiri çizgisini doğal olarak aşağı çeker.",
        "en": "ℹ️ {value}% of your portfolio is cash, which naturally dampens the return line.",
    },
    # market compass page
    "mkt_title": {"tr": "🧭 Piyasa Pusulası", "en": "🧭 Market Compass"},
    "mkt_intro": {
        "tr": "Piyasayı okumak için 5 katman + ekonomik takvim — hepsi tek sayfada, her bölümün altında basit anlatım var.",
        "en": "The 5 layers of reading the market + the economic calendar — with a plain-language explainer under each.",
    },
    "mkt_simple": {"tr": "🧒 Basit anlatım", "en": "🧒 Explain it simply"},
    # layer 1: macro
    "mkt_l1_title": {"tr": "1️⃣ Makro Ortam — rüzgar nereden esiyor?", "en": "1️⃣ Macro — which way is the wind blowing?"},
    "mkt_l1_summary": {
        "tr": "Faizler, dolar ve emtialar piyasanın genel yönünü belirler. ABD 10 yıllık faizi hızla yükseliyorsa hisseler (özellikle teknoloji) baskılanır; güçlü dolar gelişen piyasaları ve emtiaları zorlar.",
        "en": "Rates, the dollar and commodities set the market's overall direction. A fast-rising US 10-year yield pressures stocks (especially tech); a strong dollar squeezes emerging markets and commodities.",
    },
    "mkt_l1_simple": {
        "tr": """
Piyasayı bir **denizde yüzen gemiler** gibi düşün. Hisseler gemiler, makro ortam ise **hava durumu**.

- **Faiz** = rüzgarın sertliği. Faiz yükselince (rüzgar sertleşince) gemilerin ilerlemesi zorlaşır. Çünkü insanlar "hisse alacağıma faize yatırırım, garanti para" der.
- **Dolar (DXY)** = denizin akıntısı. Dolar güçlenince bizim gibi ülkelerin parası ve borsası zorlanır.
- **Altın** = can yeleği. İnsanlar korkunca altına koşar.
- **Petrol** = geminin yakıt fiyatı. Pahalanırsa şirketlerin masrafı artar, enflasyon yükselir.

Yani hisse almadan önce gökyüzüne bak: fırtına mı geliyor, güneş mi açıyor? ⛅
""",
        "en": """
Think of the market as **ships on the sea**. Stocks are the ships; macro is the **weather**.

- **Interest rates** = how hard the wind blows. When rates rise, ships struggle — people say "why risk stocks when the bank pays me guaranteed money?"
- **The dollar (DXY)** = the current. A strong dollar drags on emerging markets.
- **Gold** = the life jacket. When people get scared, they grab it.
- **Oil** = fuel prices for the ships. Expensive fuel means higher costs and inflation.

So before buying a stock, look at the sky first: storm coming, or sunshine? ⛅
""",
    },
    # layer 2: internals / breadth
    "mkt_l2_title": {"tr": "2️⃣ Piyasa İçi Göstergeler — yükseliş sağlıklı mı?", "en": "2️⃣ Market Internals — is the rally healthy?"},
    "mkt_l2_summary": {
        "tr": "Endeks yükselirken hisselerin çoğu düşüyorsa ralliyi birkaç dev hisse taşıyordur — bu kırılgandır. Breadth (genişlik), yükselişe kaç hissenin katıldığını ölçer. {size} büyük hisselik örneklemde ölçüm yapılır.",
        "en": "If the index climbs while most stocks fall, a few mega-caps are doing the lifting — that's fragile. Breadth measures how many stocks join the move. Measured on a sample of {size} large caps.",
    },
    "mkt_l2_pct50": {"tr": "SMA50 Üstü", "en": "Above SMA50"},
    "mkt_l2_pct200": {"tr": "SMA200 Üstü", "en": "Above SMA200"},
    "mkt_l2_ad": {"tr": "Yükselen / Düşen (bugün)", "en": "Advancers / Decliners"},
    "mkt_l2_hl": {"tr": "20 Gün Zirve / Dip", "en": "20d Highs / Lows"},
    "mkt_l2_healthy": {"tr": "🟢 Katılım geniş — yükselişin tabanı sağlam.", "en": "🟢 Broad participation — the rally has a solid base."},
    "mkt_l2_mixed": {"tr": "🟡 Katılım karışık — seçici ol.", "en": "🟡 Mixed participation — be selective."},
    "mkt_l2_weak": {"tr": "🔴 Katılım dar — endeksi birkaç hisse taşıyor, dikkat.", "en": "🔴 Narrow participation — a few names carry the index. Careful."},
    "mkt_l2_simple": {
        "tr": """
Sınıfça **halat çekme yarışı** düşün. Endeks = takımın toplam gücü.

Skorborda "takım kazanıyor" yazabilir ama bir bak: halatı gerçekten **kaç kişi çekiyor?**
Eğer 60 kişilik sınıfta halatı sadece 5 güçlü çocuk çekiyor, gerisi elini sürmüyorsa... o 5 çocuk yorulunca yarış biter. 😅

- **SMA200 üstü %60'tan fazlaysa** → neredeyse herkes çekiyor, takım güçlü. 🟢
- **%40'tan azsa** → birkaç kişi çekiyor, her an bırakabilirler. 🔴

Endeksin yükselmesi yetmez; **kaç hissenin katıldığı** önemli. Buna "breadth" (genişlik) denir.
""",
        "en": """
Picture a class **tug-of-war**. The index = the team's total score.

The scoreboard may say "we're winning" — but look closer: **how many kids are actually pulling the rope?**
If only 5 strong kids pull while 55 just stand there... the moment those 5 get tired, it's over. 😅

- **More than 60% above their 200-day average** → almost everyone is pulling. 🟢
- **Less than 40%** → only a few are pulling, and they can let go any time. 🔴

The index going up isn't enough — what matters is **how many stocks join in**. That's "breadth".
""",
    },
    # layer 3: sentiment
    "mkt_l3_title": {"tr": "3️⃣ Duygu & Volatilite — korku mu, iştah mı?", "en": "3️⃣ Sentiment & Volatility — fear or greed?"},
    "mkt_l3_summary": {
        "tr": "VIX, momentum, breadth ve SPY put/call oranından hesaplanan yerli korku/iştah skoru. Aşırı uçlar ters gösterge olabilir: herkes korkarken dipler, herkes iştahlıyken tepeler oluşur.",
        "en": "A home-grown fear/greed score built from VIX, momentum, breadth and the SPY put/call ratio. Extremes are contrarian: bottoms form when everyone is scared, tops when everyone is greedy.",
    },
    "sent_extreme_fear": {"tr": "AŞIRI KORKU", "en": "EXTREME FEAR"},
    "sent_fear": {"tr": "KORKU", "en": "FEAR"},
    "sent_neutral": {"tr": "NÖTR", "en": "NEUTRAL"},
    "sent_greed": {"tr": "İŞTAH", "en": "GREED"},
    "sent_extreme_greed": {"tr": "AŞIRI İŞTAH", "en": "EXTREME GREED"},
    "sent_comp_vix": {"tr": "VIX (korku endeksi)", "en": "VIX (fear index)"},
    "sent_comp_momentum": {"tr": "S&P Momentum", "en": "S&P Momentum"},
    "sent_comp_breadth": {"tr": "Breadth (katılım)", "en": "Breadth"},
    "sent_comp_put_call": {"tr": "SPY Put/Call", "en": "SPY Put/Call"},
    "mkt_l3_vix_zone": {
        "tr": "VIX şu an {vix} — {zone}. (20 altı sakin · 20-30 gergin · 30 üstü panik)",
        "en": "VIX is at {vix} — {zone}. (below 20 calm · 20-30 tense · above 30 panic)",
    },
    "vix_calm": {"tr": "sakin", "en": "calm"},
    "vix_tense": {"tr": "gergin", "en": "tense"},
    "vix_panic": {"tr": "panik", "en": "panic"},
    "mkt_l3_simple": {
        "tr": """
Piyasa aslında **kalabalık bir okul bahçesi** gibidir ve bir duygusu vardır.

- **VIX** = bahçedeki gürültü ölçer. Sessizse (20 altı) herkes sakin oyun oynuyor. Çok gürültülüyse (30 üstü) kavga çıkmış, herkes bağırıyor. 😱
- **Put/Call** = kaç çocuğun yağmurluk giydiği. Güneşli günde bile herkes yağmurluk giymişse, insanlar yağmur (düşüş) bekliyor demektir.

İşin sırrı şurada: **herkes aynı anda korktuğunda** genelde en kötüsü olmuş bitmiştir — akıllı alıcılar o zaman ortaya çıkar. **Herkes aşırı keyifliyken** de dikkat: parti bitmek üzere olabilir. 🎈

Yani bu skor 15'e düştüyse "eyvah" değil, "acaba fırsat mı?" diye düşün. 85'e çıktıysa kemerini bağla.
""",
        "en": """
The market is like a **crowded schoolyard** — and it has a mood.

- **VIX** = the noise meter. Quiet (below 20)? Everyone's playing calmly. Very loud (above 30)? A fight broke out and everyone is screaming. 😱
- **Put/Call** = how many kids are wearing raincoats. If everyone wears one on a sunny day, they must be expecting rain (a fall).

Here's the trick: when **everyone is scared at once**, the worst has usually already happened — smart buyers show up then. When **everyone is cheerful**, careful: the party may be about to end. 🎈

So if this score drops to 15, don't just panic — ask "is this a bargain?". If it hits 85, buckle up.
""",
    },
    # layer 4: money flow
    "mkt_l4_title": {"tr": "4️⃣ Para Akışı — para nereden nereye gidiyor?", "en": "4️⃣ Money Flow — where is money going?"},
    "mkt_l4_summary": {
        "tr": "Döngüsel sektörler (teknoloji, sanayi, finans) öndeyse risk iştahı açık; defansifler (kamu, temel tüketim, sağlık) öndeyse piyasa savunmaya geçmiş demektir. Detaylı harita Sektör Rotasyonu sayfasında.",
        "en": "Cyclicals leading (tech, industrials, financials) = risk-on; defensives leading (utilities, staples, health) = the market is playing defense. The full map lives on the Sector Rotation page.",
    },
    "mkt_l4_leading": {"tr": "Lider sektörler", "en": "Leading sectors"},
    "mkt_l4_lagging": {"tr": "Geride kalanlar", "en": "Lagging sectors"},
    "mkt_l4_simple": {
        "tr": """
Para bir **su** gibidir: asla kaybolmaz, sadece **yer değiştirir**.

Alışveriş merkezini düşün. Bazı günler herkes oyuncakçıya ve teknoloji mağazasına koşar (eğlence modu 🎮), bazı günler herkes market ve eczaneye yığılır (tedbir modu 🛒).

- Oyuncakçı kalabalıksa → insanlar rahat, para **riskli ama kazançlı** yerlere akıyor. Buna **risk-on** denir.
- Eczane kalabalıksa → insanlar endişeli, para **güvenli** yerlere saklanıyor. Buna **risk-off** denir.

Sektör rotasyonu, bu kalabalığın hangi mağazaya doğru yürüdüğünü gösteren güvenlik kamerasıdır. 📹
Sen de "kalabalık nereye gidiyor?" diye bakarsan, tek tek hisse seçmeden önce doğru mağazada olursun.
""",
        "en": """
Money is like **water**: it never disappears, it only **moves**.

Think of a shopping mall. Some days everyone rushes to the toy store and the gadget shop (fun mode 🎮); other days everyone crowds the grocery store and the pharmacy (caution mode 🛒).

- Toy store crowded → people feel safe, money flows into **risky but rewarding** places. That's **risk-on**.
- Pharmacy crowded → people are worried, money hides in **safe** places. That's **risk-off**.

Sector rotation is the mall's security camera showing which store the crowd is walking toward. 📹
Check where the crowd is heading before picking individual stocks — be in the right store first.
""",
    },
    # layer 5: single stock
    "mkt_l5_title": {"tr": "5️⃣ Tek Hisse Katmanı — senin hisselerinde ne oluyor?", "en": "5️⃣ Single-Stock Layer — what's happening in YOUR names?"},
    "mkt_l5_summary": {
        "tr": "Piyasa ne yaparsa yapsın, sonunda senin hisselerin önemli: bilanço tarihi yaklaşan var mı, trend kıran var mı, uyarı var mı? Detaylar Risk & Uyarılar ve Haberler sayfalarında.",
        "en": "Whatever the market does, your own names matter most: any earnings coming, any broken trends, any alerts? Details live on the Risk & Alerts and News pages.",
    },
    "mkt_l5_alerts": {"tr": "Aktif uyarı", "en": "Active alerts"},
    "mkt_l5_crit": {"tr": "{n} kritik", "en": "{n} critical"},
    "mkt_l5_below200": {"tr": "SMA200 altında", "en": "Below SMA200"},
    "mkt_l5_earnings_soon": {"tr": "Bilançosu yaklaşan", "en": "Earnings soon"},
    "mkt_l5_none": {"tr": "yok", "en": "none"},
    "mkt_l5_simple": {
        "tr": """
Buraya kadar hep **ormanı** konuştuk; şimdi sıra **senin ağaçlarında**. 🌳

Her hissen bir saksı bitkisi gibi ve düzenli bakım ister:

- **Bilanço tarihi** = karne günü. Karne gününde sürpriz olur — not iyiyse bitki fırlar, kötüyse yaprak döker. Karne gününü **bilmeden** o bitkiye yeni para koyma.
- **200 günlük ortalama** = bitkinin ana gövdesi. Fiyat bunun altına indiyse gövde eğilmiş demektir; "acaba hasta mı?" diye kontrol et.
- **Stop seviyesi** = "buradan sonra sularım boşa gidiyor" çizgin. Önceden karar verirsen, panik anında duygusal karar vermezsin.

Kural basit: ormanda fırtına varken bile bakımlı ağaç ayakta kalır — ama bakımsız ağaç güneşli günde bile devrilebilir. 🍃
""",
        "en": """
So far we've talked about the **forest**; now it's about **your trees**. 🌳

Each holding is like a potted plant that needs regular care:

- **Earnings date** = report-card day. Surprises happen — a good grade and the plant shoots up, a bad one and leaves drop. Never add money to a plant **without knowing** its report-card day.
- **The 200-day average** = the plant's main stem. If price falls below it, the stem is bending — check whether it's sick.
- **Your stop level** = the line where you say "watering past this is a waste." Decide it in advance so panic never decides for you.

Simple rule: a well-tended tree survives the storm — an ignored one can fall on a sunny day. 🍃
""",
    },
    # economic calendar
    "mkt_cal_title": {"tr": "📅 Ekonomik Takvim — önümüzdeki önemli günler", "en": "📅 Economic Calendar — key dates ahead"},
    "mkt_cal_summary": {
        "tr": "Fed faiz kararları (FOMC) ve ABD istihdam raporu (NFP) piyasanın en oynak günleridir; portföyündeki hisselerin bilanço tarihleriyle birlikte burada. CPI gibi tarihi değişen veriler için resmi takvimleri izle.",
        "en": "Fed decisions (FOMC) and the US jobs report (NFP) are the most volatile days; your holdings' earnings dates are listed too. For shifting releases like CPI, follow the official calendars.",
    },
    "ev_fomc": {"tr": "🏛️ Fed Faiz Kararı (FOMC)", "en": "🏛️ Fed Rate Decision (FOMC)"},
    "ev_nfp": {"tr": "💼 ABD İstihdam Raporu (NFP)", "en": "💼 US Jobs Report (NFP)"},
    "ev_earnings": {"tr": "📊 {symbol} Bilançosu", "en": "📊 {symbol} Earnings"},
    "ev_days_left": {"tr": "{n} gün kaldı", "en": "in {n} days"},
    "ev_today": {"tr": "BUGÜN", "en": "TODAY"},
    "ev_none": {"tr": "Önümüzdeki {n} günde takvimde olay yok.", "en": "No events in the next {n} days."},
    "mkt_cal_simple": {
        "tr": """
Bazı günler **sınav günüdür** ve o günler piyasa deli gibi sallanır. 📅

- **FOMC (Fed toplantısı)** = müdürün tüm okula konuşma yaptığı gün. Müdür "harçlıklar artıyor" derse (faiz indirimi) herkes sevinir; "kısıyoruz" derse suratlar asılır. Yılda 8 kez olur, tarihi **önceden bellidir**.
- **NFP (istihdam raporu)** = her ayın ilk cuması açıklanan okul karnesi. İyi de gelse kötü de gelse büyük dalga yaratır.
- **Bilanço günleri** = senin hisselerinin kendi sınavları.

Altın kural: **Sınav günü büyük iddiaya girme.** O günler pozisyonunu küçük tut, sonucu gör, sonra hareket et. Sınav sonucunu tahmin etmeye çalışmak kumardır. 🎲
""",
        "en": """
Some days are **exam days**, and on those days the market shakes like crazy. 📅

- **FOMC (Fed meeting)** = the principal addressing the whole school. If they say "allowances are going up" (rate cut) everyone cheers; "we're cutting back" and faces drop. Happens 8 times a year, dates known **in advance**.
- **NFP (jobs report)** = the report card released on the first Friday of every month. Good or bad, it makes waves.
- **Earnings days** = your own stocks' private exams.

Golden rule: **don't make big bets on exam day.** Keep positions small, see the result, then act. Guessing exam results is gambling. 🎲
""",
    },
    # options page
    "opt_title": {"tr": "🎯 Opsiyon Radarı", "en": "🎯 Options Radar"},
    "opt_intro": {
        "tr": "Hangi hissede en çok call/put işlemi var? En yakın vade taranır; hacim = bugün işlem gören kontrat sayısı.",
        "en": "Where is the call/put action? Nearest expiry is scanned; volume = contracts traded today.",
    },
    "opt_note": {
        "tr": "Sadece ABD hisseleri/ETF'leri (BIST'te Yahoo üzerinden opsiyon verisi yok). "
              "Veri ~15 dk gecikmeli, kaynak Yahoo Finance. Portföyündeki ABD hisseleri otomatik dahil edilir.",
        "en": "US stocks/ETFs only (no Yahoo option data for BIST). Data ~15 min delayed, from Yahoo Finance. "
              "Your US holdings are scanned automatically.",
    },
    "opt_scanning": {"tr": "Opsiyon zincirleri taranıyor...", "en": "Scanning option chains..."},
    "opt_no_data": {
        "tr": "Opsiyon verisi alınamadı. 🔄 Verileri Yenile ile tekrar dene.",
        "en": "Could not load options data. Try 🔄 Refresh Data.",
    },
    "opt_busiest": {"tr": "En Yüksek Hacim", "en": "Highest Volume"},
    "opt_total_vol": {"tr": "Toplam Hacim (kontrat)", "en": "Total Volume (contracts)"},
    "opt_most_bearish": {"tr": "En Yüksek P/C (put ağırlıklı)", "en": "Highest P/C (put-heavy)"},
    "opt_most_bullish": {"tr": "En Düşük P/C (call ağırlıklı)", "en": "Lowest P/C (call-heavy)"},
    "opt_chart_title": {"tr": "Call / Put Hacmi (en yakın vade)", "en": "Call / Put Volume (nearest expiry)"},
    "opt_table_title": {"tr": "📋 Hacim Sıralaması", "en": "📋 Volume Ranking"},
    "opt_col_expiry": {"tr": "Vade", "en": "Expiry"},
    "opt_col_call": {"tr": "Call Hacmi", "en": "Call Vol"},
    "opt_col_put": {"tr": "Put Hacmi", "en": "Put Vol"},
    "opt_col_total": {"tr": "Toplam", "en": "Total"},
    "opt_col_pcr": {"tr": "Put/Call", "en": "Put/Call"},
    "opt_col_oi": {"tr": "Açık Poz. (OI)", "en": "Open Interest"},
    "opt_col_mood": {"tr": "Eğilim", "en": "Tilt"},
    "mood_bullish": {"tr": "🟢 Call ağırlıklı", "en": "🟢 Call-heavy"},
    "mood_bearish": {"tr": "🔴 Put ağırlıklı", "en": "🔴 Put-heavy"},
    "mood_neutral": {"tr": "⚪ Dengeli", "en": "⚪ Balanced"},
    "opt_pcr_help": {
        "tr": "Put/Call oranı: {bear} üzeri put ağırlıklı (korunma/düşüş beklentisi), "
              "{bull} altı call ağırlıklı (yükseliş spekülasyonu). Tek başına al-sat sinyali değildir.",
        "en": "Put/Call ratio: above {bear} is put-heavy (hedging/bearish), below {bull} is call-heavy "
              "(bullish speculation). Not a trading signal on its own.",
    },
    "opt_detail": {"tr": "🔍 Kontrat Detayı", "en": "🔍 Contract Detail"},
    "opt_detail_pick": {"tr": "Hisse seç", "en": "Pick a symbol"},
    "opt_detail_title": {
        "tr": "{symbol} — en çok işlem gören kontratlar ({expiry} vadesi)",
        "en": "{symbol} — most traded contracts ({expiry} expiry)",
    },
    "opt_col_type": {"tr": "Tür", "en": "Type"},
    "opt_col_strike": {"tr": "Kullanım Fiyatı", "en": "Strike"},
    "opt_col_last": {"tr": "Son Fiyat", "en": "Last"},
    "opt_col_iv": {"tr": "İma Edilen Vol.", "en": "Implied Vol."},
    # rotation page
    "rot_title": {"tr": "🔄 Sektör Rotasyonu", "en": "🔄 Sector Rotation"},
    "rot_intro": {
        "tr": "Para hangi sektörden çıkıp hangisine giriyor? Ok, son 8 haftalık hareketin yönünü gösterir.",
        "en": "Which sectors is money leaving, and where is it going? The arrow shows the last 8 weeks of movement.",
    },
    "rot_chart_title": {"tr": "Rotasyon Haritası (RRG)", "en": "Rotation Map (RRG)"},
    "rot_how_to": {"tr": "❓ Grafik nasıl okunur?", "en": "❓ How to read this chart"},
    "rot_how_to_body": {
        "tr": """
**Yatay eksen (RS-Ratio):** Sektörün S&P 500'e göre gücü. 100'ün sağı = piyasadan güçlü.
**Dikey eksen (RS-Momentum):** Bu gücün artıp artmadığı. 100'ün üstü = güç kazanıyor.

Sektörler normalde **saat yönünde** dolaşır:

| Bölge | Anlamı | Ne yapılır |
|---|---|---|
| 🔵 **İyileşen** (sol üst) | Zayıftı, toparlanıyor | İzleme listesi — erken giriş adayı |
| 🟢 **Lider** (sağ üst) | Güçlü ve güçlenmeye devam ediyor | Trend burada; pozisyon taşınır |
| 🟡 **Zayıflayan** (sağ alt) | Hâlâ güçlü ama momentum kaçıyor | Kâr realizasyonu / stop sıkılaştırma |
| 🔴 **Geride** (sol alt) | Zayıf ve zayıflamaya devam ediyor | Uzak durulur |

**Kuyruk** son 8 haftayı, **ok ucu** bu haftayı gösterir. Ok sağ-yukarı bakıyorsa para o sektöre giriyor demektir.
""",
        "en": """
**Horizontal axis (RS-Ratio):** strength versus the S&P 500. Right of 100 = stronger than the market.
**Vertical axis (RS-Momentum):** whether that strength is still building. Above 100 = gaining.

Sectors normally travel **clockwise**:

| Zone | Meaning | What it implies |
|---|---|---|
| 🔵 **Improving** (top left) | Was weak, now recovering | Watchlist — early entry candidates |
| 🟢 **Leading** (top right) | Strong and getting stronger | Where the trend is; hold positions |
| 🟡 **Weakening** (bottom right) | Still strong but losing steam | Take profits / tighten stops |
| 🔴 **Lagging** (bottom left) | Weak and getting weaker | Stay away |

The **tail** is the last 8 weeks, the **arrowhead** is this week. An arrow pointing up-right means money is flowing in.
""",
    },
    "rot_moves": {"tr": "➡️ Bu Hafta Hangi Hareket Var?", "en": "➡️ This Week's Moves"},
    "rot_no_moves": {
        "tr": "Son 8 haftada bölge değiştiren sektör yok — rotasyon sakin.",
        "en": "No sector changed quadrant in the last 8 weeks — rotation is quiet.",
    },
    "rot_moved": {
        "tr": "**{symbol} · {label}**: {frm} ➡️ {to}",
        "en": "**{symbol} · {label}**: {frm} ➡️ {to}",
    },
    "rot_healthy": {"tr": "doğal rotasyon", "en": "normal rotation"},
    "rot_unusual": {"tr": "sıra dışı sıçrama", "en": "unusual jump"},
    "rot_table": {"tr": "📊 Sektör Performansı", "en": "📊 Sector Performance"},
    "rot_perf_pick": {"tr": "Sıralama dönemi", "en": "Ranking period"},
    "rot_1w": {"tr": "1 Hafta", "en": "1 Week"},
    "rot_1m": {"tr": "1 Ay", "en": "1 Month"},
    "rot_3m": {"tr": "3 Ay", "en": "3 Months"},
    "rot_zone": {"tr": "Bölge", "en": "Zone"},
    "rot_sector": {"tr": "Sektör", "en": "Sector"},
    "rot_include_mine": {
        "tr": "Kendi hisselerimi de haritada göster",
        "en": "Also plot my own holdings",
    },
    "rot_mine_hint": {
        "tr": "Portföyündeki ABD hisseleri aynı haritaya eklenir — sektörlere göre nerede durduklarını görürsün.",
        "en": "Your US holdings are added to the same map so you can see where they sit versus the sectors.",
    },
    "rot_summary": {
        "tr": "Şu an **{leading}** lider bölgede, **{lagging}** geride. Rotasyon yönü: {direction}",
        "en": "Right now **{leading}** are leading and **{lagging}** are lagging. Rotation direction: {direction}",
    },
    "rot_risk_on": {"tr": "🟢 risk iştahı açık (döngüsel sektörler önde)", "en": "🟢 risk-on (cyclicals leading)"},
    "rot_risk_off": {"tr": "🔴 savunmaya geçiş (defansif sektörler önde)", "en": "🔴 risk-off (defensives leading)"},
    "rot_mixed": {"tr": "🟡 karışık, net yön yok", "en": "🟡 mixed, no clear direction"},
    "rot_loading_error": {
        "tr": "Sektör verisi alınamadı. 🔄 Verileri Yenile ile tekrar dene.",
        "en": "Could not load sector data. Try 🔄 Refresh Data.",
    },
    "q_leading": {"tr": "Lider", "en": "Leading"},
    "q_weakening": {"tr": "Zayıflayan", "en": "Weakening"},
    "q_lagging": {"tr": "Geride", "en": "Lagging"},
    "q_improving": {"tr": "İyileşen", "en": "Improving"},
    # news page
    "news_title": {"tr": "📰 Portföy Haberleri", "en": "📰 Portfolio News"},
    "news_intro": {
        "tr": "Portföyündeki hisselerle ilgili son haberler (Yahoo Finance + Google News).",
        "en": "Latest news for your holdings (Yahoo Finance + Google News).",
    },
    "news_filter": {"tr": "Hisseye göre filtrele", "en": "Filter by holding"},
    "news_all": {"tr": "Tümü", "en": "All"},
    "news_none": {
        "tr": "Şu an haber bulunamadı. Birazdan tekrar dene.",
        "en": "No news found right now. Try again shortly.",
    },
}


def t(key: str, lang: str = "tr", **kwargs: object) -> str:
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    template = entry.get(lang) or entry["tr"]
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template
