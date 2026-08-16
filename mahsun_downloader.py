import re
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# Engellenecek reklam ağları ve takipçiler
AD_PATTERNS = [
    "bsky.app", "bluesky", "twitter.com", "x.com", "telegram.org",
    "doubleclick", "googlesyndication", "analytics", "gtag",
    "adcash", "popads", "propeller", "adnxs", "histats", "onclick",
    "adrun", "adserver", "monetag", "traffic", "banner"
]

def main():
    with sync_playwright() as p:
        print("🚀 Mahsun Sports Reklam Kırıcı & M3U8 İndirici Başlatılıyor...\n")
        
        browser_args = [
            '--autoplay-policy=no-user-gesture-required',
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-infobars',
            '--window-size=1366,768',
        ]
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            viewport={'width': 1366, 'height': 768},
            locale='tr-TR',
            timezone_id='Europe/Istanbul',
            extra_http_headers={
                'Referer': 'https://mahsun-amp.click/',
                'Origin': 'https://mahsun-amp.click'
            }
        )

        # Bot tespiti engelleme
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        # Reklam scriptlerini doğrudan ağ seviyesinde iptal et
        def route_handler(route):
            url = route.request.url.lower()
            if any(ad in url for ad in AD_PATTERNS):
                route.abort()
            else:
                route.continue_()

        context.route("**/*", route_handler)

        channels = {
            "androstreamlivebs1": ("BeIN Sports 1", "BeinSports"),
            "androstreamlivebs2": ("BeIN Sports 2", "BeinSports"),
            "androstreamlivebs3": ("BeIN Sports 3", "BeinSports"),
            "androstreamlivebs4": ("BeIN Sports 4", "BeinSports"),
            "androstreamlivebs5": ("BeIN Sports 5", "BeinSports"),
            "androstreamlivebsm1": ("BeIN Sports Max 1", "BeinSports"),
            "androstreamlivebsm2": ("BeIN Sports Max 2", "BeinSports"),
            "androstreamlivebsh": ("BeIN Sports Haber", "BeinSports"),
            "androstreamlivess1": ("S Sport 1", "S Sports"),
            "androstreamlivess2": ("S Sport 2", "S Sports"),
            "androstreamlivessplus1": ("S Sport Plus", "S Sports"),
            "androstreamlivets": ("Tivibu Spor", "Tivibu"),
            "androstreamlivets1": ("Tivibu Spor 1", "Tivibu"),
            "androstreamlivets2": ("Tivibu Spor 2", "Tivibu"),
            "androstreamlivets3": ("Tivibu Spor 3", "Tivibu"),
            "androstreamlivets4": ("Tivibu Spor 4", "Tivibu"),
            "androstreamlivesm1": ("Spor Smart 1", "Smart Sports"),
            "androstreamlivesm2": ("Spor Smart 2", "Smart Sports"),
            "androstreamlivees1": ("Euro Sport 1", "Eurosport"),
            "androstreamlivees2": ("Euro Sport 2", "Eurosport"),
            "androstreamliveidm": ("Idman TV", "Azerbaycan"),
            "androstreamlivecbcs": ("CBC Sport", "Azerbaycan"),
            "androstreamlivetrt1": ("TRT 1", "TRT"),
            "androstreamlivetrts": ("TRT Spor", "TRT"),
            "androstreamlivetrtsy": ("TRT Spor Yildiz", "TRT"),
            "androstreamliveatv": ("ATV", "Ulusal"),
            "androstreamliveas": ("A Spor", "Ulusal"),
            "androstreamlivea2": ("A2", "Ulusal"),
            "androstreamliveht": ("HT Spor", "Ulusal"),
            "androstreamlivenba": ("NBA TV", "NBA"),
            "androstreamlivetv8": ("TV 8", "Ulusal"),
            "androstreamlivetv85": ("TV 8.5", "Ulusal"),
            "androstreamlivetb": ("tabii Spor", "tabii"),
            "androstreamlivetb1": ("tabii Spor 1", "tabii"),
            "androstreamlivetb2": ("tabii Spor 2", "tabii"),
            "androstreamlivetb3": ("tabii Spor 3", "tabii"),
            "androstreamliveexn": ("Exxen TV", "Exxen"),
            "androstreamliveexn1": ("Exxen Sports 1", "Exxen"),
            "androstreamliveexn2": ("Exxen Sports 2", "Exxen"),
            "androstreamliveexn3": ("Exxen Sports 3", "Exxen"),
            "androstreamliveexn4": ("Exxen Sports 4", "Exxen"),
        }

        m3u_content = []
        output_filename = "kanallar_mahsun.m3u8"
        created = 0

        page = context.new_page()
        page.on("popup", lambda popup: popup.close())

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i:02d}/{len(channels)}] {channel_name} ({channel_id})...", end=' ')
                sys.stdout.flush()

                embed_url = f"https://8602741.xyz/event.html?id={channel_id}#amp=1"
                captured_urls = []

                def handle_request(request):
                    try:
                        req_url = request.url
                        req_url_lower = req_url.lower()

                        if ".m3u8" in req_url_lower:
                            if not any(ad in req_url_lower for ad in AD_PATTERNS):
                                captured_urls.append(req_url)
                    except:
                        pass

                page.on("request", handle_request)

                try:
                    page.goto(embed_url, timeout=12000, wait_until='domcontentloaded')
                    page.wait_for_timeout(800)

                    # 1. Adım: Oynatıcı üzerindeki şeffaf reklam katmanlarını kaldır
                    page.evaluate("""() => {
                        // Şeffaf overlay, reklam bloklayıcı ve popunder tetikleyicilerini temizle
                        const adSelectors = [
                            'div[id*="ad"]', 'div[class*="ad"]', 'div[style*="z-index"]',
                            'a[target="_blank"]', 'div[onclick]', 'span[onclick]'
                        ];
                        adSelectors.forEach(sel => {
                            document.querySelectorAll(sel).forEach(el => {
                                if (!el.querySelector('video')) {
                                    el.remove();
                                }
                            });
                        });
                    }""")

                    # 2. Adım: Reklamı geçmek için ekranın ortasına 3 kez tıkla (Multi-click)
                    for _ in range(3):
                        if captured_urls:
                            break
                        page.mouse.click(683, 384)
                        page.wait_for_timeout(600)

                    # 3. Adım: DOM içindeki video etiketini doğrudan oynatmaya zorla
                    if not captured_urls:
                        page.evaluate("""() => {
                            const videos = document.querySelectorAll('video');
                            videos.forEach(v => {
                                v.muted = true;
                                v.play().catch(() => {});
                            });
                            // Clappr oynatıcı varsa başlat
                            if (window.player && typeof window.player.play === 'function') {
                                window.player.play();
                            }
                        }""")

                    # M3U8 isteğinin düşmesini bekle
                    start_time = time.time()
                    while time.time() - start_time < 4:
                        if captured_urls:
                            break
                        page.wait_for_timeout(300)

                    chosen_m3u8 = None
                    if captured_urls:
                        chosen_m3u8 = captured_urls[-1]

                    # 4. Adım: Eğer ağdan düşmediyse sayfa içi JS değişkenlerinden yakala
                    if not chosen_m3u8:
                        js_link = page.evaluate("""() => {
                            if (window.player && window.player.options && window.player.options.source) {
                                return window.player.options.source;
                            }
                            if (window.source) return window.source;
                            if (window.file) return window.file;
                            return null;
                        }""")
                        if js_link and ".m3u8" in js_link:
                            chosen_m3u8 = js_link

                    if chosen_m3u8:
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(chosen_m3u8)
                        print(f"-> ✅ OK ({chosen_m3u8})")
                        created += 1
                    else:
                        print("-> ❌ Link bulunamadı")

                except Exception as e:
                    print(f"-> ❌ Hata: {str(e)[:50]}")
                finally:
                    page.remove_listener("request", handle_request)
                    page.wait_for_timeout(200)

            except Exception as e:
                print(f"-> ❌ Genel hata: {e}")
                continue

        page.close()
        browser.close()

        if created > 0:
            header = f"""#EXTM3U
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36
#EXTVLCOPT:http-referrer=https://mahsun-amp.click/
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36
#EXT-X-REFERER:https://mahsun-amp.click/"""

            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(header + "\n\n")
                f.write("\n".join(m3u_content))
            
            print(f"\n🎉 Tamamlandı! {created} kanal kaydedildi → {output_filename}")
        else:
            print("\n❌ Hiçbir kanal için m3u8 linki yakalanamadı.")

if __name__ == "__main__":
    main()
