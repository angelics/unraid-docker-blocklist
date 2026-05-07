#!/usr/bin/env python3
import gzip
import io
import json
import os

import requests


def ip_to_int(ip: str) -> int:
    parts = ip.strip().split(".")
    if len(parts) != 4:
        raise ValueError(f"Bad IP: {ip}")
    return (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])


def int_to_ip(i: int) -> str:
    return f"{(i >> 24) & 0xFF}.{(i >> 16) & 0xFF}.{(i >> 8) & 0xFF}.{i & 0xFF}"


def cidr_to_range(cidr: str):
    ip_part, mask_part = cidr.split("/")
    mask = int(mask_part)
    start_int = ip_to_int(ip_part)
    host_bits = 32 - mask
    num_hosts = 1 << host_bits
    end_int = start_int + num_hosts - 1
    return (start_int, end_int)


def parse_p2p_line(line: str):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if ":" not in line:
        return None
    desc, range_part = line.rsplit(":", 1)
    if "-" not in range_part:
        return None
    start_ip, end_ip = range_part.split("-", 1)
    start_int = ip_to_int(start_ip)
    end_int = ip_to_int(end_ip)
    return (start_int, end_int, desc.strip())


def parse_cidr_line(line: str, desc: str = "Block"):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "/" not in line:
        return None
    try:
        start_int, end_int = cidr_to_range(line)
        return (start_int, end_int, desc)
    except Exception:
        return None


def fetch_url(url: str, desc: str = "Block") -> list:
    resp = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    data = resp.content
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            text = gz.read().decode("utf-8", errors="replace")
    except Exception:
        text = data.decode("utf-8", errors="replace")
    entries = []
    for line in text.splitlines():
        parsed = parse_p2p_line(line)
        if parsed:
            entries.append(parsed)
    if not entries:
        for line in text.splitlines():
            parsed = parse_cidr_line(line, desc=desc)
            if parsed:
                entries.append(parsed)
    return entries


def main():
    config_path = os.environ.get("CONFIG_PATH", "/config/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    sources = config.get("sources", [])
    output = config.get("output", "/data/blocklist.p2p")
    os.makedirs(os.path.dirname(output), exist_ok=True)

    def url_to_desc(url: str) -> str:
        base = os.path.basename(url)
        if "-" in base:
            return base.split("-", 1)[0].upper()
        return "Block"

    seen = set()
    out_lines = []
    total = 0
    for url in sources:
        print(f"Fetch: {url}")
        desc = url_to_desc(url)
        try:
            entries = fetch_url(url, desc=desc)
        except Exception as e:
            print(f"Fail {url}: {e}")
            continue
        new_count = 0
        for start, end, entry_desc in entries:
            key = (start, end)
            if key in seen:
                continue
            seen.add(key)
            out_lines.append(f"{entry_desc}:{int_to_ip(start)}-{int_to_ip(end)}")
            new_count += 1
        total += new_count
        print(f"  +{new_count} ranges")

    if total == 0 and os.path.exists(output):
        print(f"Total 0 ranges, keeping existing file -> {output}")
        return

    with open(output, "w", encoding="utf-8", newline="\n") as f:
        for line in out_lines:
            f.write(line + "\n")

    gz_output = output + ".gz"
    with gzip.open(gz_output, "wt", encoding="utf-8", newline="\n") as f:
        for line in out_lines:
            f.write(line + "\n")

    print(f"Total {total} ranges -> {output} (+ {gz_output})")


if __name__ == "__main__":
    main()
