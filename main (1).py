#!/usr/bin/env python3
"""The World in One Day -- Thursday 19 November 2026.

A program that draws one newspaper front page summing up the day's
world news and writes it to /output/entry.png. Pure standard library:
no network, no third-party packages, fully deterministic, so two runs
write identical bytes.
"""
import os
import struct
import zlib

# --- 8x8 public-domain bitmap font (IBM VGA based, font8x8_basic) ---
# Each glyph is 8 bytes written as 16 hex chars; byte r is row r and
# bit 0 of a byte is the leftmost pixel. Keys are ASCII codes 32..126.
FONT = {
    32: "0000000000000000", 33: "183c3c1818001800",
    34: "3636000000000000", 35: "36367f367f363600",
    36: "0c3e031e301f0c00", 37: "006333180c666300",
    38: "1c361c6e3b336e00", 39: "0606030000000000",
    40: "180c0606060c1800", 41: "060c1818180c0600",
    42: "00663cff3c660000", 43: "000c0c3f0c0c0000",
    44: "00000000000c0c06", 45: "0000003f00000000",
    46: "00000000000c0c00", 47: "6030180c06030100",
    48: "3e63737b6f673e00", 49: "0c0e0c0c0c0c3f00",
    50: "1e33301c06333f00", 51: "1e33301c30331e00",
    52: "383c36337f307800", 53: "3f031f3030331e00",
    54: "1c06031f33331e00", 55: "3f3330180c0c0c00",
    56: "1e33331e33331e00", 57: "1e33333e30180e00",
    58: "000c0c00000c0c00", 59: "000c0c00000c0c06",
    60: "180c0603060c1800", 61: "00003f00003f0000",
    62: "060c1830180c0600", 63: "1e3330180c000c00",
    64: "3e637b7b7b031e00", 65: "0c1e33333f333300",
    66: "3f66663e66663f00", 67: "3c66030303663c00",
    68: "1f36666666361f00", 69: "7f46161e16467f00",
    70: "7f46161e16060f00", 71: "3c66030373667c00",
    72: "3333333f33333300", 73: "1e0c0c0c0c0c1e00",
    74: "7830303033331e00", 75: "6766361e36666700",
    76: "0f06060646667f00", 77: "63777f7f6b636300",
    78: "63676f7b73636300", 79: "1c36636363361c00",
    80: "3f66663e06060f00", 81: "1e3333333b1e3800",
    82: "3f66663e36666700", 83: "1e33070e38331e00",
    84: "3f2d0c0c0c0c1e00", 85: "3333333333333f00",
    86: "33333333331e0c00", 87: "6363636b7f776300",
    88: "6363361c1c366300", 89: "3333331e0c0c1e00",
    90: "7f6331184c667f00", 91: "1e06060606061e00",
    92: "03060c1830604000", 93: "1e18181818181e00",
    94: "081c366300000000", 95: "00000000000000ff",
    96: "0c0c180000000000", 97: "00001e303e336e00",
    98: "0706063e66663b00", 99: "00001e3303331e00",
    100: "3830303e33336e00", 101: "00001e333f031e00",
    102: "1c36060f06060f00", 103: "00006e33333e301f",
    104: "0706366e66666700", 105: "0c000e0c0c0c1e00",
    106: "300030303033331e", 107: "070666361e366700",
    108: "0e0c0c0c0c0c1e00", 109: "0000337f7f6b6300",
    110: "00001f3333333300", 111: "00001e3333331e00",
    112: "00003b66663e060f", 113: "00006e33333e3078",
    114: "00003b6e66060f00", 115: "00003e031e301f00",
    116: "080c3e0c0c2c1800", 117: "0000333333336e00",
    118: "00003333331e0c00", 119: "0000636b7f7f3600",
    120: "000063361c366300", 121: "00003333333e301f",
    122: "00003f190c263f00", 123: "380c0c070c0c3800",
    124: "1818180018181800", 125: "070c0c380c0c0700",
    126: "6e3b000000000000",
}

