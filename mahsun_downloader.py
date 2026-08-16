import re
import sys
import time
import base64
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Error as PlaywrightError

BLOCKED_DOMAINS = [
    "bsky.app", "bluesky", "twitter.com", "x.com", "telegram.org",
    "t.me", "youtube.com", "facebook.com", "doubleclick", "googlesyndication"
]

def main():
    with sync_playwright() as p:
        print("🚀 Mahsun Sports Script Çözücü & M3U8 İndirici Başlatılıyor...\n")
        
        browser_args = [
            '--autoplay-policy=no-user-gesture-required',
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
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

                # AMP parametresi (#amp=1) ile çağır
                embed_url = f"https://8602741.xyz/event.html?id={channel_id}#amp=1"
                captured_urls = []

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

                try:
                    page.goto(embed_url, timeout=12000, wait_until='domcontentloaded')
                    page.wait_for_timeout(800)

                    # Sayfadaki video/play butonunu tıkla
                    try:
                        page.click('#player, .player, video, button, body', timeout=1000)
                    except:
                        pass

                    # 1. YÖNTEM: Ağ trafiğinden m3u8 yakalama
                    start_time = time.time()
                    while time.time() - start_time < 4:
                        if captured_urls:
                            break
                        page.wait_for_timeout(300)

                    chosen_m3u8 = None
                    if captured_urls:
                        chosen_m3u8 = captured_urls[-1]

                    # 2. YÖNTEM: JS Değişkenlerini (Clappr, JWPlayer, Hls) doğrudan DOM'dan okuma
                    if not chosen_m3u8:
                        try:
                            js_stream = page.evaluate("""() => {
                                // Clappr player kontrolü
                                if (window.player && window.player.options && window.player.options.source) {
                                    return window.player.options.source;
                                }
                                // JWPlayer kontrolü
                                if (window.jwplayer && typeof window.jwplayer === 'function') {
                                    const playlist = window.jwplayer().getPlaylist();
                                    if (playlist && playlist[0] && playlist[0].file) return playlist[0].file;
                                }
                                // Global kaynak değişkenleri
                                if (window.source) return window.source;
                                if (window.file) return window.file;
                                if (window.videoSrc) return window.videoSrc;

                                // Sayfadaki scriptlerin içeriğinde m3u8 ara
                                const scripts = Array.from(document.querySelectorAll('script')).map(s => s.innerText);
                                for (const script of scripts) {
                                    const match = script.match(/https?:\\/\\/[^"'\\s]+?\\.m3u8[^"'\\s]*/i);
                                    if (match) return match[0];
                                }
                                return null;
                            }""")
                            if js_stream and not any(b in js_stream.lower() for b in BLOCKED_DOMAINS):
                                chosen_m3u8 = js_stream
                        except:
                            pass

                    # 3. YÖNTEM: Sayfa HTML Kaynağından Regex ile Çekme
                    if not chosen_m3u8:
                        content = page.content()
                        # Regex ile doğrudan link bulma
                        raw_matches = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', content, re.IGNORECASE)
                        valid_matches = [m for m in raw_matches if not any(b in m.lower() for b in BLOCKED_DOMAINS)]
                        if valid_matches:
                            chosen_m3u8 = valid_matches[-1]

                    # Sonuçları Kaydet
                    if chosen_m3u8:
                        m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}')
                        m3u_content.append(chosen_m3u8)
                        print(f"-> ✅ OK ({chosen_m3u8})")
                        created += 1
                    else:
                        print("-> ❌ Link bulunamadı")
                        # İlk kanalda teşhis için HTML kodunun kısa bir özetini yazdır
                        if i == 1:
                            content = page.content()
                            print(f"\n[Teşhis] İlk kanalın HTML yapısı ({len(content)} karakter):\n{content[:400]}\n...")

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
            print("\n❌ Hiçbir kanal için link yakalanamadı.")

if __name__ == "__main__":
    main()
