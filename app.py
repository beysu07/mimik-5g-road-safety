import os
import sys
import json
import traceback


def main():
    # FTR varsayilan yollari; lokal testte argv ile override edilebilir
    inp = os.environ.get('VIDEO_PATH', '/app/data/input/video.mp4')
    out = os.environ.get('OUTPUT_PATH', '/app/data/output/results.json')
    if len(sys.argv) > 1:
        inp = sys.argv[1]
    if len(sys.argv) > 2:
        out = sys.argv[2]

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    result = {'video_id': os.path.basename(inp), 'arac_bilgisi': {}, 'tespitler': []}
    try:
        from src.predict import Pipeline
        result = Pipeline().run(inp)
    except Exception:
        traceback.print_exc()  # cokmeyi engelle, gecerli JSON yine de yaz

    with open(out, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('YAZILDI ->', out)


if __name__ == '__main__':
    main()
