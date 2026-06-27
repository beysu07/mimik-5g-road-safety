import os, sys, subprocess, time
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Gece boyunca sirayla: kucuk->buyuk (seatbelt, color, plate)
TASKS = ['train/train_seatbelt.py', 'train/train_color.py', 'train/train_plate.py']

for t in TASKS:
    print(f'=== {time.strftime("%H:%M:%S")} START {t} ===', flush=True)
    rc = subprocess.run([sys.executable, t]).returncode
    print(f'=== {time.strftime("%H:%M:%S")} END   {t} rc={rc} ===', flush=True)
print('=== TUM EGITIMLER BITTI ===', flush=True)
