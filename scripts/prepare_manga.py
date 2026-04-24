from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "manga_config.json"


@dataclass(frozen=True)
class Page:
    number: int
    title: str
    body: str


@dataclass(frozen=True)
class Panel:
    number: int
    heading: str
    body: str


STYLE_BIBLE = """\
# 作画共通仕様

- 形式: Japanese black-and-white manga page, right-to-left reading flow, clean ink line art, cinematic paneling.
- 画面: 縦長ページ、完成原稿向け。セリフは吹き出し内にだけ画像として直接描き込む。
- 線: 少年漫画寄りの読みやすい線、人物の表情を明確に、背景は必要箇所だけ密度を上げる。
- トーン: 序盤は軽いコメディ、中盤は静かな会話劇、後半は緊張、ラストは余韻。
- 近未来感: 現代の住宅、学校、病院に控えめなSFデバイスが混ざる程度。過度に宇宙的・サイバーパンクにしない。
- 重要演出: 爆発よりも、マアイの微細な表情変化を優先する。
- コマ割り: 均等グリッド禁止。大ゴマ、斜め割り、縦長コマ、細い間のコマ、白い余韻、破断コマ、速度線、黒ベタをページごとに大胆に使い分ける。
- 参照画像: `images/reference`の設定資料画像集をキャラクターの唯一の正解として扱う。髪型、顔、瞳、服、体格、装甲シルエットを変えない。
- 文字: 吹き出しには「」の中の本文だけを読みやすく入れる。話者名、ラベル、余計な文字、意味不明な文字、ローマ字化、誤字を入れない。
- 禁止: photorealistic, 3D render, western superhero style, excessive gore, messy unreadable panels, random unrelated text, watermark, signature.
"""

LOCATION_BIBLE = """\
# 背景・ロケーション設計

## P02-P05: 透也の部屋

舞台は朝倉家の2階にある透也の個室。狭い高校生男子の部屋。床に工具、スマホ、脱ぎっぱなしの服、勉強机、ベッド、本棚、充電ケーブル、古いゲーム機などがある。窓の外は夜。マアイはこの部屋に匿われている。P02、P03、P04、P05は基本的に同じ部屋の中で進行する。P04では部屋のドアと廊下側を使うが、背景は透也の部屋から連続している。P05のチャイム時も、まだ透也の部屋の中で灯里とマアイが小声で会話している。

## P06: 朝倉家の玄関破壊

同じ家の玄関側でGRAVEが侵入する。爆発は玄関ドアと廊下を吹き飛ばし、透也の部屋や階段側にも煙と破片が流れ込む。背景は急に屋外や廃墟にならない。住宅の玄関、廊下、階段、破壊されたドア、割れた壁、舞い込む煙で見せる。

## P07: 家の中から外へ逃げる動線

P07は朝倉家の室内アクション。透也が部屋または廊下で灯里の前に出て、灯里がマアイの手を取り、透也は玄関・廊下側へGRAVEを引きつける。背景は透也の部屋、廊下、階段、破壊された玄関が連続して見える。まだ夜道や廃墟には行かない。

## P08: 夜道から廃墟へ

P08で初めて家の外へ出る。夜の住宅街、遠くの爆発光、小型ドローンの赤いライト、逃走する灯里とマアイ。最後に廃墟の入口へ入る。

## P09-P16: 廃墟内部

古い廃ビルまたは廃校の内部。壊れた窓、月明かり、瓦礫、柱、割れた床、埃。静かな会話劇の舞台。P09-P16は同じ廃墟内で、場所を少し移動しても背景トーンは統一する。

## P17-P22: 崩壊する廃墟

GRAVE再襲撃後の同じ廃墟。壁が吹き飛び、煙、瓦礫、炎、壊れた鉄骨、崩れた床が増える。P18-P22は同じ崩壊現場の連続。P19だけ明るい公園や街路樹にしてはいけない。

## P23: 病院

事件後の病院廊下。白い壁、長椅子、夜明けまたは曇った外光。静かな余韻。透也は包帯姿。

## P24: 学校

時間経過後の学校。教室、大型モニター、廊下、机の上の金属片。清潔で日常に戻った空気。ただしマアイの不在の余韻を残す。
"""


