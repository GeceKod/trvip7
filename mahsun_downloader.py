import re
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# Engellenecek reklam ve sosyal medya domainleri
BLOCKED_DOMAINS = [
    "bsky.app",
    "bluesky",
    "twitter.com",
    "x.com",
    "telegram.org",
    "t.me",
    "youtube.com",
    "facebook.com",
    "doubleclick",
    "googlesyndication",
    "analytics",
    "gtag",
]

def main():
    with sync_playwright() as p:
        print("🚀 Mahsun Sports Canlı Teşhis ve M3U8 İndirici Başlatılıyor...\n")
        
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-infobars',
            '--window-size=1366,768',
        ]
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        
        # Tarayıcı başlıklarını doğal Iframe isteği gibi hazırla
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            viewport={'width': 1366, 'height': 768},
            locale='tr-TR',
            timezone_id='Europe/Istanbul',
            extra_http_headers={
                'Referer': 'https://mahsun-amp.click/',
                'Origin': 'https://mahsun-amp.click',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
            }
        )

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        # İlk test edilecek kanallar
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

        regex_fallback = re.compile(
            r'["\'](https?://[^"\'\s]+?/[^"\'\s]+?\.m3u8[^"\'\s]*)["\']',
            re.IGNORECASE
        )

        page = context.new_page()
        page.on("popup", lambda popup: popup.close())

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"\n[{i:02d}/{len(channels)}] 📡 {channel_name} ({channel_id}) taranıyor...")
                sys.stdout.flush()

                embed_url = f"https://8602741.xyz/event.html?id={channel_id}"
                captured_urls = []
                network_logs = []

                # Tüm ağ trafiğini kaydet (Teşhis için)
                def handle_response(response):
                    try:
                        r_url = response.url
                        r_url_lower = r_url.lower()
                        status = response.status

                        # m3u8 veya yayın sunucusu isteklerini yakala
                        if ".m3u8" in r_url_lower or "andro" in r_url_lower or "evrenesoglu" in r_url_lower:
                            network_logs.append(f"HTTP {status} -> {r_url[:80]}")

                        if ".m3u8" in r_url_lower:
                            if not any(b in r_url_lower for b in BLOCKED_DOMAINS):
                                captured_urls.append(r_url)
                    except:
                        pass

                page.on("response", handle_response)

                try:
                    response = page.goto(embed_url, timeout=12000, wait_until='domcontentloaded')
                    http_status = response.status if response else "Yok"
                    title = page.title()
                    print(f"   ↳ Sayfa Durumu: HTTP {http_status} | Başlık: {title[:30]}")

                    # Sayfada oynatıcı tetikle
                    page.wait_for_timeout(1000)
                    try:
                        page.click('body, video, iframe', timeout=1500)
                    except:
                        pass

                    # 4 saniye m3u8 düşmesini bekle
                    start_time = time.time()
                    while time.time() - start_time < 5:
                        if captured_urls:
                            break
                        page.wait_for_timeout(400)

                    # Ağ teşhis kayıtlarını yazdır
                    if network_logs:
                        print("   ↳ Ağ Trafiği:")
                        for log in network_logs[:3]:
                            print(f"      • {log}")

                    # Link seçimi
                    chosen_m3u8 = None
                    if captured_urls:
                        chosen_m3u8 = captured_urls[-1]

                    if chosen_m3u8:
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(chosen_m3u8)
                        print(f"   ↳ ✅ BULUNDU: {chosen_m3u8}")
                        created += 1
                    else:
                        # Sayfa içi JS regex kontrolü
                        content = page.content()
                        match = regex_fallback.search(content)
                        if match and not any(b in match.group(1).lower() for b in BLOCKED_DOMAINS):
                            stream_url = match.group(1)
                            m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                            m3u_content.append(stream_url)
                            print(f"   ↳ ✅ Regex ile Bulundu: {stream_url}")
                            created += 1
                        else:
                            print("   ↳ ❌ Link bulunamadı.")
                            if "Just a moment" in content or "Cloudflare" in content:
                                print("   ↳ ⚠️ Cloudflare/Bot doğrulamasına takıldı (GitHub Actions IP engeli).")

                except Exception as e:
                    print(f"   ↳ ❌ Hata: {str(e)[:60]}")
                finally:
                    page.remove_listener("response", handle_response)

            except Exception as e:
                print(f"❌ Genel hata: {e}")
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
            print("\n❌ Hiçbir kanal için link yakalanamadı.")

if __name__ == "__main__":
    main()
