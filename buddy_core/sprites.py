"""
Sprite Generator & Manager for Desktop Buddy Bahubali ("Baahubali Edition").
Generates crisp, heroic, high-detail warrior sprites for all animation states:
- Majestic golden armor (Kavacham) with Mahishmati lion/sun crest
- Royal crimson dhoti with golden borders & kamarbandh
- Muscular warrior physique, bajuband (golden armbands), and wrist bracers
- Iconic Baahubali forehead tilak, flowing warrior locks & golden headband (Mukut)
- Legendary Mahishmati broadsword (raised triumphantly in celebrate!)
"""

import os
import math
from PIL import Image, ImageDraw

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Baahubali Color Palette
COLOR_OUTLINE = (28, 20, 15, 255)            # Deep dark outline
COLOR_SKIN = (212, 148, 102, 255)            # Warm sun-kissed Indian warrior skin
COLOR_SKIN_SHADOW = (176, 112, 70, 255)      # Muscle contours & shadow
COLOR_SKIN_HIGHLIGHT = (235, 178, 132, 255)  # Muscle highlight
COLOR_HAIR = (20, 16, 16, 255)               # Deep black hair
COLOR_HAIR_HIGHLIGHT = (48, 40, 40, 255)     # Hair sheen
COLOR_ARMOR_GOLD = (248, 196, 42, 255)       # Shining royal Mahishmati gold armor
COLOR_ARMOR_SHADOW = (184, 136, 22, 255)     # Chiseled armor shadow
COLOR_ARMOR_HIGHLIGHT = (255, 230, 120, 255) # Armor gleam
COLOR_DHOTI_RED = (168, 28, 38, 255)         # Royal crimson dhoti
COLOR_DHOTI_SHADOW = (116, 16, 24, 255)      # Dhoti fold shadow
COLOR_GOLD_TRIM = (252, 212, 64, 255)        # Dhoti golden border & kamarbandh
COLOR_TILAK_RED = (210, 24, 30, 255)         # Iconic Baahubali warrior Tilak
COLOR_TILAK_WHITE = (248, 242, 232, 255)     # Sandalwood base accent
COLOR_RUBY = (215, 20, 45, 255)              # Crown & armor ruby gem
COLOR_SWORD_STEEL = (228, 234, 244, 255)     # Steel broadsword blade
COLOR_SWORD_DARK = (150, 162, 178, 255)      # Blade fuller / edge shadow
COLOR_SWORD_HILT = (242, 192, 40, 255)       # Golden crossguard & pommel
COLOR_EYE_WHITE = (255, 255, 255, 255)
COLOR_EYE_PUPIL = (20, 15, 15, 255)
COLOR_SHADOW = (0, 0, 0, 55)                 # Floor shadow
COLOR_AURA_GOLD = (255, 215, 0, 220)         # Victory aura