CHARACTER_BIBLE = """\
# キャラクター固定設定

## 朝倉 灯里

中学生の少女。肩くらい、または少し短めの自然な髪。表情豊かで目は大きめ。部屋着または私服、パーカーやカーディガン。読者の感情を受け持つため、驚き、怒り、笑い、涙、寂しさをはっきり出す。

## 朝倉 透也

高校生の兄。少し寝ぐせのある髪、ラフな学生服または部屋着、眠そうな目つき。普段は軽く頼りないが、妹を守る場面では顔つきが変わる。

## MAI / マアイ

正式型番 EDU-430C。旧型教育用アンドロイドの少女型。人間に近いが完全には人間に見えない。リング状に淡く発光する瞳、首元や手首の細い機械ライン、制服風の教育用ジャケット、整いすぎたストレートボブ。基本は無表情。表情変化は目元だけに限定する。

## GRAVE / グレイヴ

正式型番 SEC-860G。黒い大型装甲の攻撃型アンドロイド。赤い単眼または細い赤い発光ライン。顔は人間的にしない。重機のような太い手足と内蔵式武装。右前腕は設定資料通りの内蔵式多銃身砲、左腕は重装甲のマニピュレーター。悪意ではなく命令だけで動く怖さを出す。

## ECHO / エコー

正式型番 EDU-860G。新型教育用アンドロイド。人間にかなり近く、自然な笑顔を持つ。ラストでは明るく爽やかに見えるが、マアイより尊い存在として描かない。
"""


CHARACTER_SHEET_PROMPTS = {
    "mai": (
        "MAI / マアイ",
        "Japanese all-ages manga character design sheet, front view, side view, back view, full body, same character consistency. "
        "A humanoid old educational android, model EDU-430C, called MAI. She looks close to human but not fully human. "
        "Straight bob hair arranged too perfectly, ring-shaped softly glowing eyes, thin mechanical seams on neck and wrists, "
        "fully clothed school-uniform-like educational jacket, calm expressionless face. Black-and-white manga line art with light screentone. "
        "No speech bubbles, no text, no logo, no watermark.",
    ),
    "akari": (
        "朝倉 灯里",
        "Japanese all-ages manga character design sheet, front view, side view, back view, full body, same character consistency. "
        "Expressive school-age heroine, shoulder-length natural hair, large emotional eyes, fully clothed casual hoodie or cardigan, "
        "skirt or shorts, energetic but kind. Black-and-white manga line art with light screentone. "
        "No speech bubbles, no text, no logo, no watermark.",
    ),
    "toya": (
        "朝倉 透也",
        "Japanese all-ages manga character design sheet, front view, side view, back view, full body, same character consistency. "
        "High school older brother, slightly messy bed hair, sleepy eyes, fully clothed casual student clothes, "
        "looks a little unreliable but fundamentally kind. Black-and-white manga line art with light screentone. "
        "No speech bubbles, no text, no logo, no watermark.",
    ),
    "grave": (
        "GRAVE / グレイヴ",
        "Japanese manga mecha character design sheet, front view, side view, back view, full body, same character consistency. "
        "Large black armored anti-android suppression unit, model SEC-860G, called GRAVE. Heavy industrial limbs, "
        "inhuman face, red mono-eye or thin red visor, right forearm is an integrated multi-barrel cannon exactly like the reference sheet, "
        "left arm is a heavy armored manipulator hand, intimidating silhouette, no malice, only command-driven. "
        "Black-and-white manga line art with sharp shadows and mechanical detail. No speech bubbles, no text, no logo, no watermark.",
    ),
    "echo": (
        "ECHO / エコー",
        "Japanese all-ages manga character design sheet, front view, side view, back view, full body, same character consistency. "
        "New educational android model EDU-860G, called ECHO, very close to human, natural smile, modern school assistant outfit, "
        "clean future-friendly design. It must feel pleasant but slightly ambiguous. Black-and-white manga line art with light screentone. "
        "No speech bubbles, no text, no logo, no watermark.",
    ),
}


