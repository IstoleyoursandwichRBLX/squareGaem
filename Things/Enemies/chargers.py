import pygame
import math
import random
import statuses

chargerSize = 75 * 1.05
chargerMaxHP = 20
chargerTouchDamage = 20
chargerChargeTouchDamage = 35

chargerWindupDuration = 500
chargerChargeDuration = 2000
chargerChargeCooldown = 5000
chargerChargeSpeedMultiplier = 4
chargerKnockbackFriction = 0.85
chargerPunchKnockbackAmount = 55
 
def createChargerSurface(size):
    intSize = int(size)
    surface = pygame.Surface((intSize, intSize), pygame.SRCALPHA)

    pygame.draw.rect(surface, (20, 20, 140), (0, 0, intSize, intSize))
    pygame.draw.rect(surface, (255, 255, 255), (0, 0, intSize, intSize), width = 6)

    return surface

def spawnChargers(count, baseEnemySpeed, playerX, playerY, currentTime):
    speed = baseEnemySpeed

    newChargers = []
    for _ in range(count):
        dist = random.randint(400, 700)
        angle = random.uniform(0, math.pi * 2)
        x = playerX + math.cos(angle) * dist
        y = playerY + math.sin(angle) * dist

        newChargers.append({
            "x": x,
            "y": y,
            "hp": chargerMaxHP,
            "max_hp": chargerMaxHP,
            "speed": speed,
            "last_hit": -9999,
            "chargeState": "idle",
            "chargeStateStart": 0,
            "lastCharge": currentTime,
            "chargeDirX": 0,
            "chargeDirY": 0,
            "chargeAfterimages": [],
            "knockbackX": 0,
            "knockbackY": 0
        })

    return newChargers

def updateChargerMovement(charger, playerX, playerY, currentTime):
    knockbackX = charger.get("knockbackX", 0)
    knockbackY = charger.get("knockbackY", 0)

    if abs(knockbackX) > 0.5 or abs(knockbackY) > 0.5:
        charger["x"] += knockbackX
        charger["y"] += knockbackY
        charger["knockbackX"] = knockbackX * chargerKnockbackFriction
        charger["knockbackY"] = knockbackY * chargerKnockbackFriction
        return

    charger["knockbackX"] = 0
    charger["knockbackY"] = 0

    state = charger["chargeState"]

    if state == "idle":
        dx = playerX - charger["x"]
        dy = playerY - charger["y"]
        dist = math.sqrt(dx * dx + dy * dy)

        speed = statuses.getEffectiveSpeed(charger, currentTime)

        if dist > 0:
            charger["x"] += (dx / dist) * speed
            charger["y"] += (dy / dist) * speed

        if currentTime - charger["lastCharge"] >= chargerChargeCooldown:
            charger["chargeState"] = "windup"
            charger["chargeStateStart"] = currentTime

    elif state == "windup":
        if currentTime - charger["chargeStateStart"] >= chargerWindupDuration:
            dx = playerX - charger["x"]
            dy = playerY - charger["y"]
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > 0:
                charger["chargeDirX"] = dx / dist
                charger["chargeDirY"] = dy / dist
            else:
                charger["chargeDirX"], charger["chargeDirY"] = 0, -1
 
            charger["chargeState"] = "charging"
            charger["chargeStateStart"] = currentTime
            charger["lastCharge"] = currentTime

    elif state == "charging":
        chargeElapsed = currentTime - charger["chargeStateStart"]
 
        if chargeElapsed >= chargerChargeDuration:
            charger["chargeState"] = "idle"
        else:
            speed = charger["speed"] * chargerChargeSpeedMultiplier
            charger["x"] += charger["chargeDirX"] * speed
            charger["y"] += charger["chargeDirY"] * speed
 
            charger["chargeAfterimages"].append({
                "x": charger["x"],
                "y": charger["y"],
                "alpha": 160
            })

def interruptChargeWithPunch(charger, punchDirX, punchDirY):
    charger["chargeState"] = "idle"
    charger["knockbackX"] = punchDirX * chargerPunchKnockbackAmount
    charger["knockbackY"] = punchDirY * chargerPunchKnockbackAmount