# --- world land mask, 80 columns x 40 rows, equirectangular ---
# Row r covers latitude 90-(r+0.5)*4.5; each hex digit holds 4 columns
# and bit j of the digit is column 4*i+j (LSB first).
MAP = [
    "00000000000000000000", "00000008300000000000",
    "0000e6fff08000040000", "0001008f7000018f0000",
    "0f9c381f70070affff74", "dfffffffff7210000000",
    "8fff781000eeffffff73", "018ff930008efffff780",
    "000fff7008efffffff00", "000fff3008fffffff700",
    "000fff000c536ffff900", "000ef7000c8c7fff3100",
    "000cf7000c30ffff7200", "000c70000cffffff7000",
    "000030000eff79ff3000", "000029000fffe17e0000",
    "0000c1000ffff03c0000", "000000100eff30280000",
    "000008700eff70040000", "000008f100cf30002000",
    "00000cf300cf10047400", "00000cff008f10080810",
    "000008ff008f10000000", "000008f7008f50000b00",
    "000000f7008f4000cf11", "000000f1008f0000ef30",
    "000000f100070000cf30", "000000f000030000c830",
    "00000070000000000818", "00000030000000000014",
    "00000810000000000000", "00000850000000000000",
    "00000000000000000000", "00000000000000000000",
    "00000000000000000000", "000000300008f7efff70",
    "0004cf300efffffffff1", "0efff702fffffffffff1",
    "0cfffffffffffffffff1", "00000000000000000000",
]

W, H = 1024, 1024
PAPER = (247, 242, 231)
INK = (26, 26, 26)
RED = (168, 35, 42)
NAVY = (22, 50, 79)
TEAL = (15, 118, 110)
GOLD = (176, 124, 18)
SKY = (214, 231, 243)
SAND = (232, 222, 196)
GREY = (110, 108, 100)
WHITE = (255, 255, 255)
GREEN = (46, 125, 50)
ORANGE = (214, 106, 24)


