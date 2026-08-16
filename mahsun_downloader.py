import re
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# Engellenecek reklam ve sosyal medya domainleri
BLOCKED_DOMAINS = [
    "bsky.app", "bluesky", "twitter.com", "x.com", "telegram.org",
    "t.me", "youtube.com", "facebook.com", "doubleclick", "googlesyndication",
    "analytics", "gtag"
]

def check_active_domain(context):
    """Mahsun Sports aktif domainini doğrulama."""
    test_urls = [
        "https://mahsun-amp.click/",
        "https://mahsunsports.xyz/",
        "https://mahsunsports46.xyz/",
    ]

    print("\n🔍 Mahsun Sports domain kontrolü yapılıyor...\n")
    page = context.new_page()
    page.on("popup", lambda popup: popup.close())

    for url in test_urls:
        try:
            print(f"   Deniyor → {url}", end=" ")
            response = page.goto(url, timeout=8000, wait_until="domcontentloaded")
            if response and response.ok:
                print("✅ BULUNDU!")
                page.close()
                return url.rstrip("/")
            else:
                print(f"❌ HTTP {response.status if response else 'Yok'}")
        except Exception as e:
            print(f"❌ {str(e)[:40]}")

    page.close()
    return "https://mahsun-amp.click"


def main():
    with sync_playwright() as p:
        print("🚀 Mahsun Sports Iframe Tetikleyici & M3U8 İndirici Başlatılıyor...\n")
        
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
            timezone_id='Europe/Istanbul'
        )

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        domain = check_active_domain(context)
        print(f"\n📡 Kullanılan Domain: {domain}\n")

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

        captured_urls = []

        # m3u8 İsteklerini Yakalayıcı
        def handle_request(request):
            try:
                req_url = request.url
                req_url_lower = req_url.lower()

                if ".m3u8" in req_url_lower:
                    if not any(blocked in req_url_lower for blocked in BLOCKED_DOMAINS):
                        captured_urls.append(req_url)
            except:
                pass

        page.on("request", handle_request)

        # 1. Ana host sayfasına bağlan
        print("🌐 Ana sunucu ortamı hazırlanıyor...")
        try:
            page.goto(domain, timeout=20000, wait_until='domcontentloaded')
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"⚠️ Uyarı: {e}")

        # 2. Kanalları gerçek iframe içinde sırayla çalıştır
        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i:02d}/{len(channels)}] {channel_name} ({channel_id})...", end=' ')
                sys.stdout.flush()

                captured_urls.clear()

                # Sayfa içine iframe enjekte et (Anti-standalone korumasını aşar)
                embed_src = f"https://8602741.xyz/event.html?id={channel_id}"
                page.evaluate(f"""() => {{
                    document.body.innerHTML = '<iframe id="target_player" src="{embed_src}" allow="autoplay; encrypted-media; fullscreen" style="width:800px;height:500px;border:none;"></iframe>';
                }}""")

                # Iframe'in yüklenmesini bekle ve oynatıcıyı tıkla
                page.wait_for_timeout(800)
                try:
                    frame = page.frame_locator("#target_player")
                    frame.locator("body").click(timeout=1500)
                except:
                    pass

                # m3u8 linkinin düşmesini bekle
                start_time = time.time()
                while time.time() - start_time < 5:
                    if captured_urls:
                        break
                    page.wait_for_timeout(300)

                chosen_m3u8 = None
                if captured_urls:
                    chosen_m3u8 = captured_urls[-1]

                if chosen_m3u8:
                    m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                    m3u_content.append(chosen_m3u8)
                    print(f"-> ✅ OK ({chosen_m3u8})")
                    created += 1
                else:
                    print("-> ❌ Link bulunamadı")

            except Exception as e:
                print(f"-> ❌ Hata: {str(e)[:50]}")
                continue

        page.close()
        browser.close()

        if created > 0:
            header = f"""#EXTM3U
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36
#EXTVLCOPT:http-referrer={domain}/
#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36
#EXT-X-REFERER:{domain}/"""

            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(header + "\n\n")
                f.write("\n".join(m3u_content))
            
            print(f"\n🎉 Tamamlandı! {created} kanal kaydedildi → {output_filename}")
        else:
            print("\n❌ Hiçbir kanal için m3u8 linki yakalanamadı.")

if __name__ == "__main__":
    main()
