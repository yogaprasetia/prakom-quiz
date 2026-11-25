#!/usr/bin/env python3
"""Terbitkan kuis Prakom ke web latihan (https://yogaprasetia.github.io/kuis-prakom/), TANPA mengirim poll Telegram.

Pakai: python3 publish_web.py today.json
- Validasi sama dengan send_polls.py (q <=300, opsi 2-10 & <=100, explanation <=200, answer valid, case <=1500).
- Simpan salinan sebagai q_YYYYMMDD.json (tanggal WIB; bila sudah ada untuk hari ini → q_YYYYMMDD_2.json, dst.).
- Catat soal (+ ringkasan kasus) ke asked.txt agar tidak berulang.
- Bangun ulang data web (kuis-prakom/tools/build_data.py), commit, push ke GitHub Pages.
Cetak baris terakhir: PUBLISHED <file> <jumlah soal>  atau keluar dengan kode != 0 bila gagal.
"""
import datetime, json, os, re, shutil, subprocess, sys

DIR = os.path.dirname(os.path.abspath(__file__))
WEB = os.environ.get("KUIS_WEB_DIR", os.path.join(os.path.dirname(DIR), "kuis-prakom"))
REPO = "yogaprasetia/kuis-prakom"


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, shell=True, text=True, capture_output=True)
    if r.returncode:
        sys.exit(f"Gagal: {cmd}\n{r.stdout}{r.stderr}")
    return r.stdout


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, "today.json")
    Q = json.load(open(src, encoding="utf-8"))
    bad = [i + 1 for i, x in enumerate(Q)
           if not isinstance(x.get("q"), str) or len(x["q"]) > 300 or len(x.get("explanation", "")) > 200
           or not (2 <= len(x.get("options", [])) <= 10) or any(len(o) > 100 for o in x["options"])
           or not isinstance(x.get("answer"), int) or not (0 <= x["answer"] < len(x["options"]))
           or len((x.get("case") or "").strip()) > 1500]
    if bad:
        sys.exit(f"Invalid questions (length/answer): {bad}")

    tgl = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y%m%d")
    dst, n = os.path.join(DIR, f"q_{tgl}.json"), 1
    same = lambda p: os.path.exists(p) and json.load(open(p, encoding="utf-8")) == Q
    while os.path.exists(dst) and not same(dst):
        n += 1
        dst = os.path.join(DIR, f"q_{tgl}_{n}.json")
    already = same(dst)
    if not already:
        shutil.copyfile(src, dst)
        with open(os.path.join(DIR, "asked.txt"), "a", encoding="utf-8") as log:
            for x in Q:
                log.write(x["q"] + "\n")
                case = (x.get("case") or "").strip()
                if case:
                    log.write("  [kasus] " + re.sub(r"\s+", " ", case)[:200] + "\n")

    if not os.path.isdir(WEB):
        run(f"gh repo clone {REPO} {WEB}", os.path.dirname(WEB))
    run("git pull -q --rebase", WEB)
    print(run(f"python3 tools/build_data.py {DIR}", WEB).strip())
    run("git add -A", WEB)
    if subprocess.run("git diff --cached --quiet", cwd=WEB, shell=True).returncode:
        run(f'git commit -qm "feat : kuis harian {tgl}" && git push -q', WEB)
    print(f"PUBLISHED {dst} {len(Q)}")


if __name__ == "__main__":
    main()