class Canvas:
    def __init__(self):
        self.px = bytearray(PAPER * (W * H))

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * W + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            d = r * r - (yy - cy) ** 2
            dx = int(d ** 0.5) if d >= 0 else 0
            self.hline(cx - dx, yy, 2 * dx + 1, c)

    def poly(self, pts, c):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(int(x1 + (y - y1) * (x2 - x1) / (y2 - y1)))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(xs[i], y, xs[i + 1] - xs[i] + 1, c)

    # -- text ---------------------------------------------------------
    def glyph(self, x, y, s, code, c, bold=False):
        g = FONT.get(code)
        if g is None:
            return
        data = bytes.fromhex(g)
        dx = max(1, s // 2) if bold else 0
        for r in range(8):
            byte = data[r]
            if not byte:
                continue
            for col in range(8):
                if byte & (1 << col):
                    self.rect(x + col * s, y + r * s, s, s, c)
                    if dx:
                        self.rect(x + col * s + dx, y + r * s, s, s, c)

    def text(self, x, y, s, txt, c, bold=False):
        cx = x
        for ch in txt:
            code = ord(ch)
            if 32 <= code <= 126:
                self.glyph(cx, y, s, code, c, bold)
            cx += 8 * s
        return cx - x

    def text_w(self, s, txt):
        return 8 * s * len(txt)

    def wrap(self, txt, s, max_w):
        lines = []
        for para in txt.split("\n"):
            words = para.split(" ")
            cur = ""
            for wd in words:
                trial = wd if not cur else cur + " " + wd
                if self.text_w(s, trial) <= max_w or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = wd
            if cur or not lines:
                lines.append(cur)
        return lines

    def para(self, x, y, s, txt, c, max_w, leading=None, bold=False):
        if leading is None:
            leading = 8 * s + 3
        for ln in self.wrap(txt, s, max_w):
            self.text(x, y, s, ln, c, bold)
            y += leading
        return y

    # -- output -------------------------------------------------------
    def png(self, path):
        raw = bytearray()
        stride = W * 3
        for yy in range(H):
            raw.append(0)
            raw += self.px[yy * stride:(yy + 1) * stride]
        comp = zlib.compress(bytes(raw), 9)

        def chunk(kind, data):
            out = struct.pack(">I", len(data)) + kind + data
            out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            return out

        ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
        data = b"\x89PNG\r\n\x1a\n"
        data += chunk(b"IHDR", ihdr)
        data += chunk(b"IDAT", comp)
        data += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(data)
        return len(data)


# --- small drawn scenes ---------------------------------------------
def scene_skyline(c, x, y, w, h):
    c.rect(x, y, w, h, SKY)
    c.circle(x + int(w * 0.78), y + 14, 9, GOLD)
    tops = [0.45, 0.30, 0.55, 0.22, 0.40, 0.33]
    bw = w // len(tops)
    for i, t in enumerate(tops):
        bh = int(h * t) + 8
        c.rect(x + i * bw + 2, y + h - bh, bw - 4, bh, NAVY)
        for wy in range(y + h - bh + 4, y + h - 4, 7):
            c.rect(x + i * bw + 5, wy, 3, 3, GOLD)
    c.rect(x + 2 * bw + 6, y + h - int(h * 0.55) - 12, 2, 12, RED)
    c.poly([(x + 2 * bw + 8, y + h - int(h * 0.55) - 12),
            (x + 2 * bw + 20, y + h - int(h * 0.55) - 8),
            (x + 2 * bw + 8, y + h - int(h * 0.55) - 4)], RED)


def scene_chart(c, x, y, w, h):
    c.rect(x, y, w, h, (16, 68, 54))
    for gy in range(y + 8, y + h - 4, 10):
        c.hline(x + 4, gy, w - 8, (255, 255, 255), 1)
    pts = []
    n = 6
    for i in range(n):
        bx = x + 10 + i * ((w - 20) // n)
        bh = 10 + i * 4
        by = y + h - 8 - bh
        col = GREEN if i % 2 == 0 else (214, 48, 49)
        c.rect(bx, by, 10, bh, col)
        pts.append((bx + 5, by))
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GOLD, 2)


def scene_sunset(c, x, y, w, h):
    c.rect(x, y, w, h, (58, 32, 92))
    c.circle(x + int(w * 0.5), y + int(h * 0.62), 13, ORANGE)
    for sx, sy in [(20, 8), (60, 14), (250, 6), (290, 16)]:
        c.rect(x + sx, y + sy, 2, 2, WHITE)
    for i, bh in enumerate([16, 26, 12, 30, 18]):
        bw = w // 5
        c.rect(x + i * bw + 1, y + h - bh, bw - 2, bh, (24, 16, 44))


def band(c, x, y, w, h, bg, kind):
    c.rect(x, y, w, h, bg)
    cx, cy = x + w // 2, y + h // 2
    if kind == "sun":
        c.circle(cx, cy, 8, GOLD)
        for dx, dy in [(-14, 0), (14, 0), (0, -12), (0, 12)]:
            c.line(cx + dx, cy + dy, cx + dx * 2, cy + dy * 2, GOLD, 2)
    elif kind == "wave":
        for k, yy in enumerate([cy - 4, cy + 4]):
            pts = [(x + 6 + i * 14, yy + (4 if i % 2 else -4))
                   for i in range((w - 12) // 14 + 1)]
            for i in range(len(pts) - 1):
                c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                       WHITE, 2)
    elif kind == "flag":
        c.rect(cx - 2, y + 4, 3, h - 8, WHITE)
        c.poly([(cx + 1, y + 5), (cx + 26, y + 10), (cx + 1, y + 15)], RED)
    elif kind == "ship":
        c.poly([(cx - 26, cy + 2), (cx + 26, cy + 2), (cx + 18, cy + 10),
                (cx - 18, cy + 10)], INK)
        c.rect(cx - 6, cy - 8, 8, 10, INK)
    elif kind == "frame":
        c.frame(cx - 22, cy - 10, 44, 20, GOLD, 2)
        c.circle(cx - 8, cy - 3, 4, ORANGE)
        c.hline(cx - 16, cy + 5, 32, TEAL, 2)
    elif kind == "bars":
        for i, bh in enumerate([10, 18, 8, 22, 14]):
            c.rect(cx - 26 + i * 11, cy + 12 - bh, 7, bh, WHITE)
    elif kind == "note":
        c.circle(cx - 8, cy + 4, 5, WHITE)
        c.rect(cx - 3, cy - 10, 3, 14, WHITE)
        c.poly([(cx, cy - 10), (cx + 12, cy - 6), (cx, cy - 2)], WHITE)
    elif kind == "peak":
        c.poly([(cx - 28, cy + 10), (cx - 8, cy - 10), (cx + 6, cy + 10)],
               WHITE)
        c.poly([(cx - 2, cy + 10), (cx + 14, cy - 4), (cx + 28, cy + 10)],
               (200, 200, 200))
    elif kind == "court":
        c.poly([(cx - 24, cy - 8), (cx, cy - 14), (cx + 24, cy - 8)], WHITE)
        for dx in (-18, 0, 18):
            c.rect(cx + dx - 2, cy - 8, 4, 18, WHITE)
        c.rect(cx - 26, cy + 10, 52, 3, WHITE)
    elif kind == "bolt":
        c.poly([(cx + 2, cy - 12), (cx - 8, cy + 2), (cx - 1, cy + 2),
                (cx - 3, cy + 12), (cx + 8, cy - 2), (cx + 1, cy - 2)],
               GOLD)


# --- stories ---------------------------------------------------------
# (number, place, topic, headline, summary, scene kind, scene bg)
TOP3 = [
    (1, "SHENZHEN", "SUMMIT",
     "Trump, Xi and Putin hold first three-way summit",
     "The three nuclear powers meet at APEC in Shenzhen; arms control "
     "and the Iran war top the agenda.",
     "skyline"),
    (2, "MIAMI", "GAMES",
     "GTA VI arrives after a 13-year wait",
     "Rockstar's sequel launches worldwide; Miami turns into Vice City "
     "for a festival as critics call it a masterpiece.",
     "sunset"),
    (3, "NASDAQ", "MARKETS",
     "Anthropic debuts in the biggest IPO on record",
     "The Claude maker lists on Nasdaq as ANT at $83; $81.3bn raised, "
     "the biggest IPO on record.",
     "chart"),
]

SMALL9 = [
    (4, "THE HAGUE", "LAW",
     "World Court rules on Rohingya case",
     "The ICJ rules in Gambia's case over the 2017 campaign; 730,000 fled.",
     "court", NAVY),
    (5, "ANTALYA", "CLIMATE",
     "COP31 enters its final 48 hours",
     "Ministers take over the text; the $120bn adaptation fund is still open.",
     "sun", (176, 124, 18)),
    (6, "ODISHA", "STORM",
     "Akvan bears down as 72,000 flee",
     "Red alerts in 11 districts as the cyclone nears landfall near Gopalpur.",
     "wave", TEAL),
    (7, "BERLIN", "DIPLOMACY",
     "Allies rally behind Kyiv in Berlin",
     "Merz hosts the Coalition of the Willing as Europe fears a Shenzhen deal.",
     "flag", NAVY),
    (8, "GAZA", "WAR",
     "Israeli tanks cross the Yellow Line",
     "A rare ground raid in central Gaza raises fears for the fragile truce.",
     "bars", (120, 60, 40)),
    (9, "GULF", "WAR",
     "Iran hits back across the Gulf",
     "Tehran strikes Gulf states after US raids on Qeshm island; oil spikes.",
     "ship", (30, 70, 90)),
    (10, "NEW YORK", "ART",
     "Van Gogh sells for a record $190.4m",
     "The painting sets a new auction high for the artist after a Nazi-era row.",
     "frame", (60, 40, 80)),
    (11, "LONDON", "WAR",
     "UK sends Ukraine 1,000 drones",
     "Britain will provide 1,000 long-range strike drones, the BBC reports.",
     "bolt", (90, 90, 90)),
    (12, "LAGOS", "MUSIC",
     "Fela Kuti enters the Rock Hall",
     "The Afrobeat legend is the first Africa-born musician inducted.",
     "note", (120, 40, 90)),
]

BRIEFS = [
    "13 CRIMEA - Bridge hit again.",
    "14 N KOREA - Enrichment up.",
    "15 GAZA - Floods swamp camps.",
    "16 US - Measles status lost.",
    "17 ALASKA - Dems win 56 seats.",
    "18 HOUSE - Epstein files vote.",
    "19 HUANG - Nvidia chief exits.",
    "20 JAKARTA - Asset seizure.",
    "21 N KOREA - First AI chatbot.",
    "22 EGYPT - $2.3B IMF deal.",
    "23 CRICKET - NZ 60/4 vs India.",
    "24 ENGLAND - Win by 97 runs.",
    "25 TENNIS - Alcaraz in semis.",
    "26 CHELSEA - Top Women's CL.",
    "27 EU - Sanctions +3 years.",
    "28 ABU DHABI - Talks stall.",
    "29 LATAM - Peru fuel crisis.",
    "30 SCIENCE - Gravity message.",
    "31 SUNEUNG - 551,864 sit exam.",
    "32 FLORIDA - 15.3in rain.",
    "33 CANBERRA - Jobless 4.9%.",
    "34 BANGLADESH - 4 killed.",
    "35 RIYADH - Missile hits.",
    "36 TSMC - China chip curbs.",
]

STATS = [
    ("EUROPE", "8", "1,000", "UK strike drones for Ukraine", (30, 90, 160)),
    ("AMERICAS", "9", "$81.3bn", "Anthropic IPO, biggest ever", (20, 110, 60)),
    ("ASIA-PACIFIC", "9", "72,000", "evacuated ahead of Akvan", RED),
    ("MIDEAST", "5", "730,000", "Rohingya who fled in 2017", (160, 90, 20)),
    ("AFRICA", "2", "$2.3bn", "Egypt IMF deal", (176, 124, 18)),
    ("OCEANIA", "2", "97 runs", "England's ODI win margin", TEAL),
    ("WORLD", "1", "1st", "gravity message sent", GREY),
]

# (lon, lat) of the 12 featured stories, for the map dots.
DOTS = [
    (114.1, 22.5), (-80.2, 25.8), (-74.0, 40.7), (4.3, 52.1),
    (30.7, 36.9), (84.9, 19.3), (13.4, 52.5), (34.5, 31.5),
    (56.3, 26.6), (-74.0, 40.7), (-0.1, 51.5), (3.4, 6.5),
]

DATECHECK = ("DATE CHECK - First reported Wed 18 Nov, not today's news: "
             "EU's 45bn euro Ukraine loan - Jeffries nominated - "
             "Voyager 1 crosses one light-day - US-Venezuela deal signed - "
             "Pew: Islam largest by 2035.")

FOOTER = ("Every story here happened, or was first reported, on Thursday "
          "19 November 2026. Sources: Reuters, AP, AFP, BBC.")


def draw_map(c, x, y):
    c.rect(x, y, 460, 168, NAVY)
    cell = 4
    ox, oy = x + 70, y + 4
    for r in range(40):
        row = MAP[r]
        for col in range(80):
            nib = int(row[col // 4], 16)
            if (nib >> (col % 4)) & 1:
                c.rect(ox + col * cell + 1, oy + r * cell + 1, 2, 2, SAND)
    for i, (lon, lat) in enumerate(DOTS, 1):
        px = ox + int((lon + 180) / 360 * 80 * cell)
        py = oy + int((90 - lat) / 180 * 40 * cell)
        if i == 3:
            px -= 10
            py -= 4
        if i == 10:
            px += 8
        c.circle(px, py, 9, RED)
        num = str(i)
        nx = px - (4 if len(num) == 1 else 8)
        c.text(nx, py - 4, 1, num, WHITE, bold=True)


def build():
    c = Canvas()
    # masthead
    c.hline(24, 10, 976, RED, 3)
    t = "THE WORLD IN ONE DAY"
    c.text((W - c.text_w(2, t)) // 2, 20, 2, t, RED, bold=True)
    r = "ONE PAGE - 36 STORIES"
    c.text(W - 24 - c.text_w(1, r), 22, 1, r, GREY)
    title = "Thursday 19 November 2026"
    c.text((W - c.text_w(4, title)) // 2, 42, 4, title, INK, bold=True)
    sub = "Shenzhen summit - Myanmar verdict - Biggest IPO on record"
    c.text((W - c.text_w(2, sub)) // 2, 80, 2, sub, RED)
    c.hline(24, 100, 976, INK, 2)
    # stat bar
    colw = 976 // 7
    for i, (name, cnt, big, cap, col) in enumerate(STATS):
        cx = 24 + i * colw
        label = name + " " + cnt
        c.text(cx + (colw - c.text_w(1, label)) // 2, 108, 1, label, col,
               bold=True)
        c.text(cx + (colw - c.text_w(2, big)) // 2, 122, 2, big, INK,
               bold=True)
        c.para(cx + 6, 146, 1, cap, GREY, colw - 12, leading=10)
        if i:
            c.vline(cx, 108, 58, (210, 205, 190), 1)
    c.hline(24, 178, 976, INK, 1)
    # top 3 stories
    scenes = {"skyline": scene_skyline, "chart": scene_chart,
              "sunset": scene_sunset}
    for i, (num, place, topic, head, summ, kind) in enumerate(TOP3):
        x = 24 + i * (314 + 17)
        y = 188
        scenes[kind](c, x, y, 314, 48)
        kick = "%d - %s - %s" % (num, place, topic)
        c.text(x, y + 56, 1, kick, RED, bold=True)
        y2 = c.para(x, y + 70, 2, head, INK, 314, leading=19, bold=True)
        c.para(x, y2 + 4, 1, summ, INK, 314, leading=11)
    c.hline(24, 372, 976, INK, 1)
    # 9 small stories, 3 rows
    for r in range(3):
        for k in range(3):
            idx = r * 3 + k
            num, place, topic, head, summ, kind, bg = SMALL9[idx]
            x = 24 + k * (314 + 17)
            y = 382 + r * 116
            band(c, x, y, 314, 30, bg, kind)
            kick = "%d - %s - %s" % (num, place, topic)
            c.text(x, y + 36, 1, kick, RED, bold=True)
            y2 = c.para(x, y + 49, 2, head, INK, 314, leading=19, bold=True)
            c.para(x, y2 + 3, 1, summ, INK, 314, leading=11)
    # map + briefs
    my = 736
    c.text(24, my, 1, "WHERE IT HAPPENED", RED, bold=True)
    draw_map(c, 24, my + 14)
    c.text(24, my + 188, 1, "Red numbers mark stories 1-12.", GREY)
    bx = 510
    c.text(bx, my, 1, "ALSO ON THURSDAY 19 NOVEMBER - 24 MORE STORIES", RED,
           bold=True)
    for i, b in enumerate(BRIEFS):
        col = i // 12
        row = i % 12
        x = bx + col * 245
        y = my + 16 + row * 16
        c.para(x, y, 1, b, INK, 240, leading=10)
    # date check
    dy = 958
    c.frame(24, dy, 976, 44, RED, 2)
    c.para(34, dy + 7, 1, DATECHECK, RED, 956, leading=11)
    # footer
    c.text(24, 1008, 1, FOOTER, GREY)
    return c


def main():
    os.makedirs("/output", exist_ok=True)
    dst = "/output/entry.png"
    n = build().png(dst)
    print("Wrote %s (%d bytes)" % (dst, n))


if __name__ == "__main__":
    main()