def draw_bahubali(
    state="idle",
    frame=0,
    w=100,
    h=100,
    direction="right"
):
    """Draw a single frame of Bahubali."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    center_x = w // 2
    ground_y = 88

    # Dynamic animation variables
    bob_y = 0
    jump_y = 0
    shadow_scale = 1.0
    eye_state = "open"
    mouth_state = "neutral"
    arm_left_angle = 0
    arm_right_angle = 0
    leg_left_x = -9
    leg_right_x = 9
    leg_left_y = 0
    leg_right_y = 0
    sword_pose = "hip"  # "hip", "raised", "point", "meditate"
    sash_swing = 0

    if state == "idle":
        # Slow warrior breathing
        bob_y = int(math.sin(frame * (math.pi / 2)) * 1.8)
        sash_swing = int(math.sin(frame * (math.pi / 2)) * 2)
        eye_state = "blink" if frame == 2 else "open"
        sword_pose = "hip"

    elif state == "walk":
        # Heroic warrior stride
        phase = frame % 6
        bob_y = abs(int(math.sin(phase * math.pi / 3) * 3))
        stride = int(math.sin(phase * math.pi / 3) * 7)
        leg_left_x = -9 + stride
        leg_right_x = 9 - stride
        leg_left_y = -abs(int(math.cos(phase * math.pi / 3) * 3))
        leg_right_y = -abs(int(math.sin(phase * math.pi / 3) * 3))
        arm_left_angle = -stride * 3
        arm_right_angle = stride * 3
        sash_swing = stride * 2
        sword_pose = "hip"

    elif state == "think":
        # Strategic contemplation
        bob_y = 1
        eye_state = "think"
        arm_right_angle = 45  # Hand to chin
        sword_pose = "lean"

    elif state == "talk":
        # Commanding royal address
        bob_y = (frame % 2) * 2
        eye_state = "open"
        mouth_state = "talk"
        arm_right_angle = -25 + (frame % 3) * 10  # Royal gesture
        arm_left_angle = 10
        sword_pose = "hip"

    elif state == "celebrate":
        # Raising the legendary Mahishmati broadsword aloft!
        jump_y = -int(math.sin(frame * (math.pi / 5)) * 10)
        bob_y = jump_y
        shadow_scale = max(0.6, 1.0 + (jump_y / 25.0))
        eye_state = "heroic"
        mouth_state = "shout"
        arm_right_angle = -140  # Raising sword high to sky
        arm_left_angle = -45
        sword_pose = "raised"

    elif state == "sleep":
        # Peaceful warrior meditation (Padmasana)
        bob_y = 3
        eye_state = "closed"
        sword_pose = "meditate"

    y_off = bob_y

    # 1. Soft Floor Shadow
    shadow_w = int(22 * shadow_scale)
    shadow_h = int(6 * shadow_scale)
    d.ellipse(
        [center_x - shadow_w, ground_y - shadow_h, center_x + shadow_w, ground_y + shadow_h],
        fill=COLOR_SHADOW
    )

    # 2. Back Hair & Flowing Crimson Scarf (Behind Body)
    head_top = 18 + y_off
    # Back long warrior hair cascading past shoulders
    d.polygon([
        (center_x - 17, head_top + 10),
        (center_x - 22, head_top + 34),
        (center_x - 14, head_top + 40),
        (center_x - 10, head_top + 28)
    ], fill=COLOR_HAIR)
    d.polygon([
        (center_x + 17, head_top + 10),
        (center_x + 22, head_top + 34),
        (center_x + 14, head_top + 40),
        (center_x + 10, head_top + 28)
    ], fill=COLOR_HAIR)

    # Flowing royal crimson scarf/uttariyam fluttering in wind
    scarf_tip_x = center_x + 18 + sash_swing
    scarf_tip_y = head_top + 42 + y_off // 2
    d.polygon([
        (center_x + 12, head_top + 24),
        (scarf_tip_x + 8, scarf_tip_y),
        (scarf_tip_x, scarf_tip_y + 8),
        (center_x + 10, head_top + 32)
    ], fill=COLOR_DHOTI_RED, outline=COLOR_DHOTI_SHADOW)
    # Scarf golden border
    d.line([(scarf_tip_x + 8, scarf_tip_y), (scarf_tip_x, scarf_tip_y + 8)], fill=COLOR_GOLD_TRIM, width=2)

    # 3. Legs & Dhoti
    dhoti_top = 62 + y_off
    dhoti_bot = 78 + y_off

    if state == "sleep":
        # Crossed legs for meditation
        d.rounded_rectangle([center_x - 22, dhoti_top + 2, center_x + 22, ground_y - 2], radius=6, fill=COLOR_DHOTI_RED, outline=COLOR_OUTLINE, width=1)
        # Gold trims on folded dhoti
        d.line([center_x - 20, ground_y - 4, center_x + 20, ground_y - 4], fill=COLOR_GOLD_TRIM, width=2)
        d.line([center_x - 12, dhoti_top + 6, center_x + 12, dhoti_top + 6], fill=COLOR_GOLD_TRIM, width=1)
    else:
        # Left Leg & Foot
        fl_x = center_x + leg_left_x
        fl_y = ground_y - 9 + leg_left_y + y_off
        # Muscular calf
        d.rectangle([fl_x - 4, dhoti_bot - 2, fl_x + 3, fl_y], fill=COLOR_SKIN)
        # Golden warrior greave / ankle cuff
        d.rectangle([fl_x - 4, fl_y - 4, fl_x + 4, fl_y], fill=COLOR_ARMOR_GOLD, outline=COLOR_OUTLINE, width=1)
        # Warrior sandal foot
        d.rounded_rectangle([fl_x - 5, fl_y, fl_x + 4, fl_y + 6], radius=2, fill=COLOR_SKIN_SHADOW, outline=COLOR_OUTLINE, width=1)
        # Gold sandal strap
        d.line([fl_x - 4, fl_y + 2, fl_x + 3, fl_y + 2], fill=COLOR_GOLD_TRIM, width=1)

        # Right Leg & Foot
        fr_x = center_x + leg_right_x
        fr_y = ground_y - 9 + leg_right_y + y_off
        # Muscular calf
        d.rectangle([fr_x - 3, dhoti_bot - 2, fr_x + 4, fr_y], fill=COLOR_SKIN)
        # Golden warrior greave
        d.rectangle([fr_x - 4, fr_y - 4, fr_x + 4, fr_y], fill=COLOR_ARMOR_GOLD, outline=COLOR_OUTLINE, width=1)
        # Warrior sandal foot
        d.rounded_rectangle([fr_x - 4, fr_y, fr_x + 5, fr_y + 6], radius=2, fill=COLOR_SKIN_SHADOW, outline=COLOR_OUTLINE, width=1)
        # Gold sandal strap
        d.line([fr_x - 3, fr_y + 2, fr_x + 4, fr_y + 2], fill=COLOR_GOLD_TRIM, width=1)

        # Royal Dhoti Skirt & Folds
        d.polygon([
            (center_x - 17, dhoti_top),
            (center_x + 17, dhoti_top),
            (center_x + 16, dhoti_bot),
            (center_x - 16, dhoti_bot)
        ], fill=COLOR_DHOTI_RED, outline=COLOR_OUTLINE)

        # Dhoti Pleat Shadows
        d.line([center_x - 8, dhoti_top + 2, center_x - 10, dhoti_bot], fill=COLOR_DHOTI_SHADOW, width=1)
        d.line([center_x + 8, dhoti_top + 2, center_x + 10, dhoti_bot], fill=COLOR_DHOTI_SHADOW, width=1)

        # Dhoti Golden Bottom Hem
        d.line([center_x - 16, dhoti_bot - 1, center_x + 16, dhoti_bot - 1], fill=COLOR_GOLD_TRIM, width=2)

        # Central Hanging Golden Sash (Uttariyam Pleats)
        sash_hang = sash_swing // 2
        d.polygon([
            (center_x - 4, dhoti_top),
            (center_x + 4, dhoti_top),
            (center_x + 3 + sash_hang, dhoti_bot + 4),
            (center_x - 3 + sash_hang, dhoti_bot + 4)
        ], fill=COLOR_GOLD_TRIM, outline=COLOR_ARMOR_SHADOW)
        d.line([(center_x + sash_hang, dhoti_top), (center_x + sash_hang, dhoti_bot + 4)], fill=COLOR_DHOTI_RED, width=1)

    # 4. Golden Kamarbandh (Waistband & Royal Buckle)
    d.rounded_rectangle([center_x - 16, dhoti_top - 3, center_x + 16, dhoti_top + 3], radius=2, fill=COLOR_ARMOR_GOLD, outline=COLOR_OUTLINE, width=1)
    # Royal Center Buckle with Ruby
    d.ellipse([center_x - 4, dhoti_top - 4, center_x + 4, dhoti_top + 4], fill=COLOR_ARMOR_GOLD, outline=COLOR_ARMOR_SHADOW, width=1)
    d.ellipse([center_x - 2, dhoti_top - 2, center_x + 2, dhoti_top + 2], fill=COLOR_RUBY)

    # 5. Muscular Torso & Golden Mahishmati Kavacham (Chestplate)
    chest_top = 40 + y_off
    # Base Muscular Torso
    d.rounded_rectangle([center_x - 17, chest_top, center_x + 17, dhoti_top], radius=5, fill=COLOR_ARMOR_GOLD, outline=COLOR_OUTLINE, width=2)
    # Armor Highlights & Contour Details
    d.line([center_x - 15, chest_top + 2, center_x + 15, chest_top + 2], fill=COLOR_ARMOR_HIGHLIGHT, width=1)
    # Pectoral Plates
    d.arc([center_x - 14, chest_top + 4, center_x - 2, chest_top + 14], start=0, end=180, fill=COLOR_ARMOR_SHADOW, width=1)
    d.arc([center_x + 2, chest_top + 4, center_x + 14, chest_top + 14], start=0, end=180, fill=COLOR_ARMOR_SHADOW, width=1)
    # Abdominal Plates (Six-pack armor ribs)
    d.line([center_x, chest_top + 10, center_x, dhoti_top - 4], fill=COLOR_ARMOR_SHADOW, width=1)
    d.line([center_x - 10, chest_top + 15, center_x + 10, chest_top + 15], fill=COLOR_ARMOR_SHADOW, width=1)
    d.line([center_x - 8, chest_top + 19, center_x + 8, chest_top + 19], fill=COLOR_ARMOR_SHADOW, width=1)

    # Royal Mahishmati Lion/Sun Insignia in Center Chest
    insignia_y = chest_top + 9
    d.ellipse([center_x - 3, insignia_y - 3, center_x + 3, insignia_y + 3], fill=COLOR_RUBY, outline=COLOR_ARMOR_HIGHLIGHT, width=1)

    # Golden Royal Shoulder Pauldrons (Flared Shoulder Armor)
    d.polygon([(center_x - 17, chest_top + 1), (center_x - 24, chest_top + 5), (center_x - 18, chest_top + 12), (center_x - 15, chest_top + 8)], fill=COLOR_ARMOR_GOLD, outline=COLOR_OUTLINE)
    d.polygon([(center_x + 17, chest_top + 1), (center_x + 24, chest_top + 5), (center_x + 18, chest_top + 12), (center_x + 15, chest_top + 8)], fill=COLOR_ARMOR_GOLD, outline=COLOR_OUTLINE)

    # Diagonal Royal Crimson Uttariyam (Sash across chest)
    d.line([center_x - 16, chest_top + 2, center_x + 14, dhoti_top - 1], fill=COLOR_DHOTI_RED, width=3)
    d.line([center_x - 16, chest_top + 3, center_x + 14, dhoti_top], fill=COLOR_GOLD_TRIM, width=1)

    # 6. Arms & Hands
    # Left Arm
    la_x = center_x - 18
    la_y = chest_top + 6
    la_rad = math.radians(arm_left_angle)
    la_elbow_x = la_x - 6 - int(math.sin(la_rad) * 6)
    la_elbow_y = la_y + 8 + int(math.cos(la_rad) * 6)
    la_hand_x = la_elbow_x - int(math.sin(la_rad) * 6)
    la_hand_y = la_elbow_y + int(math.cos(la_rad) * 6)

    # Muscular Bicep
    d.line([la_x, la_y, la_elbow_x, la_elbow_y], fill=COLOR_SKIN, width=6)
    # Golden Bajuband (Armlet)
    d.line([la_x - 2, la_y + 3, la_elbow_x + 1, la_elbow_y - 2], fill=COLOR_ARMOR_GOLD, width=2)
    # Forearm & Golden Wrist Kada/Vambrace
    d.line([la_elbow_x, la_elbow_y, la_hand_x, la_hand_y], fill=COLOR_SKIN, width=5)
    d.line([la_hand_x - 1, la_hand_y - 2, la_hand_x + 1, la_hand_y + 2], fill=COLOR_ARMOR_GOLD, width=3)
    # Clenched Hand
    d.ellipse([la_hand_x - 3, la_hand_y - 3, la_hand_x + 3, la_hand_y + 3], fill=COLOR_SKIN_SHADOW, outline=COLOR_OUTLINE, width=1)

    # Right Arm
    ra_x = center_x + 18
    ra_y = chest_top + 6
    ra_rad = math.radians(arm_right_angle)
    ra_elbow_x = ra_x + 6 + int(math.sin(ra_rad) * 6)
    ra_elbow_y = ra_y + 8 + int(math.cos(ra_rad) * 6)
    ra_hand_x = ra_elbow_x + int(math.sin(ra_rad) * 6)
    ra_hand_y = ra_elbow_y + int(math.cos(ra_rad) * 6)

    if sword_pose == "raised":
        # Straight up raised arm
        ra_elbow_x = ra_x + 2
        ra_elbow_y = ra_y - 10
        ra_hand_x = ra_x + 3
        ra_hand_y = ra_y - 22

    elif sword_pose == "lean" or (state == "think"):
        # Hand to chin
        ra_elbow_x = ra_x + 8
        ra_elbow_y = ra_y + 10
        ra_hand_x = center_x + 4
        ra_hand_y = head_top + 24

    d.line([ra_x, ra_y, ra_elbow_x, ra_elbow_y], fill=COLOR_SKIN, width=6)
    # Golden Bajuband
    d.line([ra_x + 2, ra_y + 3, ra_elbow_x - 1, ra_elbow_y - 2], fill=COLOR_ARMOR_GOLD, width=2)
    # Forearm & Golden Wrist Kada
    d.line([ra_elbow_x, ra_elbow_y, ra_hand_x, ra_hand_y], fill=COLOR_SKIN, width=5)
    d.line([ra_hand_x - 1, ra_hand_y - 2, ra_hand_x + 1, ra_hand_y + 2], fill=COLOR_ARMOR_GOLD, width=3)
    # Clenched Hand
    d.ellipse([ra_hand_x - 3, ra_hand_y - 3, ra_hand_x + 3, ra_hand_y + 3], fill=COLOR_SKIN_SHADOW, outline=COLOR_OUTLINE, width=1)

    # 7. Mahishmati Royal Broadsword
    if sword_pose == "raised":
        # Held high aloft above head in right hand with golden glory sparkles!
        sw_base_x = ra_hand_x
        sw_base_y = ra_hand_y
        sw_tip_x = sw_base_x
        sw_tip_y = sw_base_y - 30

        # Golden Crossguard & Pommel
        d.line([sw_base_x - 7, sw_base_y, sw_base_x + 7, sw_base_y], fill=COLOR_SWORD_HILT, width=3)
        d.ellipse([sw_base_x - 2, sw_base_y + 3, sw_base_x + 2, sw_base_y + 7], fill=COLOR_RUBY)

        # Shining Steel Blade
        d.polygon([
            (sw_base_x - 3, sw_base_y),
            (sw_tip_x - 3, sw_tip_y + 5),
            (sw_tip_x, sw_tip_y),
            (sw_tip_x + 3, sw_tip_y + 5),
            (sw_base_x + 3, sw_base_y)
        ], fill=COLOR_SWORD_STEEL, outline=COLOR_OUTLINE, width=1)
        # Center fuller line
        d.line([(sw_base_x, sw_base_y), (sw_tip_x, sw_tip_y + 3)], fill=COLOR_SWORD_DARK, width=1)

        # Golden Victory Aura & Sparkles (Jai Mahishmati!)
        sparkle_phase = frame % 4
        d.line([sw_tip_x - 8, sw_tip_y, sw_tip_x + 8, sw_tip_y], fill=COLOR_AURA_GOLD, width=2)
        d.line([sw_tip_x, sw_tip_y - 8, sw_tip_x, sw_tip_y + 8], fill=COLOR_AURA_GOLD, width=2)
        d.ellipse([sw_tip_x - 3, sw_tip_y - 3, sw_tip_x + 3, sw_tip_y + 3], fill=(255, 255, 255, 240))
        # Extra sparks
        d.text((sw_tip_x + 6, sw_tip_y - 8), "*", fill=COLOR_AURA_GOLD)
        d.text((sw_tip_x - 12, sw_tip_y - 4), "*", fill=COLOR_AURA_GOLD)

    elif sword_pose == "meditate":
        # Sword resting flat horizontally in front of crossed legs
        msw_y = ground_y - 5
        d.line([center_x - 24, msw_y, center_x + 20, msw_y], fill=COLOR_SWORD_STEEL, width=3)
        d.line([center_x - 24, msw_y, center_x - 16, msw_y], fill=COLOR_SWORD_HILT, width=4)
        d.ellipse([center_x - 26, msw_y - 2, center_x - 23, msw_y + 2], fill=COLOR_RUBY)

    else:
        # Sword sheathed at left hip
        sw_hip_x = center_x - 14
        sw_hip_y = dhoti_top
        # Golden Crossguard & Pommel
        d.line([sw_hip_x - 4, sw_hip_y - 2, sw_hip_x + 4, sw_hip_y + 4], fill=COLOR_SWORD_HILT, width=3)
        d.ellipse([sw_hip_x + 2, sw_hip_y + 3, sw_hip_x + 6, sw_hip_y + 7], fill=COLOR_RUBY)
        # Sheath hanging down alongside dhoti
        d.line([sw_hip_x, sw_hip_y, sw_hip_x - 6, sw_hip_y + 22], fill=COLOR_ARMOR_SHADOW, width=3)
        d.line([sw_hip_x - 5, sw_hip_y + 18, sw_hip_x - 7, sw_hip_y + 22], fill=COLOR_ARMOR_GOLD, width=3)

    # 8. Head & Neck
    neck_top = chest_top - 6
    d.rectangle([center_x - 6, neck_top, center_x + 6, chest_top + 1], fill=COLOR_SKIN)
    # Royal Golden Necklace (Kanthamaala)
    d.arc([center_x - 8, neck_top + 2, center_x + 8, neck_top + 9], start=0, end=180, fill=COLOR_ARMOR_GOLD, width=2)

    # Face Shape (Square heroic jawline)
    face_left = center_x - 13
    face_right = center_x + 13
    face_top = head_top + 4
    face_bot = neck_top + 4
    d.rounded_rectangle([face_left, face_top, face_right, face_bot], radius=7, fill=COLOR_SKIN, outline=COLOR_OUTLINE, width=2)
    # Cheek shading
    d.line([face_left + 1, face_bot - 4, face_left + 5, face_bot - 1], fill=COLOR_SKIN_SHADOW, width=1)
    d.line([face_right - 1, face_bot - 4, face_right - 5, face_bot - 1], fill=COLOR_SKIN_SHADOW, width=1)

    # 9. Hair & Royal Topknot (Man-Bun) & Mukut (Headband)
    # Front Warrior Hair Curving around face
    d.polygon([(center_x - 14, head_top + 4), (center_x - 17, head_top + 18), (center_x - 12, head_top + 12)], fill=COLOR_HAIR)
    d.polygon([(center_x + 14, head_top + 4), (center_x + 17, head_top + 18), (center_x + 12, head_top + 12)], fill=COLOR_HAIR)

    # Top Hair Volume
    d.ellipse([center_x - 14, head_top - 2, center_x + 14, head_top + 10], fill=COLOR_HAIR)

    # Royal Warrior Topknot / Man-Bun
    bun_y = head_top - 7
    d.ellipse([center_x - 6, bun_y, center_x + 6, bun_y + 8], fill=COLOR_HAIR, outline=COLOR_OUTLINE, width=1)
    # Gold thread tying the topknot
    d.line([center_x - 5, bun_y + 4, center_x + 5, bun_y + 4], fill=COLOR_ARMOR_GOLD, width=2)

    # Golden Mukut / Warrior Headband
    mukut_y = head_top + 5
    d.line([face_left, mukut_y, face_right, mukut_y], fill=COLOR_ARMOR_GOLD, width=3)
    d.line([face_left + 2, mukut_y - 1, face_right - 2, mukut_y - 1], fill=COLOR_ARMOR_HIGHLIGHT, width=1)
    # Center Royal Ruby in Headband
    d.polygon([(center_x, mukut_y - 4), (center_x + 3, mukut_y), (center_x, mukut_y + 3), (center_x - 3, mukut_y)], fill=COLOR_RUBY, outline=COLOR_ARMOR_GOLD)

    # 10. Iconic Baahubali Warrior Tilak
    # Signature vertical red vermilion streak with sandalwood accent
    tilak_y = mukut_y + 3
    d.line([center_x, tilak_y, center_x, tilak_y + 6], fill=COLOR_TILAK_RED, width=2)
    # Sandalwood crescent base
    d.arc([center_x - 3, tilak_y + 4, center_x + 3, tilak_y + 7], start=0, end=180, fill=COLOR_TILAK_WHITE, width=1)

    # 11. Eyes & Warrior Eyebrows
    eye_y = head_top + 14
    eye_l_x = center_x - 6
    eye_r_x = center_x + 6

    # Bold Warrior Eyebrows (Angle determined)
    d.line([eye_l_x - 4, eye_y - 3, eye_l_x + 2, eye_y - 2], fill=COLOR_HAIR, width=2)
    d.line([eye_r_x - 2, eye_y - 2, eye_r_x + 4, eye_y - 3], fill=COLOR_HAIR, width=2)

    if eye_state == "open" or eye_state == "heroic":
        # Determined warrior eyes
        d.ellipse([eye_l_x - 3, eye_y - 1, eye_l_x + 2, eye_y + 3], fill=COLOR_EYE_WHITE)
        d.ellipse([eye_r_x - 2, eye_y - 1, eye_r_x + 3, eye_y + 3], fill=COLOR_EYE_WHITE)
        d.ellipse([eye_l_x - 1, eye_y, eye_l_x + 1, eye_y + 2], fill=COLOR_EYE_PUPIL)
        d.ellipse([eye_r_x - 1, eye_y, eye_r_x + 1, eye_y + 2], fill=COLOR_EYE_PUPIL)
    elif eye_state == "blink":
        d.line([eye_l_x - 3, eye_y + 1, eye_l_x + 2, eye_y + 1], fill=COLOR_HAIR, width=2)
        d.line([eye_r_x - 2, eye_y + 1, eye_r_x + 3, eye_y + 1], fill=COLOR_HAIR, width=2)
    elif eye_state == "think":
        # Gazing up thoughtfully
        d.ellipse([eye_l_x - 3, eye_y - 2, eye_l_x + 2, eye_y + 2], fill=COLOR_EYE_WHITE)
        d.ellipse([eye_r_x - 2, eye_y - 2, eye_r_x + 3, eye_y + 2], fill=COLOR_EYE_WHITE)
        d.ellipse([eye_l_x - 1, eye_y - 2, eye_l_x + 1, eye_y], fill=COLOR_EYE_PUPIL)
        d.ellipse([eye_r_x - 1, eye_y - 2, eye_r_x + 1, eye_y], fill=COLOR_EYE_PUPIL)
        # Strategic battle spark above head
        spark_y = head_top - 12 + (frame % 3) * 2
        d.text((center_x + 14, spark_y), "+", fill=COLOR_AURA_GOLD)
    elif eye_state == "closed":
        d.arc([eye_l_x - 3, eye_y, eye_l_x + 2, eye_y + 3], start=0, end=180, fill=COLOR_HAIR, width=2)
        d.arc([eye_r_x - 2, eye_y, eye_r_x + 3, eye_y + 3], start=0, end=180, fill=COLOR_HAIR, width=2)
        # Serene Om symbol / Z floating
        om_y = head_top - 6 - (frame * 3)
        d.text((center_x + 14, om_y), "Om", fill=COLOR_AURA_GOLD)

    # 12. Iconic Baahubali Warrior Mustache & Mouth
    mustache_y = eye_y + 5
    # The famous upward curved thick mustache!
    d.arc([center_x - 8, mustache_y - 2, center_x, mustache_y + 3], start=180, end=0, fill=COLOR_HAIR, width=2)
    d.arc([center_x, mustache_y - 2, center_x + 8, mustache_y + 3], start=180, end=0, fill=COLOR_HAIR, width=2)
    # Royal curved tips
    d.line([center_x - 8, mustache_y, center_x - 9, mustache_y - 2], fill=COLOR_HAIR, width=2)
    d.line([center_x + 8, mustache_y, center_x + 9, mustache_y - 2], fill=COLOR_HAIR, width=2)

    # Mouth expressions
    mouth_y = mustache_y + 3
    if mouth_state == "shout":
        # Roaring victory ("Jai Mahishmati!")
        d.ellipse([center_x - 3, mouth_y, center_x + 3, mouth_y + 4], fill=(130, 20, 20), outline=COLOR_OUTLINE)
    elif mouth_state == "talk":
        # Speaking royal orders
        mouth_w = 3 + (frame % 3) * 2
        d.rectangle([center_x - mouth_w // 2, mouth_y, center_x + mouth_w // 2, mouth_y + 2], fill=(140, 30, 30))
    else:
        # Stoic warrior smile
        d.line([center_x - 2, mouth_y, center_x + 2, mouth_y], fill=COLOR_OUTLINE, width=1)

    # Flip horizontally if moving left
    if direction == "left":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    return img


def generate_all_sprites():
    """Pre-generates all Baahubali animation states and caches them in ASSETS_DIR."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    animations = {
        "idle": 4,
        "walk_right": 6,
        "walk_left": 6,
        "think": 6,
        "talk": 6,
        "celebrate": 6,
        "sleep": 4
    }

    cached_frames = {}

    for state, num_frames in animations.items():
        cached_frames[state] = []
        direction = "left" if "left" in state else "right"
        base_state = "walk" if "walk" in state else state

        for f in range(num_frames):
            filename = f"{state}_{f}.png"
            filepath = os.path.join(ASSETS_DIR, filename)
            frame_img = draw_bahubali(state=base_state, frame=f, direction=direction)
            frame_img.save(filepath, "PNG")
            cached_frames[state].append(filepath)

    return cached_frames


class SpriteManager:
    """Manages sprite frame cycles and returns PIL Images for Tkinter."""
    def __init__(self):
        self.frames = generate_all_sprites()
        self.current_state = "idle"
        self.frame_index = 0

    def set_state(self, state):
        if state in self.frames and state != self.current_state:
            self.current_state = state
            self.frame_index = 0

    def get_current_frame_path(self):
        state_frames = self.frames.get(self.current_state, self.frames["idle"])
        return state_frames[self.frame_index % len(state_frames)]

    def advance_frame(self):
        state_frames = self.frames.get(self.current_state, self.frames["idle"])
        self.frame_index = (self.frame_index + 1) % len(state_frames)
        return state_frames[self.frame_index]


if __name__ == "__main__":
    print("Generating Bahubali sprite frames...")
    mgr = SpriteManager()
    print(f"Generated {sum(len(v) for v in mgr.frames.values())} frames successfully!")
