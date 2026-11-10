#!/usr/bin/env python3
import collections
import csv
import glob
import html
import os
import shutil
import sys

csv.field_size_limit(10**7)
NEAR_TIE_DEGREES = 2.0


def is_he_label(text):
    t = text.strip().upper().replace(" ", "").replace("&", "")
    return t in {"HE", "HESTAIN", "HANDE"}


def margin(row):
    try:
        return float(row["angle_e_minus_h"])
    except ValueError:
        return None


def section(title, rows):
    cards = []
    for r in rows:
        src = f"thumbs/{html.escape(r['name'])}.jpg"
        caption = f"{r['name']}<br>{r['reason']} | label: {r['stain_label'] or 'none'} | h-e margin: {r['angle_e_minus_h'] or 'n/a'}"
        cards.append(f'<figure><img loading="lazy" src="{src}" alt=""><figcaption>{caption}</figcaption></figure>')
    return f"<h2>{html.escape(title)} ({len(rows)})</h2><div class=grid>{''.join(cards)}</div>"


def main(samplesheet, tsv_dir, jpg_dir, out_dir):
    with open(samplesheet, newline="") as f:
        labels = {r["name"]: (r.get("stain_label") or "") for r in csv.DictReader(f)}

    rows = []
    for path in sorted(glob.glob(os.path.join(tsv_dir, "*.tsv"))):
        with open(path, newline="") as f:
            rows.extend(csv.DictReader(f, delimiter="\t"))
    for r in rows:
        r["stain_label"] = labels.get(r["name"], "")
        try:
            r["angle_e_minus_h"] = str(round(float(r["angle_h"]) - float(r["angle_e"]), 2))
        except ValueError:
            r["angle_e_minus_h"] = ""

    fields = ["name", "is_he", "reason", "stain_label", "angle_e_minus_h", "n_tissue", "n_dark", "n_light",
              "angle_h", "angle_e", "angle_dab", "slide"]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "he_check_results.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    kept = [r for r in rows if r["is_he"] == "True"]
    rejected = [r for r in rows if r["is_he"] == "False"]
    errors = [r for r in rows if r["is_he"] == "error"]
    near = [r for r in rows if margin(r) is not None and abs(margin(r)) < NEAR_TIE_DEGREES]
    labelled = [r for r in rows if is_he_label(r["stain_label"])]
    lines = [
        f"slides: {len(rows)}",
        f"kept as h&e: {len(kept)}",
        f"rejected: {len(rejected)}",
        f"could not read: {len(errors)}",
        f"near ties to check by eye (h and e within {NEAR_TIE_DEGREES:g} degrees): {len(near)}",
        "rejected by reason:",
    ]
    lines += [f"  {k}: {v}" for k, v in collections.Counter(r["reason"] for r in rejected).most_common()]
    lines += [
        f"labelled h&e in linkage: {len(labelled)}",
        f"  of those, rejected by the rule: {sum(r['is_he'] == 'False' for r in labelled)}",
        f"not labelled h&e but kept by the rule: {sum(r['is_he'] == 'True' and not is_he_label(r['stain_label']) for r in rows)}",
    ]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(out_dir, "he_check_summary.txt"), "w") as f:
        f.write(text)
    print(text, end="")

    thumbs = os.path.join(out_dir, "thumbs")
    os.makedirs(thumbs, exist_ok=True)
    for jpg in glob.glob(os.path.join(jpg_dir, "*.jpg")):
        shutil.copy(jpg, thumbs)

    near_names = {r["name"] for r in near}
    rejected.sort(key=lambda r: (r["reason"], abs(margin(r)) if margin(r) is not None else 999))
    page = ("<!doctype html><meta charset=utf-8><title>H&amp;E check</title><style>"
            "body{font:14px sans-serif;margin:16px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}"
            "figure{margin:0}img{width:100%;height:auto;border:1px solid #ccc}figcaption{font-size:11px;overflow-wrap:anywhere}</style>"
            f"<h1>H&amp;E check</h1><pre>{html.escape(text)}</pre>"
            + section("Rejected", rejected)
            + section("Kept, near tie", [r for r in kept if r["name"] in near_names])
            + section("Kept", [r for r in kept if r["name"] not in near_names]))
    with open(os.path.join(out_dir, "thumbnails.html"), "w") as f:
        f.write(page)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("usage: he_summary.py <samplesheet.csv> <tsv_dir> <jpg_dir> <output_dir>")
    main(*sys.argv[1:])