COVER_PROMPT = """\
Japanese black-and-white all-ages theatrical manga cover illustration for "Last Lie: MAI", using the attached character reference images as strict visual canon.

Match the reference images exactly: MAI's face, bob hair, ring eyes, android seams and outfit; Akari's face, hair and casual outfit; Toya if included; GRAVE's black armored silhouette and red mono-eye. Do not redesign any character.

Central composition: MAI stands calmly with a cracked metal security tag in one hand. Her ring-shaped eyes are soft but almost expressionless. In the foreground, Akari gently reaches toward MAI as a sign of trust. Behind them, the huge black armored GRAVE appears as a threatening shadow with a red mono-eye. Near-future school science fiction drama atmosphere, emotional not action-focused. Clean manga ink, dramatic screentone, strong silhouette.

Cover layout: bold Japanese manga cover composition, not a flat character lineup. Use a huge dark GRAVE silhouette as the background mass, MAI as the calm vertical center line, Akari as the emotional foreground diagonal, strong black-and-white contrast, dramatic rim light, storm-like screentone texture, and clear depth. Keep all three characters visually distinct and exactly matched to their own reference sheets.

Render the following cover text clearly in Japanese:
Title: ラスト・ライ
Subtitle: MAI
Tagline: その嘘は、世界でいちばん優しかった。

Do not add any other text, logo, watermark, or signature.
"""


