"""Faz2 HLS videosunu iki cozunurlukte yerele indirir (segment birlestirme, yeniden
kodlama YOK -> orijinal kalite korunur; olcumun dogru olmasi icin sart).

Kullanim: python scripts/faz2_indir.py [--out veri/faz2]
Cikti   : veri/faz2/faz2_1080p.ts , veri/faz2/faz2_240p.ts
"""
import argparse
import os
import sys
import time
import urllib.request

BASE = 'https://teknofest-arge-turkcell.ercdn.net/hls/4/pZ/faz2/faz2.smil/'
MASTER = BASE + 'playlist.m3u8'


def getir(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def rendition_bul():
    """Master playlist'ten (ad, alt_playlist_url) listesi cikarir."""
    metin = getir(MASTER).decode('utf-8', 'ignore').splitlines()
    out, ad = [], None
    for satir in metin:
        s = satir.strip()
        if s.startswith('#EXT-X-STREAM-INF'):
            ad = 'bilinmeyen'
            for parca in s.split(','):
                if parca.strip().startswith('NAME='):
                    ad = parca.split('=', 1)[1].strip().strip('"')
                elif parca.strip().startswith('RESOLUTION='):
                    ad = ad if ad != 'bilinmeyen' else parca.split('=', 1)[1].strip()
        elif s and not s.startswith('#') and ad:
            out.append((ad, BASE + s))
            ad = None
    return out


def segmentleri_indir(playlist_url, hedef):
    metin = getir(playlist_url).decode('utf-8', 'ignore').splitlines()
    segmentler = [s.strip() for s in metin if s.strip() and not s.startswith('#')]
    toplam = len(segmentler)
    print('  %d segment -> %s' % (toplam, hedef))
    t0 = time.time()
    with open(hedef, 'wb') as f:
        for i, seg in enumerate(segmentler, 1):
            url = seg if seg.startswith('http') else BASE + seg
            for deneme in range(3):
                try:
                    f.write(getir(url))
                    break
                except Exception as e:
                    if deneme == 2:
                        print('    HATA %s: %s' % (seg, e), file=sys.stderr)
                    time.sleep(1)
            if i % 10 == 0 or i == toplam:
                print('    %d/%d (%.0f sn)' % (i, toplam, time.time() - t0))
    return os.path.getsize(hedef)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='veri/faz2')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    for ad, url in rendition_bul():
        etiket = ad.lower().replace(' ', '')
        hedef = os.path.join(a.out, 'faz2_%s.ts' % etiket)
        print('[%s] %s' % (ad, url))
        boyut = segmentleri_indir(url, hedef)
        print('  bitti: %.1f MB\n' % (boyut / 1e6))

    print('Dogrulama:')
    import cv2
    for f in sorted(os.listdir(a.out)):
        if not f.endswith('.ts'):
            continue
        p = os.path.join(a.out, f)
        cap = cv2.VideoCapture(p)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        w, h = int(cap.get(3)), int(cap.get(4))
        cap.release()
        print('  %-22s %dx%d  %.1f fps  %d kare  ~%.1f sn' %
              (f, w, h, fps, n, n / fps if fps else 0))


if __name__ == '__main__':
    main()
