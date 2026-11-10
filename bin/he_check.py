#!/usr/bin/env python3
import math
import os
import sys

import openslide

H = (0.65, 0.70, 0.29)
E = (0.2159, 0.8012, 0.5581)
DAB = (0.27, 0.57, 0.78)
FIELDS = ["name", "slide", "is_he", "reason", "n_tissue", "n_dark", "n_light",
          "angle_h", "angle_e", "angle_dab"]


def od(v):
    return max(0.0, -math.log10(max(v, 1) / 255))


def angle(u, v):
    nu = math.sqrt(sum(x * x for x in u))
    nv = math.sqrt(sum(x * x for x in v))
    c = sum(a * b for a, b in zip(u, v)) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def classify(img):
    n = n_dark = n_light = 0
    r_sum = g_sum = b_sum = 0
    pixels = getattr(img, "get_flattened_data", img.getdata)()
    for r, g, b in pixels:
        if r < 25 and g < 25 and b < 25:
            n_dark += 1
        elif r > 220 and g > 220 and b > 220:
            n_light += 1
        else:
            n += 1
            r_sum += r
            g_sum += g
            b_sum += b
    out = {"n_tissue": n, "n_dark": n_dark, "n_light": n_light,
           "angle_h": "", "angle_e": "", "angle_dab": ""}
    if n_dark == 0 and n_light == 0:
        return False, "no_background", out
    if n_dark >= n_light:
        return False, "dark_background", out
    if n == 0:
        return False, "no_tissue", out
    mean = (od(r_sum / n), od(g_sum / n), od(b_sum / n))
    if sum(mean) == 0:
        return False, "zero_density", out
    angle_h, angle_e, angle_dab = angle(mean, H), angle(mean, E), angle(mean, DAB)
    out.update(angle_h=round(angle_h, 2), angle_e=round(angle_e, 2), angle_dab=round(angle_dab, 2))
    if angle_dab < angle_e:
        return False, "closer_to_dab", out
    if angle_h < angle_e:
        return False, "closer_to_hematoxylin", out
    return True, "he", out


def main(path, out_dir, name=None):
    name = name or os.path.basename(path)
    os.makedirs(out_dir, exist_ok=True)
    row = {"name": name, "slide": os.path.basename(path)}
    try:
        slide = openslide.OpenSlide(path)
        img = slide.get_thumbnail((1000, 1000)).convert("RGB")
        is_he, reason, details = classify(img)
        row.update(details, is_he=is_he, reason=reason)
        img.thumbnail((400, 400))
        img.save(os.path.join(out_dir, f"{name}.jpg"), quality=85)
    except Exception as err:
        row.update(is_he="error", reason=f"read_error: {type(err).__name__}: {err}".replace("\t", " "))
    with open(os.path.join(out_dir, f"{name}.tsv"), "w") as f:
        f.write("\t".join(FIELDS) + "\n")
        f.write("\t".join(str(row.get(k, "")) for k in FIELDS) + "\n")
    print("\t".join(str(row.get(k, "")) for k in FIELDS))


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: he_check.py <slide> <output_dir> [name]")
    main(*sys.argv[1:])
