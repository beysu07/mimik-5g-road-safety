import argparse
from pathlib import Path


def polygon_to_box(values):
    xs = values[0::2]
    ys = values[1::2]
    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys), max(ys)
    return ((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)


def normalize_file(path):
    output = []
    converted = 0
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        fields = line.split()
        if not fields:
            continue
        class_id = int(fields[0])
        values = [float(value) for value in fields[1:]]
        if len(values) == 4:
            box = values
        elif len(values) >= 6 and len(values) % 2 == 0:
            box = polygon_to_box(values)
            converted += 1
        else:
            raise ValueError(f'{path}:{line_no}: gecersiz etiket uzunlugu')
        if class_id != 0 or any(value < 0 or value > 1 for value in box):
            raise ValueError(f'{path}:{line_no}: gecersiz sinif veya koordinat')
        output.append(f'{class_id} ' + ' '.join(f'{value:.8f}' for value in box))
    path.write_text('\n'.join(output) + ('\n' if output else ''), encoding='utf-8')
    return converted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', type=Path)
    args = parser.parse_args()
    converted = 0
    files = list(args.dataset.glob('*/labels/*.txt'))
    for path in files:
        converted += normalize_file(path)
    print(f'{len(files)} etiket dosyasi kontrol edildi; {converted} polygon bbox yapildi.')


if __name__ == '__main__':
    main()
