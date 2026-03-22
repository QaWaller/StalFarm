import random
import os
import time
import json
import threading
from datetime import datetime
from pathlib import Path

# ======================= ПУТЬ ДЛЯ СОХРАНЕНИЙ =======================
try:
    GAME_DIR = Path(__file__).parent if "__file__" in dir() else Path.cwd()
    SAVE_DIR = GAME_DIR / "saves"
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    # проверка на запись
    test_file = SAVE_DIR / "test.txt"
    test_file.write_text("test")
    test_file.unlink()
    SAVE_PATH = SAVE_DIR / "save.txt"
except:
    SAVE_DIR = Path.home() / "Documents" / "Stalkan"
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    SAVE_PATH = SAVE_DIR / "save.txt"

# ======================= ПРОФИЛИ =======================
BUILDS = {
    "stealth": {
        "name": "Стелс Сатурн",
        "weapon": "ВСС-М",
        "health": 90,
        "armor": 1.1,
        "heat_mod": 0.65,
        "dmg_mod": 0.85,
        "ammo_use": 2,
        "desc": "Быстрый, хрупкий, тихий, экономичный"
    },
    "heavy": {
        "name": "Антарес",
        "weapon": "ПКП Печенег",
        "health": 120,
        "armor": 0.85,
        "heat_mod": 1.25,
        "dmg_mod": 1.35,
        "ammo_use": 8,
        "desc": "Жирный, пулестойкий, шумный, прожорливый"
    }
}

# ======================= ЛУТ =======================
LOOT_DATA = {
    "Солевик": {"price_100g": 250, "weight": (150, 350), "emoji": "🥬"},
    "Мятноплод": {"price_100g": 450, "weight": (200, 450), "emoji": "🍃"},
    "Сластёна": {"price_100g": 1100, "weight": (300, 550), "emoji": "🍬"},
    "Кубоарбуз": {"price_100g": 2800, "weight": (450, 750), "emoji": "🍉"},
    "Лимонник": {"price_100g": 5200, "weight": (600, 950), "emoji": "🍋"}
}

# ======================= АРТЕФАКТЫ =======================
ARTIFACTS = {
    "Кровь камня": {"price": 8000, "weight": 100, "emoji": "🪨"},
    "Слеза зоны": {"price": 15000, "weight": 50, "emoji": "💧"},
    "Золотая сфера": {"price": 30000, "weight": 150, "emoji": "🔮"},
    "Мёртвая голова": {"price": 50000, "weight": 200, "emoji": "💀"}
}

# ======================= УЛУЧШЕНИЯ =======================
UPGRADES = {
    "silencer": {"name": "Глушитель", "effect": "heat_reduce", "value": 0.75, "cost": 40000},
    "compensator": {"name": "Компенсатор", "effect": "dmg_bonus", "value": 1.2, "cost": 50000}
}

# ======================= ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =======================
TOTAL_WALLET = 0
STASH_LVL = 1
MAX_STASH_HP = 100
MAX_STASH_WEIGHT = 3000
AMMO_STOCK = 100
MEDKITS_STOCK = 3
DETECTOR_LEVEL = 0
STASH_MASKED = False
MASKING_PROGRESS = 0
MASK_THREAD = None
STASH_CONTENT = {}
ACTIVE_UPGRADES = []
ACHIEVEMENTS = {}
LAST_PLAY_DATE = ""
DAILY_BONUS_CLAIMED = False

# ======================= ФУНКЦИИ =======================
def save_game():
    data = {
        "wallet": TOTAL_WALLET, "stash_lvl": STASH_LVL, "max_hp": MAX_STASH_HP,
        "max_weight": MAX_STASH_WEIGHT, "ammo": AMMO_STOCK, "med": MEDKITS_STOCK,
        "detector": DETECTOR_LEVEL, "stash_content": STASH_CONTENT,
        "upgrades": ACTIVE_UPGRADES, "achievements": ACHIEVEMENTS,
        "daily_bonus": DAILY_BONUS_CLAIMED, "last_date": LAST_PLAY_DATE
    }
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n💾 Игра сохранена!")
        time.sleep(0.5)
    except:
        print("\n⚠️ Ошибка сохранения")
        time.sleep(1)

