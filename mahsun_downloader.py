import re
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Error as PlaywrightError

AD_PATTERNS = [
    "bsky.app", "bluesky", "twitter.com", "x.com", "telegram.org",
    "doubleclick", "googlesyndication", "analytics", "gtag",
    "adcash", "popads", "propeller", "adnxs", "histats", "onclick",
    "adrun", "adserver", "monetag", "traffic", "banner"
]

def main():
    with sync_playwright() as p:
        print("🚀 Mahsun Sports Teşhis & Ekran Görüntüsü Alıcı Başlatılıyor...\n")
        
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

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        channels = {
            "androstreamlivebs1": ("BeIN Sports 1", "BeinSports"),
            "androstreamlivebs2": ("BeIN Sports 2", "BeinSports"),
            "androstreamlivebs3": ("BeIN Sports 3", "BeinSports"),
            "androstreamlivess1": ("S Sport 1", "S Sports"),
            "androstreamlivetrt1": ("TRT 1", "TRT"),
        }

        m3u_content = []
        output_filename = "kanallar_mahsun.m3u8"
        created = 0
        debug_captured = False

        page = context.new_page()
        page.on("popup", lambda popup: popup.close())

        # Tarayıcı konsol loglarını topla
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

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
                    page.wait_for_timeout(1000)

                    # Sayfada tıklama dene
                    try:
                        page.click('body, video, #player, .player', timeout=1500)
                    except:
                        pass

                    start_time = time.time()
                    while time.time() - start_time < 4:
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

                        # İlk başarısız kanalda EKRAN GÖRÜNTÜSÜ VE HTML KAYDET
                        if not debug_captured:
                            page.screenshot(path="debug_screenshot.png", full_page=True)
                            with open("debug_page.html", "w", encoding="utf-8") as f:
                                f.write(page.content())
                            
                            print("   📸 Ekran görüntüsü kaydedildi → debug_screenshot.png")
                            print("   📄 Sayfa HTML kaydedildi → debug_page.html")
                            
                            if console_logs:
                                print("   ⚠️ Tarayıcı Konsol Kayıtları:")
                                for log in console_logs[-8:]:
                                    print(f"      • {log[:100]}")
                            
                            debug_captured = True

                except Exception as e:
                    print(f"-> ❌ Hata: {str(e)[:50]}")
                finally:
                    page.remove_listener("request", handle_request)

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

if __name__ == "__main__":
    main()