CHECKLIST = """\
# 漫画制作チェックリスト

- `images/reference`のキャラクター設定資料画像集を毎回参照画像としてAPIに渡す。
- 生成画像には吹き出し内のセリフ本文だけを直接入れる。
- セリフは話者名なしで、「」の中身だけを吹き出しに入れる。
- コマ割りは均等グリッド禁止。日本の漫画のように、視線誘導と大ゴマを使う。
- P20最終コマのマアイは、大きな笑顔にしない。微笑未満、瞳だけ柔らかい表情にする。
- P15、P16、P20、P22、P24は品質確認を厳しくする。
- 同じページを作り直す場合は、構図指示を変えすぎず、表情・密度・視線だけを調整する。
- API生成時はまず表紙またはP1だけで参照画像の効き方を確認する。
- P02-P07は透也の部屋と朝倉家の玄関・廊下の連続空間として描く。途中で屋外、公園、廃墟、学校にしない。
"""


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing config: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def parse_pages(story_text: str) -> list[Page]:
    pattern = re.compile(r"^# P(\d+)\s+(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(story_text))
    pages: list[Page] = []

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(story_text)
        number = int(match.group(1))
        title = match.group(2).strip()
        body = story_text[start:end].strip()
        pages.append(Page(number=number, title=title, body=body))

    if len(pages) != 24:
        raise ValueError(f"Expected 24 pages, found {len(pages)}")
    return pages


def parse_panels(page: Page) -> list[Panel]:
    pattern = re.compile(r"^##\s+(\d+)コマ目(?::|：)?\s*(.*?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(page.body))
    panels: list[Panel] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(page.body)
        panels.append(Panel(int(match.group(1)), match.group(2).strip(), page.body[start:end].strip()))
    return panels


def extract_panel_dialogue(panel: Panel) -> list[dict]:
    lines: list[dict] = []
    current_speaker = None
    for raw_line in panel.body.splitlines():
        line = raw_line.strip()
        speaker_match = re.fullmatch(r"\*\*(.+?)\*\*", line)
        if speaker_match:
            current_speaker = speaker_match.group(1)
            continue
        if current_speaker and line and not line.startswith("#") and not line.startswith("---") and not line.startswith(">"):
            quote_match = re.fullmatch(r"[「“](.+?)[」”]", line)
            if quote_match:
                lines.append(
                    {
                        "text": quote_match.group(1),
                        "panel": panel.number,
                    }
                )
                current_speaker = None
    return lines


def extract_dialogue_items(page: Page) -> list[dict]:
    items: list[dict] = []
    for panel in parse_panels(page):
        items.extend(extract_panel_dialogue(panel))
    return items


def format_dialogue(page: Page) -> str:
    items = extract_dialogue_items(page)
    if not items:
        return "吹き出しセリフなし"
    lines = [
        "Placement notes are not drawable text. Render only the Japanese dialogue strings below.",
    ]
    for item in items:
        lines.append(f"- place in panel {item['panel']}: {item['text']}")
    return "\n".join(lines)


def page_layout_instruction(page: Page, panel_count: int) -> str:
    special = {
        1: "3 panels with cinematic asymmetry: a huge tilted TV-news panel taking the upper half, a thin surveillance-camera strip cutting diagonally across the page, and a black title-card panel at the bottom. Strong right-to-left eye flow and no equal rectangles.",
        2: "5 panels: intimate room scene with a large low-angle panel of MAI on the floor, small insert of smartphone search, close-up of MAI's ring eyes, and angled hand/tool detail. Use cramped room perspective.",
        3: "8 panels: quick back-and-forth comedy rhythm using narrow reaction panels, then a larger close-up for Toya's '目を見たから'. Make the eye close-up a visual anchor.",
        4: "7 panels: door-comedy timing. Use vertical door-slit panels, sudden reveal panel, and exaggerated reaction panel. Avoid a simple row layout.",
        5: "8 panels: suspense from repeated doorbell. Use thin sound-beat panels, tight faces, and a small warm panel when Akari names MAI.",
        6: "5 panels: page starts with a huge explosive entrance splash panel breaking the panel border, then tight mechanical close-ups and weapon deployment panels. Use diagonal debris, speed lines, and heavy blacks.",
        7: "6 panels: action diversion. Use a large diagonal split between Toya drawing GRAVE away and Akari pulling MAI. Make GRAVE's red eye a sharp tracking insert.",
        8: "6 panels: night escape. Use a long horizontal running panel, a vertical drone-searchlight panel, and an irregular ruin-entry panel with motion blur.",
        9: "6 panels: quiet ruin page. One large moonlit establishing panel, then smaller breathing/reaction panels. Use broken window shapes as panel echoes.",
        10: "7 panels: philosophical conversation. Use a calm large two-shot, small close-ups, and white space to slow the reading rhythm.",
        11: "9 panels: tension explanation. Use red-light sightline inserts, GRAVE image cut-in, and small deadpan comedy panels for the 3.7 percent exchange.",
        12: "9 panels: truth reveal with present and flashback intercut. Use jagged flashback panels, warning-screen inserts, and darker borders for memory.",
        13: "9 panels: emotional debate. Use tight face close-ups, a large Akari panel for '人を助けたなら', and a small lonely final panel.",
        14: "10 panels: comedy lesson. Use fast small reaction panels, a large interruption panel, and clean balloon placement for timing.",
        15: "8 panels: conversation page with one large emotional central panel for Akari's key line. Surround it with smaller reaction panels. Use white negative space and an open background.",
        16: "12 panels: delicate conversation rhythm. Use many small quiet reaction panels, a silent beat, and a close-up of MAI's eyes for the unclassified reaction. Let the page breathe despite many panels.",
        17: "6 panels: drone detection tension, then a huge wall-destruction impact panel that breaks panel borders. Use debris, black speed lines, and tilted frames.",
        18: "8 panels: collapsing ruin action. Use diagonal falling rubble panels, smoke-obscured close-ups, and a tall panel of MAI supporting Akari.",
        19: "12 panels: immediate attack and rescue sequence inside the same collapsed ruin as pages 18 and 20. Use a clear visual chain: Akari trapped, GRAVE targeting her with the right forearm cannon, MAI lunging in, MAI grabbing the cannon armor, muzzle forced aside, shot missing Akari, impact destroying MAI's left arm, then quiet emotional close-ups. Avoid confusing silhouettes and avoid any flashback-like memory panel.",
        20: "9 panels: emotional climax. Build from small close-up panels to a large final panel of MAI making a micro-expression. Do not make MAI smile broadly. Final panel should dominate the bottom third.",
        21: "8 panels: duel setup. Use Akari fleeing in a narrow foreground strip, then a massive confrontation panel with MAI small against GRAVE. Strong scale contrast.",
        22: "9 panels: sacrifice sequence. Tight core close-ups, calm face close-up, then a large white flash panel. The final flash should dominate the page and swallow panel borders.",
        23: "13 panels: hospital emotional aftermath. Use quiet small panels, hand/metal-fragment close-up, and one large tearful-smile panel near the end.",
        24: "7 panels: quiet epilogue. Use airy school panels, object close-up of metal fragment, ghostlike MAI silhouette, and a final large quiet profile panel with strong empty space.",
    }
    if page.number in special:
        return special[page.number]
    if panel_count <= 4:
        return f"{panel_count} panels with one strong large panel, at least one narrow timing panel, and a clear diagonal eye path. Avoid equal rectangles."
    if panel_count <= 7:
        return f"{panel_count} panels in a varied Japanese manga layout: one large anchor panel, two medium panels, several narrow timing panels, and dynamic asymmetry. Avoid equal grid."
    return f"{panel_count} panels in a dense but readable Japanese manga layout: combine vertical narrow panels, close-ups, border-breaking action or emotion, and one larger emotional beat. Avoid equal grid."


def grave_design_instruction_for_page(page: Page) -> str:
    if page.number == 19:
        return (
            "GRAVE design lock for P19: Use `production/character_sheets/grave.md` and `images/reference/grave.png` exactly. "
            "GRAVE is a huge black armored SEC-860G with a red mono-eye visor, broad angular shoulder armor, heavy industrial legs, "
            "and a right forearm integrated cannon. The weapon must be part of the right forearm armor, not held in a hand. "
            "It has four slim parallel barrels at the wrist end, like the reference sheet's forearm cannon. "
            "Do not draw a separate gun, do not draw a round rotary minigun, do not draw a huge handheld gatling, do not add a sword, "
            "and do not replace the cannon with a normal hand. In the rescue panel, MAI grips the armored right forearm/cannon housing, "
            "forcing the four-barrel muzzle away from Akari."
        )
    if page.number == 21:
        return (
            "GRAVE design lock: Use `production/character_sheets/grave.md` and `images/reference/grave.png` exactly. "
            "GRAVE is a huge black armored SEC-860G with a red mono-eye visor, broad angular shoulder armor, heavy industrial legs, "
            "and a right forearm integrated multi-barrel cannon/gun. The final action panel must clearly show the right forearm as a gun, "
            "not a normal hand, not a sword, not an empty arm, not a human-like arm. Keep the left arm as a heavy manipulator hand."
        )
    return "GRAVE design lock: if GRAVE appears, follow `production/character_sheets/grave.md` and `images/reference/grave.png` exactly."


def mai_damage_instruction_for_page(page: Page) -> str:
    if page.number == 19:
        return (
            "MAI damage continuity: In this page MAI returns and grabs GRAVE's right forearm cannon, forcing the shot away from Akari. "
            "The bullet hits MAI and destroys/blows off MAI's left arm. From the impact panel onward, MAI must be visibly battered, "
            "missing her anatomical left arm from the shoulder or upper arm, with sparks and broken mechanical parts. "
            "Left/right are from MAI's own body, not from the viewer's perspective. Do not remove her right arm. "
            "Akari is not an android and has not lost any arm: keep both of Akari's arms intact; only Akari's leg/foot is injured."
        )
    if page.number in {20, 21, 22}:
        base = (
            "MAI damage continuity: MAI has already lost her anatomical left arm in P19. Throughout this page, draw MAI battered and missing her left arm, "
            "with a broken left shoulder/upper-arm stump, exposed mechanical parts, and sparks. Keep MAI's right arm intact and usable. "
            "Do not restore the missing left arm and do not swap the damaged side. Left/right are from MAI's own body: if MAI faces the reader, "
            "the missing left arm appears on the reader's right; if MAI is seen from behind, the missing left arm appears on the reader's left. "
            "Akari, if present, has both arms intact; do not amputate or damage Akari's arms."
        )
        if page.number == 21:
            return (
                base
                + " P21 panel 2 specific lock: MAI is standing before GRAVE and is often seen from behind; in that back-view composition, "
                "the missing arm must appear on the image/viewer's left side, while MAI's intact right arm appears on the image/viewer's right side. "
                "Do not put the broken shoulder on the image/viewer's right in panel 2."
            )
        if page.number == 22:
            return (
                base
                + " P22 panel 1 specific lock: MAI uses only her intact right arm to open/remove her jacket and expose the chest control core; "
                "the left shoulder remains a broken stump with no left forearm or left hand."
            )
        return base
    return "MAI damage continuity: follow the page script."


def akari_injury_instruction_for_page(page: Page) -> str:
    if page.number == 18:
        return (
            "Akari injury continuity: Akari's injured foot/leg is trapped by rubble, but she is wearing white or light-colored socks. "
            "Do not draw the injured foot as bare skin, a black sock, black boot, black prosthetic, or mechanical leg. "
            "Akari's arms are intact. MAI still has both arms on P18; MAI's left arm is not lost until P19."
        )
    if page.number in {19, 20, 21}:
        return (
            "Akari injury continuity: Akari has both arms intact throughout this page. Her injury is only her leg/foot, "
            "so show limping, crawling, or being unable to stand, but never remove, blacken, or mechanize either of Akari's arms."
        )
    return "Akari injury continuity: follow the page script."


def location_instruction_for_page(page: Page) -> str:
    if 2 <= page.number <= 5:
        return (
            "Location lock: Toya's small second-floor bedroom at night. Keep the same bedroom continuity across P02-P05: "
            "desk, bed, bookshelf, smartphone, tools on the floor, door to hallway, cramped teenage room. "
            "Do not show outdoor streets, ruins, school corridors, hospital, or parks."
        )
    if page.number == 6:
        return (
            "Location lock: Asakura house entrance and hallway being destroyed by GRAVE. This is the same house as P02-P05, "
            "not a battlefield or ruined city. Show broken front door, hallway, stairs, smoke entering the home, splintered walls, "
            "and debris from the entrance explosion."
        )
    if page.number == 7:
        return (
            "Location lock: inside Asakura house, moving from Toya's bedroom to hallway and broken entrance. "
            "Toya diverts GRAVE inside the house while Akari takes MAI away. Do not show night road or ruins yet."
        )
    if page.number == 8:
        return "Location lock: outside at night, residential street escape, then entrance to an abandoned building at the end."
    if 9 <= page.number <= 16:
        return "Location lock: inside the same quiet abandoned building. Broken windows, moonlight, dust, pillars, rubble, cracked floor."
    if 17 <= page.number <= 22:
        return "Location lock: same abandoned building after GRAVE attack. Collapsing walls, smoke, rubble, firelight, torn rebar, ruined concrete."
    if page.number == 23:
        return "Location lock: hospital corridor after the incident. White walls, bench, quiet recovery atmosphere."
    if page.number == 24:
        return "Location lock: school after time has passed. Classroom, hallway, large monitor, desk, ordinary daylight with lingering sadness."
    return "Location lock: follow the page script and keep continuity with adjacent pages."


def reference_keys_for_page(page: Page) -> list[str]:
    mapping = {
        1: ["mai"],
        2: ["mai", "toya"],
        3: ["mai", "toya"],
        4: ["mai", "toya", "akari"],
        5: ["mai", "toya", "akari"],
        6: ["mai", "toya", "akari", "grave"],
        7: ["mai", "toya", "akari", "grave"],
        8: ["mai", "akari"],
        9: ["mai", "akari"],
        10: ["mai", "akari"],
        11: ["mai", "akari", "grave"],
        12: ["mai", "akari"],
        13: ["mai", "akari"],
        14: ["mai", "akari", "toya"],
        15: ["mai", "akari"],
        16: ["mai", "akari"],
        17: ["mai", "akari", "grave"],
        18: ["mai", "akari", "grave"],
        19: ["mai", "akari", "grave"],
        20: ["mai", "akari"],
        21: ["mai", "akari", "grave"],
        22: ["mai", "grave"],
        23: ["akari", "toya", "mai"],
        24: ["akari", "mai", "echo"],
    }
    return mapping.get(page.number, ["mai", "akari", "toya", "grave", "echo"])


def context_images_for_page(page: Page, output_format: str) -> list[str]:
    if page.number < 1 or page.number > 24:
        return []

    context = []
    if page.number > 1:
        context.append(f"images/pages/page_{page.number - 1:02d}.{output_format}")
    if page.number < 24:
        context.append(f"images/pages/page_{page.number + 1:02d}.{output_format}")
    return context


def character_names_for_keys(keys: list[str]) -> str:
    names = {
        "mai": "MAI / マアイ",
        "akari": "朝倉 灯里",
        "toya": "朝倉 透也",
        "grave": "GRAVE / グレイヴ",
        "echo": "ECHO / エコー",
    }
    return ", ".join(names[key] for key in keys)


def build_page_prompt(page: Page) -> str:
    panel_script = sanitize_panel_script(page.body)
    panels = parse_panels(page)
    dialogue = format_dialogue(page)
    reference_keys = reference_keys_for_page(page)
    context_images = context_images_for_page(page, "png")
    return f"""\
# P{page.number:02d} {page.title}

## Image Prompt

Create one complete vertical Japanese black-and-white manga page, using the attached character reference images as strict visual canon.

Use the shared style and character settings from `production/style_bible.md` and `production/character_prompts.md`.
Use the location continuity bible from `production/location_bible.md`.

Page goal: {page.title}

Character reference requirements:
- The attached reference images are the canonical character design sheets.
- This page uses only these character references: {character_names_for_keys(reference_keys)}.
- Match each named character to their own attached reference image exactly.
- Never swap character identities. Do not give Akari's face or clothes to MAI, do not give MAI's android seams to Akari, and do not mix GRAVE armor with any human character.
- Do not redesign faces, hairstyles, outfits, body proportions, or GRAVE's armor silhouette.

Continuity requirements:
- If adjacent page images are attached, use them only as continuity references for background atmosphere, lighting, debris, smoke, and location.
- Do not copy the adjacent page panel layout. Do not introduce characters that are not in this page.
- For P19 specifically, the whole scene remains inside the collapsed ruined building area from P18 and P20. It must not look like a park, tree-lined street, schoolyard, clean sidewalk, or peaceful outdoor path.

Page location requirement:
{location_instruction_for_page(page)}

GRAVE weapon and silhouette requirement:
{grave_design_instruction_for_page(page)}

MAI damage requirement:
{mai_damage_instruction_for_page(page)}

Akari injury requirement:
{akari_injury_instruction_for_page(page)}

Manga panel layout requirement:
{page_layout_instruction(page, len(panels))}

Panel script:
{panel_script}

Speech balloon text to render exactly:
{dialogue}

Composition requirements:
- Treat the panel script as the exact page beat structure.
- Draw bold expressive Japanese manga panel borders and visual storytelling, not a simple storyboard grid.
- Use cinematic scale shifts, low angles, close-up inserts, diagonal panel cuts, black speed lines, border breaks, and purposeful white space where appropriate.
- Render only the Japanese dialogue strings after each colon in the speech list above, inside speech balloons in the correct panels.
- Do not render speaker names, character names, "panel", "place in", page labels, captions, metadata, or any labels for who is speaking.
- Use Japanese manga lettering: vertical text inside speech balloons where natural.
- Do not invent any extra text. Do not omit speech balloon dialogue. Do not replace Japanese with gibberish or pseudo-text.
- Preserve character consistency for Akari, Toya, MAI, GRAVE, and ECHO.
- Prioritize emotional clarity over background detail.

Safety and negative prompt:
all-ages adventure drama, fully clothed characters, non-suggestive camera framing, photorealistic, 3D render, color comic, speaker names in balloons, character name labels, unreadable unrelated text, watermark, signature, extra characters, wrong character ages, exaggerated smile on MAI, excessive gore.
"""


def sanitize_panel_script(text: str) -> str:
    replacements = {
        "少女型アンドロイド": "人型教育用アンドロイド",
        "少女型": "人型",
        "手錠": "破損した金属セキュリティリング",
        "壊れた手錠": "壊れた金属セキュリティリング",
        "腕には破損した金属セキュリティリング": "腕元に破損した金属セキュリティリング",
    }
    sanitized = text
    for old, new in replacements.items():
        sanitized = sanitized.replace(old, new)
    return sanitized


def build_character_sheet_prompt(title: str, prompt: str, reference_image_path: str) -> str:
    return f"""\
# {title} 三面図プロンプト

## 参照画像

![{title} reference](../../{reference_image_path})

画像ファイル: `../../{reference_image_path}`

## Image Prompt

{prompt}

Shared style:
{STYLE_BIBLE}
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    config = load_config()
    story_path = ROOT / config["story_file"]
    spec_path = ROOT / config["spec_file"]
    production_dir = ROOT / config["production_dir"]
    page_prompt_dir = production_dir / "page_prompts"

    story_text = read_text(story_path)
    spec_text = read_text(spec_path)
    pages = parse_pages(story_text)

    write_file(production_dir / "style_bible.md", STYLE_BIBLE)
    write_file(production_dir / "location_bible.md", LOCATION_BIBLE)
    character_sheet_dir = production_dir / "character_sheets"
    character_sheet_index = ["# キャラクター三面図・固定用プロンプト"]
    character_jobs = []
    for slug, (title, prompt) in CHARACTER_SHEET_PROMPTS.items():
        prompt_path = character_sheet_dir / f"{slug}.md"
        reference_path = f"{config['images_dir']}/reference/{slug}.{config['output_format']}"
        write_file(prompt_path, build_character_sheet_prompt(title, prompt, reference_path))
        character_sheet_index.append(f"- [{title}](character_sheets/{slug}.md)")
        character_jobs.append(
            {
                "key": slug,
                "title": title,
                "prompt_file": str(prompt_path.relative_to(ROOT)).replace("\\", "/"),
                "output_file": f"{config['images_dir']}/reference/{slug}.{config['output_format']}",
            }
        )

    write_file(production_dir / "character_prompts.md", CHARACTER_BIBLE + "\n\n" + "\n".join(character_sheet_index))
    write_file(production_dir / "cover_prompt.md", "# 表紙プロンプト\n\n" + COVER_PROMPT)
    write_file(production_dir / "checklist.md", CHECKLIST)

    dialogue_sections = []
    lettering_pages = []
    manifest_pages = []
    for page in pages:
        prompt_path = page_prompt_dir / f"page_{page.number:02d}.md"
        write_file(prompt_path, build_page_prompt(page))
        dialogue_items = extract_dialogue_items(page)
        dialogue_sections.append(f"## P{page.number:02d} {page.title}\n\n{format_dialogue(page)}")
        lettering_pages.append(
            {
                "page": page.number,
                "title": page.title,
                "items": dialogue_items,
            }
        )
        manifest_pages.append(
            {
                "page": page.number,
                "title": page.title,
                "prompt_file": str(prompt_path.relative_to(ROOT)).replace("\\", "/"),
                "output_file": f"{config['images_dir']}/pages/page_{page.number:02d}.{config['output_format']}",
                "lettered_file": f"{config['images_dir']}/lettered/page_{page.number:02d}.{config['output_format']}",
                "reference_keys": reference_keys_for_page(page),
                "context_images": context_images_for_page(page, config["output_format"]),
            }
        )

    write_file(production_dir / "dialogue_script.md", "# 吹き出し用台詞台本\n\n" + "\n\n".join(dialogue_sections))
    write_file(production_dir / "lettering.json", json.dumps({"pages": lettering_pages}, ensure_ascii=False, indent=2))

    manifest = {
        "model": config["model"],
        "quality": config["quality"],
        "size": config["size"],
        "output_format": config["output_format"],
        "story_file": config["story_file"],
        "spec_file": config["spec_file"],
        "source_lengths": {
            "story_chars": len(story_text),
            "spec_chars": len(spec_text),
        },
        "assets": {
            "style_bible": "production/style_bible.md",
            "location_bible": "production/location_bible.md",
            "character_prompts": "production/character_prompts.md",
            "cover_prompt": "production/cover_prompt.md",
            "cover_reference_keys": ["mai", "akari", "grave"],
            "dialogue_script": "production/dialogue_script.md",
            "lettering": "production/lettering.json",
            "checklist": "production/checklist.md",
        },
        "characters": character_jobs,
        "pages": manifest_pages,
    }
    write_file(production_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    print(f"Prepared {len(pages)} page prompts in {page_prompt_dir.relative_to(ROOT)}")
    print(f"Manifest: {(production_dir / 'manifest.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