def load_game():
    global TOTAL_WALLET, STASH_LVL, MAX_STASH_HP, MAX_STASH_WEIGHT, AMMO_STOCK
    global MEDKITS_STOCK, DETECTOR_LEVEL, STASH_CONTENT, ACTIVE_UPGRADES, ACHIEVEMENTS
    global DAILY_BONUS_CLAIMED, LAST_PLAY_DATE
    if SAVE_PATH.exists():
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                TOTAL_WALLET = d.get("wallet", 0)
                STASH_LVL = d.get("stash_lvl", 1)
                MAX_STASH_HP = d.get("max_hp", 100)
                MAX_STASH_WEIGHT = d.get("max_weight", 3000)
                AMMO_STOCK = d.get("ammo", 100)
                MEDKITS_STOCK = d.get("med", 3)
                DETECTOR_LEVEL = d.get("detector", 0)
                STASH_CONTENT = d.get("stash_content", {})
                ACTIVE_UPGRADES = d.get("upgrades", [])
                ACHIEVEMENTS = d.get("achievements", {})
                DAILY_BONUS_CLAIMED = d.get("daily_bonus", False)
                LAST_PLAY_DATE = d.get("last_date", "")
        except:
            pass

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_heat_bar(heat):
    bar = "█" * (heat // 10) + "░" * (10 - (heat // 10))
    color = "\033[32m" if heat < 40 else "\033[33m" if heat < 80 else "\033[31m"
    return f"{color}[{bar}] {heat}%\033[0m"

def get_stash_weight():
    return sum(STASH_CONTENT.values())

def add_to_stash(item_name, weight):
    if get_stash_weight() + weight <= MAX_STASH_WEIGHT:
        STASH_CONTENT[item_name] = STASH_CONTENT.get(item_name, 0) + weight
        return True
    return False

def start_masking():
    global MASKING_PROGRESS, MASK_THREAD, STASH_MASKED
    if STASH_MASKED:
        return False, "Схрон уже замаскирован!"
    if MASKING_PROGRESS > 0 and MASKING_PROGRESS < 100:
        return False, f"Маскировка уже идёт! {MASKING_PROGRESS:.0f}%"
    MASKING_PROGRESS = 0
    STASH_MASKED = False
    def masking_process():
        global MASKING_PROGRESS, STASH_MASKED
        for i in range(1, 41):
            if MASKING_PROGRESS == -1:
                break
            time.sleep(1)
            MASKING_PROGRESS = i * 2.5
            if i == 40:
                STASH_MASKED = True
                MASKING_PROGRESS = 100
    MASK_THREAD = threading.Thread(target=masking_process)
    MASK_THREAD.daemon = True
    MASK_THREAD.start()
    return True, "Начинаю маскировку схрона... (40 сек)"

def unmask_stash():
    global STASH_MASKED, MASKING_PROGRESS
    if STASH_MASKED:
        STASH_MASKED = False
        MASKING_PROGRESS = 0
        return True, "Маскировка снята!"
    return False, "Схрон не замаскирован"

def daily_bonus():
    global DAILY_BONUS_CLAIMED, TOTAL_WALLET, LAST_PLAY_DATE
    today = datetime.now().strftime("%Y-%m-%d")
    if LAST_PLAY_DATE != today:
        DAILY_BONUS_CLAIMED = False
    if not DAILY_BONUS_CLAIMED:
        bonus = random.randint(3000, 10000)
        TOTAL_WALLET += bonus
        DAILY_BONUS_CLAIMED = True
        LAST_PLAY_DATE = today
        return True, bonus
    return False, 0

def check_achievements():
    global TOTAL_WALLET, AMMO_STOCK, MEDKITS_STOCK, MAX_STASH_WEIGHT
    if not ACHIEVEMENTS.get("first_raid", False):
        ACHIEVEMENTS["first_raid"] = True
        TOTAL_WALLET += 3000
        print("\n🏆 ДОСТИЖЕНИЕ: Первый рейд! +3000 р.")
        time.sleep(1)
    if STASH_LVL >= 2 and not ACHIEVEMENTS.get("upgrade", False):
        ACHIEVEMENTS["upgrade"] = True
        MAX_STASH_WEIGHT += 500
        print("\n🏆 ДОСТИЖЕНИЕ: Улучшение! +500 г к весу схрона")
        time.sleep(1)
    if TOTAL_WALLET >= 100000 and not ACHIEVEMENTS.get("rich", False):
        ACHIEVEMENTS["rich"] = True
        AMMO_STOCK += 50
        MEDKITS_STOCK += 2
        print("\n🏆 ДОСТИЖЕНИЕ: Богач! +50 патронов, +2 аптечки")
        time.sleep(1)
    if DETECTOR_LEVEL >= 3 and not ACHIEVEMENTS.get("detector", False):
        ACHIEVEMENTS["detector"] = True
        TOTAL_WALLET += 10000
        print("\n🏆 ДОСТИЖЕНИЕ: Ищейка! +10000 р.")
        time.sleep(1)
    save_game()

def random_event(hp, max_hp, heat, ammo, medkits, money, dmg_mod, armor):
    art_chance = 0.0
    if DETECTOR_LEVEL == 1:
        art_chance = 0.05
    elif DETECTOR_LEVEL == 2:
        art_chance = 0.10
    elif DETECTOR_LEVEL == 3:
        art_chance = 0.18

    events = [
        ("🌋 РАДИОАКТИВНЫЙ ВСПЛЕСК", "Земля под ногами засветилась!",
         lambda: (max(0, hp - int(random.randint(10, 20) * armor)), heat + 15, money, ammo, medkits, None)),
        ("💎 НАХОДКА", "Ты нашёл старую монету.",
         lambda: (hp, heat, money + random.randint(2000, 8000), ammo, medkits, None)),
        ("📦 ТАЙНИК", "Старый рюкзак с патронами.",
         lambda: (hp, heat, money, ammo + 20, medkits, None)),
        ("🌀 АНОМАЛЬНЫЙ ТУМАН", "Всё вокруг затянуло, трудно дышать.",
         lambda: (max(0, hp - int(random.randint(8, 15) * armor)), heat + 12, money, ammo, medkits, None)),
        ("🔫 ЗАСАДА", "Из кустов выскочили бандиты!",
         lambda: (max(0, hp - int(random.randint(15, 30) * dmg_mod * armor)), heat + 20, money, max(0, ammo - 15), medkits, None)),
        ("📡 СТАРАЯ РАЦИЯ", "Ты услышал координаты тайника.",
         lambda: (hp, heat, money + random.randint(1000, 5000), ammo, medkits, None)),
    ]
    if art_chance > 0 and random.random() < art_chance:
        art_name = random.choice(list(ARTIFACTS.keys()))
        events.append((f"🔍 АРТЕФАКТ: {ARTIFACTS[art_name]['emoji']} {art_name}",
                       f"Детектор запищал! Ты нашёл {art_name}.",
                       lambda: (hp, heat, money, ammo, medkits, art_name)))
    else:
        events.append(("🔍 ПУСТО", "Ничего не произошло.",
                       lambda: (hp, heat, money, ammo, medkits, None)))

    name, desc, effect = random.choice(events)
    print(f"\n⚠️ {name} ⚠️")
    print(desc)
    time.sleep(1)
    hp, heat, money, ammo, medkits, artifact = effect()
    return hp, heat, money, ammo, medkits, artifact

# ======================= ОСНОВНОЙ РЕЙД =======================
def run_raid(build, location):
    global AMMO_STOCK, MEDKITS_STOCK, STASH_CONTENT, STASH_MASKED, TOTAL_WALLET

    heat_reduce = 1.0
    dmg_bonus = 1.0
    for up in ACTIVE_UPGRADES:
        if UPGRADES[up]["effect"] == "heat_reduce":
            heat_reduce = UPGRADES[up]["value"]
        elif UPGRADES[up]["effect"] == "dmg_bonus":
            dmg_bonus = UPGRADES[up]["value"]

    max_hp = build["health"]
    armor = build["armor"]
    hp = max_hp
    stash_hp = MAX_STASH_HP
    ammo = AMMO_STOCK
    medkits = MEDKITS_STOCK
    money = 0
    heat = 0
    farm_cd = 0
    enemy_group = "ЗАРЯ" if location == "Лабиринт" else "РУБЕЖ"
    last_log = "ПДА: Выхожу на связь..."
    current_loot = {}
    turn_count = 0

    while hp > 0 and stash_hp > 0:
        turn_count += 1
        clear()

        mask_status = "🔒 ЗАМАСКИРОВАН" if STASH_MASKED else "⚠️ ВИДИМЫЙ"
        mask_progress = f" ({MASKING_PROGRESS:.0f}%)" if 0 < MASKING_PROGRESS < 100 else ""

        detector_str = "❌" if DETECTOR_LEVEL == 0 else f"Ур.{DETECTOR_LEVEL}"
        print(f"🔹 ЛОКАЦИЯ: {location}  |  👤 {build['name']} ({build['weapon']})")
        print(f"🛡️ БРОНЯ: Научка | 🔫 БК: {ammo} | 📡 ДЕТЕКТОР: {detector_str}")
        print(f"📦 СХРОН: {mask_status}{mask_progress} | Вес: {get_stash_weight()}/{MAX_STASH_WEIGHT} г")
        print("-" * 65)
        print(f"❤️ HP: {hp}/{max_hp}%  |  📦 ТАЙМЕР СХРОНА: {stash_hp}%  |  💊 АПТЕЧКИ: {medkits}")
        print(f"🔥 ПАЛЕВО: {get_heat_bar(heat)}")
        print("-" * 65)

        if current_loot:
            loot_str = ", ".join([f"{LOOT_DATA[n]['emoji']}{n}: {w}г" for n, w in list(current_loot.items())[:3]])
            if len(current_loot) > 3:
                loot_str += f" +{len(current_loot)-3}"
            print(f"🎒 ЛУТ В РЕЙДЕ: {loot_str} (всего {sum(current_loot.values())} г)")
        else:
            print("🎒 ЛУТ В РЕЙДЕ: пусто")

        print(f"💰 БЛОКИ: {money} р.")
        print(f"💬 {last_log}")
        print("-" * 65)

        print(" 1. СОБРАТЬ МЯКОТЬ\n 2. ПОМОЧЬ УЧЕНЫМ (15 патр)\n 3. АПТЕЧКА\n 4. МАСКИРОВКА СХРОНА (40 сек)")
        print(" 5. СНЯТЬ МАСКИРОВКУ\n 6. ОТДОХНУТЬ (может быть событие)\n 7. ОБЫСКАТЬ МЕСТНОСТЬ\n 8. ВЫЙТИ")

        cmd = input("\n >> ").strip()

        if cmd == "1":
            if farm_cd > 0:
                last_log = f"Место выгорело. Ждать {farm_cd} х."
                continue
            name = random.choice(list(LOOT_DATA.keys()))
            g = random.randint(*LOOT_DATA[name]["weight"])
            current_loot[name] = current_loot.get(name, 0) + g
            stash_hp -= 2
            farm_cd = random.randint(2, 4)
            heat = min(100, heat + int(10 * build['heat_mod'] * heat_reduce))
            last_log = f"🌿 +{g}г {LOOT_DATA[name]['emoji']}{name}"

        elif cmd == "2":
            if ammo < 15:
                last_log = "Не хватает патронов (нужно 15)!"
                continue
            ammo -= 15
            success_chance = 0.5 - (STASH_LVL - 1) * 0.03
            if random.random() < success_chance:
                reward = random.randint(6000, 15000)
                money += reward
                last_log = f"✅ Ученые спасены! +{reward} р."
            else:
                dmg = int(random.randint(15, 25) * build['dmg_mod'] * dmg_bonus * armor)
                hp -= dmg
                last_log = f"❌ Засада! -{dmg} HP"
            heat = min(100, heat + int(20 * build['heat_mod'] * heat_reduce))
            stash_hp -= 5

        elif cmd == "3":
            if medkits > 0:
                heal = 45
                hp = min(max_hp, hp + heal)
                medkits -= 1
                last_log = f"💊 Лечение +{heal} HP"
            else:
                last_log = "Нет аптечек!"

        elif cmd == "4":
            success, msg = start_masking()
            last_log = msg
            if success:
                print(f"\n🕐 {msg}")
                time.sleep(1)

        elif cmd == "5":
            success, msg = unmask_stash()
            last_log = msg

        elif cmd == "6":
            if farm_cd > 0:
                farm_cd -= 1
            heat = max(0, heat - 12)
            last_log = "Отдых..."
            if random.random() < 0.1:
                hp, heat, money, ammo, medkits, artifact = random_event(
                    hp, max_hp, heat, ammo, medkits, money, build['dmg_mod'] * dmg_bonus, armor
                )
                if artifact:
                    current_loot[artifact] = current_loot.get(artifact, 0) + ARTIFACTS[artifact]["weight"]
                    last_log = f"Найден артефакт: {ARTIFACTS[artifact]['emoji']}{artifact}!"
                else:
                    last_log = "Случилось непредвиденное!"

        elif cmd == "7":
            heat = min(100, heat + 5)
            artifact_chance = 0.0
            if DETECTOR_LEVEL == 1:
                artifact_chance = 0.12
            elif DETECTOR_LEVEL == 2:
                artifact_chance = 0.20
            elif DETECTOR_LEVEL == 3:
                artifact_chance = 0.30
            if artifact_chance > 0 and random.random() < artifact_chance:
                art_name = random.choice(list(ARTIFACTS.keys()))
                weight = ARTIFACTS[art_name]["weight"]
                current_loot[art_name] = current_loot.get(art_name, 0) + weight
                last_log = f"🔍 Найден артефакт: {ARTIFACTS[art_name]['emoji']} {art_name} (+{weight}г)"
            else:
                roll = random.random()
                if roll < 0.1:
                    dmg = int(15 * armor)
                    hp -= dmg
                    last_log = f"💣 ЛОВУШКА! -{dmg} HP"
                elif roll < 0.35:
                    if random.random() < 0.5:
                        ammo += 20
                        last_log = "🔫 Нашёл патроны!"
                    else:
                        medkits += 1
                        last_log = "💊 Нашёл аптечку!"
                else:
                    last_log = "🔍 Ничего не найдено."

        elif cmd == "8":
            break

        if heat > 20:
            detect = (heat / 300) * (1 + (STASH_LVL - 1) * 0.05)
            if random.random() < detect:
                dmg = int(random.randint(35, 65) * build['dmg_mod'] * dmg_bonus * armor)
                hp -= dmg
                heat = max(0, heat - 25)
                last_log = f"⚠️ {enemy_group} ОБНАРУЖИЛИ! -{dmg} HP"
                print(f"\n!!! {last_log} !!!")
                time.sleep(1.5)

        if hp <= 0:
            break

    AMMO_STOCK = ammo
    MEDKITS_STOCK = medkits

    if hp > 0:
        full_items = []
        for name, weight in current_loot.items():
            if not add_to_stash(name, weight):
                full_items.append(f"{name} ({weight}г)")
        if full_items:
            print(f"\n⚠️ СХРОН ПЕРЕПОЛНЕН! Потеряно: {', '.join(full_items)}")
        profit = money
        for n, w in current_loot.items():
            if n in LOOT_DATA:
                profit += int((w / 100) * LOOT_DATA[n]["price_100g"])
            elif n in ARTIFACTS:
                cnt = w // ARTIFACTS[n]["weight"]
                profit += cnt * ARTIFACTS[n]["price"]
        print(f"\n✅ ВЫНЕСЕНО: {profit} р.")
        if stash_hp > 50:
            bonus = random.randint(3000, 10000)
            profit += bonus
            print(f"🎁 Бонус за сохранность: +{bonus} р.")
        TOTAL_WALLET += profit
        if STASH_MASKED:
            extra = random.randint(1000, 3000)
            TOTAL_WALLET += extra
            print(f"🔒 За маскировку схрона +{extra} р.")
    else:
        print("\n💀 ТЫ ПОГИБ...")
        if STASH_MASKED:
            for name, weight in current_loot.items():
                add_to_stash(name, weight)
            print("🔒 ЗАМАСКИРОВАННЫЙ СХРОН СОХРАНИЛ ЛУТ!")
        else:
            print("⚠️ СХРОН НЕ ЗАМАСКИРОВАН! ВСЁ ПОТЕРЯНО!")
        AMMO_STOCK = max(20, AMMO_STOCK // 2)
        print(f"Потеряно 50% боезапаса. Осталось: {AMMO_STOCK}")

    save_game()
    check_achievements()
    input("\nНажми Enter...")
    return hp, 0

# ======================= МАГАЗИН =======================
def shop():
    global TOTAL_WALLET, AMMO_STOCK, MEDKITS_STOCK, DETECTOR_LEVEL, STASH_CONTENT

    while True:
        clear()
        print(f"📦 СНАБЖЕНЕЦ ЗАВЕТА | Баланс: {TOTAL_WALLET} р.")
        print("-" * 45)
        current_weight = get_stash_weight()
        print(f"📦 СХРОН: {current_weight}/{MAX_STASH_WEIGHT} г")
        if STASH_CONTENT:
            print("Содержимое:")
            for name, weight in list(STASH_CONTENT.items())[:5]:
                if name in LOOT_DATA:
                    print(f"  {LOOT_DATA[name]['emoji']} {name}: {weight}г")
                elif name in ARTIFACTS:
                    print(f"  {ARTIFACTS[name]['emoji']} {name} (артефакт): {weight}г")
            if len(STASH_CONTENT) > 5:
                print(f"  ...и ещё {len(STASH_CONTENT)-5} предметов")
        print("-" * 45)

        print(" 1. Патроны (50 шт)   - 6.000 р.")
        print(" 2. Аптечка (1 шт)    - 15.000 р.")
        if DETECTOR_LEVEL == 0:
            print(" 3. Детектор (базовый) - 50.000 р.")
        else:
            print(f" 3. Детектор (ур.{DETECTOR_LEVEL}) - улучшен")
        print(" 4. ПРОДАТЬ ЛУТ")
        print(" 5. МАСТЕРСКАЯ (улучшения оружия и детектора)")
        print(" 0. Назад")

        c = input("\n >> ").strip()

        if c == "1" and TOTAL_WALLET >= 6000:
            TOTAL_WALLET -= 6000
            AMMO_STOCK += 50
            print("✅ +50 патронов")
            time.sleep(0.5)
        elif c == "2" and TOTAL_WALLET >= 15000:
            TOTAL_WALLET -= 15000
            MEDKITS_STOCK += 1
            print("✅ +1 аптечка")
            time.sleep(0.5)
        elif c == "3" and DETECTOR_LEVEL == 0 and TOTAL_WALLET >= 50000:
            TOTAL_WALLET -= 50000
            DETECTOR_LEVEL = 1
            print("✅ Детектор куплен! Теперь вы можете находить артефакты.")
            time.sleep(1)
        elif c == "4":
            if not STASH_CONTENT:
                print("Схрон пуст!")
                time.sleep(1)
                continue
            clear()
            print("📦 ПРОДАЖА ЛУТА")
            print("-" * 45)
            items = list(STASH_CONTENT.items())
            sellable = []
            for i, (name, weight) in enumerate(items, 1):
                if name in LOOT_DATA:
                    price = int((weight / 100) * LOOT_DATA[name]["price_100g"])
                    print(f"{i}. {LOOT_DATA[name]['emoji']} {name}: {weight}г = {price} р.")
                    sellable.append((name, price, weight))
                elif name in ARTIFACTS:
                    cnt = weight // ARTIFACTS[name]["weight"]
                    price = cnt * ARTIFACTS[name]["price"]
                    print(f"{i}. {ARTIFACTS[name]['emoji']} {name} (артефакт): {weight}г ({cnt} шт) = {price} р.")
                    sellable.append((name, price, weight))
            print("\n0. Назад")
            print("Введите номер для продажи или 'all'")
            sell_cmd = input("\n >> ").strip()
            if sell_cmd == "all":
                total = 0
                for name, price, w in sellable:
                    total += price
                    del STASH_CONTENT[name]
                TOTAL_WALLET += total
                print(f"💰 Продано всё! +{total} р.")
                time.sleep(1.5)
            elif sell_cmd.isdigit() and 1 <= int(sell_cmd) <= len(sellable):
                name, price, w = sellable[int(sell_cmd)-1]
                TOTAL_WALLET += price
                del STASH_CONTENT[name]
                print(f"💰 Продано! +{price} р.")
                time.sleep(1)
        elif c == "5":
            upgrade_shop()
        elif c == "0":
            break
        save_game()

def upgrade_shop():
    global TOTAL_WALLET, ACTIVE_UPGRADES, DETECTOR_LEVEL
    while True:
        clear()
        print("🔧 МАСТЕРСКАЯ")
        print("-" * 45)
        print("Улучшения оружия:")
        if not ACTIVE_UPGRADES:
            print("  Нет")
        else:
            for up in ACTIVE_UPGRADES:
                print(f"  + {UPGRADES[up]['name']}")
        print("-" * 45)
        for key, up in UPGRADES.items():
            if key not in ACTIVE_UPGRADES:
                print(f"{key[0].upper()}. {up['name']} - {up['cost']} р.")
        print("-" * 45)
        print("Улучшение детектора:")
        if DETECTOR_LEVEL == 0:
            print("  Детектор не куплен")
        elif DETECTOR_LEVEL == 1:
            print("  D. Улучшить до уровня 2 - 60.000 р.")
        elif DETECTOR_LEVEL == 2:
            print("  D. Улучшить до уровня 3 - 80.000 р.")
        else:
            print("  Максимальный уровень")
        print("0. Назад")

        c = input("\n >> ").strip().lower()
        if c == "0":
            break
        for key in UPGRADES:
            if c == key[0] and key not in ACTIVE_UPGRADES:
                if TOTAL_WALLET >= UPGRADES[key]["cost"]:
                    TOTAL_WALLET -= UPGRADES[key]["cost"]
                    ACTIVE_UPGRADES.append(key)
                    print(f"✅ {UPGRADES[key]['name']} куплен!")
                    time.sleep(1)
                    save_game()
                else:
                    print(f"💰 Не хватает {UPGRADES[key]['cost'] - TOTAL_WALLET} р.")
                    time.sleep(1)
                break
        if c == "d":
            if DETECTOR_LEVEL == 1:
                if TOTAL_WALLET >= 60000:
                    TOTAL_WALLET -= 60000
                    DETECTOR_LEVEL = 2
                    print("✅ Детектор улучшен до уровня 2! Шанс найти артефакт выше.")
                    time.sleep(1)
                    save_game()
                else:
                    print(f"💰 Не хватает {60000 - TOTAL_WALLET} р.")
                    time.sleep(1)
            elif DETECTOR_LEVEL == 2:
                if TOTAL_WALLET >= 80000:
                    TOTAL_WALLET -= 80000
                    DETECTOR_LEVEL = 3
                    print("✅ Детектор улучшен до уровня 3! Максимальный шанс найти артефакт.")
                    time.sleep(1)
                    save_game()
                else:
                    print(f"💰 Не хватает {80000 - TOTAL_WALLET} р.")
                    time.sleep(1)
            else:
                print("Невозможно улучшить.")
                time.sleep(1)

# ======================= ОСНОВНОЙ ЦИКЛ =======================
def main():
    global TOTAL_WALLET, STASH_LVL, MAX_STASH_HP, MAX_STASH_WEIGHT, AMMO_STOCK, MEDKITS_STOCK
    load_game()

    claimed, bonus = daily_bonus()
    if claimed:
        print(f"\n🎁 ЕЖЕДНЕВНЫЙ БОНУС: +{bonus} р.")
        time.sleep(2)

    while True:
        clear()
        print("╔═══════════════════════════════════════════╗")
        print("║      🏠 БАЗА ГРУППИРОВКИ 'ЗАВЕТ'          ║")
        print("╠═══════════════════════════════════════════╣")
        print(f"║ 💰 КОШЕЛЕК: {TOTAL_WALLET:<10} р.              ║")
        print(f"║ 🛠️ СХРОН: Ур.{STASH_LVL} ({MAX_STASH_HP}% HP, {MAX_STASH_WEIGHT} г)  ║")
        print("╚═══════════════════════════════════════════╝")
        print(" 1. В ЛАБИРИНТ (ЗАРЯ)")
        print(" 2. В ОТРАЖЕНИЕ (РУБЕЖ)")
        print(" 3. К СНАБЖЕНЦУ")
        print(" 4. УЛУЧШИТЬ СХРОН")
        print(" 5. ВЫХОД")

        m_cmd = input("\n >> ").strip()

        if m_cmd in ["1", "2"]:
            loc = "Лабиринт" if m_cmd == "1" else "Отражение"
            clear()
            print(" ВЫБОР БИЛДА:")
            print(" 1. Стелс Сатурн (ВСС-М) — быстрый, хрупкий, тихий")
            print(" 2. Антарес (ПКП Печенег) — жирный, пулестойкий, мощный")
            p_idx = input(" >> ").strip()
            if p_idx == "1":
                build = BUILDS["stealth"]
            elif p_idx == "2":
                build = BUILDS["heavy"]
            else:
                continue
            run_raid(build, loc)

        elif m_cmd == "3":
            shop()
        elif m_cmd == "4":
            cost = 100000 * STASH_LVL
            if TOTAL_WALLET >= cost:
                TOTAL_WALLET -= cost
                STASH_LVL += 1
                MAX_STASH_HP += 20
                MAX_STASH_WEIGHT += 1500
                print(f"✅ Схрон улучшен до {STASH_LVL} уровня!")
                save_game()
            else:
                print(f"💰 Не хватает {cost - TOTAL_WALLET} р.")
                time.sleep(1.5)
        elif m_cmd == "5":
            break

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ошибка: {e}")
        input()