import math
import random

import pygame

icemanName = "Iceman"
icemanSize = 110
icemanMaxHP = 400
icemanTouchDamage = 20
icemanTouchCooldown = 2000
icemanSpawnDistance = 650
icemanImagePath = "Things/Images/Iceman.png"

icemanDodgeCooldown = 2000
icemanDodgeDuration = 200
icemanDodgeSpeed = 16
icemanDodgeRecheck = 500

icemanBulletDetectRadius = 380
icemanBulletDodgeChance = 0.6
icemanBulletReactionDelay = 150

icemanPunchDetectRadius = 300
icemanPunchDodgeChance = 0.35
icemanPunchReactionDelay = 0

icemanSlideCooldown = 2000
icemanSlideDuration = 3000
icemanSlideSpeedMultiplier = 2
icemanSlideSteer = 0.035
icemanSlideMinDistance = 450

icemanFreezeCooldown = 7500
icemanFreezeTrackDuration = 1000
icemanFreezeFadeDuration = 300
icemanFreezeDamage = 30
icemanFreezeSizeMultiplier = 2.5
icemanFreezeMaxDistance = 900
icemanFreezeColor = (80, 170, 255)
icemanFreezeAlpha = 128
icemanFrozenDuration = 1500

icemanDecisionInterval = 250
icemanSlideFrozenDistance = 200
icemanFreezeStillSpeed = 3.5
icemanFreezeCloseDistance = 300
icemanFreezeCloseSpeed = 5
icemanFreezeOverdue = 5000


def createIcemanSurface(size = icemanSize):
    image = pygame.image.load(icemanImagePath).convert_alpha()
    return pygame.transform.smoothscale(image, (int(size), int(size)))


def spawnIceman(playerX, playerY, speed):
    angle = random.uniform(0, math.pi * 2)

    return {
        "x": playerX + math.cos(angle) * icemanSpawnDistance,
        "y": playerY + math.sin(angle) * icemanSpawnDistance,
        "hp": icemanMaxHP,
        "max_hp": icemanMaxHP,
        "speed": speed,
        "last_hit": -9999,
        "dodgeState": "none",
        "dodgeStart": 0,
        "dodgeDirX": 0,
        "dodgeDirY": 0,
        "reactStart": 0,
        "reactDelay": 0,
        "lastDodge": -9999,
        "nextCheck": 0,
        "slideState": "none",
        "slideStart": 0,
        "velX": 0,
        "velY": 0,
        "lastSlide": -9999,
        "freezeState": "none",
        "freezeStart": 0,
        "freezeX": 0,
        "freezeY": 0,
        "lastFreeze": -9999
    }


def updateIcemanMovement(iceman, playerX, playerY):
    dx = playerX - iceman["x"]
    dy = playerY - iceman["y"]
    dist = math.sqrt(dx * dx + dy * dy)

    if dist > 0:
        iceman["x"] += (dx / dist) * iceman["speed"]
        iceman["y"] += (dy / dist) * iceman["speed"]


def overlaps(iceman, x, y, size):
    half = (icemanSize + size) / 2
    return abs(iceman["x"] - x) < half and abs(iceman["y"] - y) < half


def tryTouchDamage(iceman, playerX, playerY, playerSize, currentTime):
    if not overlaps(iceman, playerX, playerY, playerSize):
        return 0

    if currentTime - iceman["last_hit"] < icemanTouchCooldown:
        return 0

    iceman["last_hit"] = currentTime
    return icemanTouchDamage


def damage(iceman, amount):
    iceman["hp"] -= amount


def touchesSegment(iceman, x1, y1, x2, y2, width):
    dx = x2 - x1
    dy = y2 - y1
    lengthSquared = dx * dx + dy * dy

    if lengthSquared == 0:
        t = 0
    else:
        t = ((iceman["x"] - x1) * dx + (iceman["y"] - y1) * dy) / lengthSquared
        t = max(0, min(1, t))

    closestX = x1 + t * dx
    closestY = y1 + t * dy
    distSquared = (iceman["x"] - closestX) ** 2 + (iceman["y"] - closestY) ** 2

    return distSquared <= (width / 2 + icemanSize / 2) ** 2

def findThreat(iceman, projectiles, punching, playerX, playerY, punchDirX, punchDirY):
    if punching:
        toX = iceman["x"] - playerX
        toY = iceman["y"] - playerY
        dist = math.sqrt(toX * toX + toY * toY)

        if 0 < dist <= icemanPunchDetectRadius:
            if (toX * punchDirX + toY * punchDirY) / dist > 0.85:
                return punchDirX, punchDirY, icemanPunchDodgeChance, icemanPunchReactionDelay

    for p in projectiles:
        toX = iceman["x"] - p["x"]
        toY = iceman["y"] - p["y"]
        dist = math.sqrt(toX * toX + toY * toY)
        speed = math.sqrt(p["dx"] * p["dx"] + p["dy"] * p["dy"])

        if dist == 0 or speed == 0 or dist > icemanBulletDetectRadius:
            continue

        if (toX * p["dx"] + toY * p["dy"]) / (dist * speed) > 0.92:
            return p["dx"] / speed, p["dy"] / speed, icemanBulletDodgeChance, icemanBulletReactionDelay

    return None


def stepDodge(iceman):
    iceman["x"] += iceman["dodgeDirX"] * icemanDodgeSpeed
    iceman["y"] += iceman["dodgeDirY"] * icemanDodgeSpeed


def updateIcemanDodge(iceman, currentTime, projectiles, punching, playerX, playerY, punchDirX, punchDirY):
    state = iceman["dodgeState"]

    if state == "dodging":
        if currentTime - iceman["dodgeStart"] >= icemanDodgeDuration:
            iceman["dodgeState"] = "none"
            iceman["lastDodge"] = currentTime
            return False

        stepDodge(iceman)
        return True

    if state == "reacting":
        if currentTime - iceman["reactStart"] < iceman["reactDelay"]:
            return False

        iceman["dodgeState"] = "dodging"
        iceman["dodgeStart"] = currentTime
        stepDodge(iceman)
        return True

    if currentTime - iceman["lastDodge"] < icemanDodgeCooldown or currentTime < iceman["nextCheck"]:
        return False

    threat = findThreat(iceman, projectiles, punching, playerX, playerY, punchDirX, punchDirY)

    if threat is None:
        return False

    threatDirX, threatDirY, chance, delay = threat
    iceman["nextCheck"] = currentTime + icemanDodgeRecheck

    if random.random() > chance:
        return False

    side = random.choice((-1, 1))
    iceman["dodgeDirX"] = -threatDirY * side
    iceman["dodgeDirY"] = threatDirX * side
    iceman["dodgeState"] = "reacting"
    iceman["reactStart"] = currentTime
    iceman["reactDelay"] = delay

    return False

def startIceman(iceman, currentTime):
    iceman["lastSlide"] = currentTime - icemanSlideCooldown + 3000
    iceman["lastFreeze"] = currentTime - icemanFreezeCooldown + 6000


def updateSlideMovement(iceman, playerX, playerY):
    dx = playerX - iceman["x"]
    dy = playerY - iceman["y"]
    dist = math.sqrt(dx * dx + dy * dy)

    if dist > 0:
        topSpeed = iceman["speed"] * icemanSlideSpeedMultiplier
        targetX = dx / dist * topSpeed
        targetY = dy / dist * topSpeed

        iceman["velX"] += (targetX - iceman["velX"]) * icemanSlideSteer
        iceman["velY"] += (targetY - iceman["velY"]) * icemanSlideSteer

    iceman["x"] += iceman["velX"]
    iceman["y"] += iceman["velY"]


def chooseAbility(iceman, currentTime, dist, playerFrozen, playerInvincible):
    slideReady = currentTime - iceman["lastSlide"] >= icemanSlideCooldown
    freezeReady = currentTime - iceman["lastFreeze"] >= icemanFreezeCooldown
    playerSpeed = iceman.get("playerSpeed", 0)

    if freezeReady and not playerFrozen and not playerInvincible and dist <= icemanFreezeMaxDistance:
        standingStill = playerSpeed <= icemanFreezeStillSpeed
        closeAndSteady = dist <= icemanFreezeCloseDistance and playerSpeed <= icemanFreezeCloseSpeed
        overdue = currentTime - iceman["lastFreeze"] >= icemanFreezeCooldown + icemanFreezeOverdue

        if standingStill or closeAndSteady or overdue:
            return "freeze"

    if slideReady:
        if playerFrozen and dist >= icemanSlideFrozenDistance:
            return "slide"

        if dist >= icemanSlideMinDistance:
            return "slide"

    return None


def updateIcemanAbilities(iceman, currentTime, playerX, playerY, playerSize, playerInvincible, playerFrozen):
    damage = 0
    froze = False

    radius = playerSize * icemanFreezeSizeMultiplier / 2

    lastX = iceman.get("lastPX", playerX)
    lastY = iceman.get("lastPY", playerY)
    moved = math.sqrt((playerX - lastX) ** 2 + (playerY - lastY) ** 2)
    iceman["playerSpeed"] = iceman.get("playerSpeed", 0) * 0.9 + moved * 0.1
    iceman["lastPX"] = playerX
    iceman["lastPY"] = playerY

    if iceman["freezeState"] == "tracking":
        iceman["freezeX"] = playerX
        iceman["freezeY"] = playerY

        if currentTime - iceman["freezeStart"] >= icemanFreezeTrackDuration:
            iceman["freezeState"] = "fading"
            iceman["freezeStart"] = currentTime

    elif iceman["freezeState"] == "fading":
        if currentTime - iceman["freezeStart"] >= icemanFreezeFadeDuration:
            iceman["freezeState"] = "none"
            iceman["lastFreeze"] = currentTime

            freezeDX = playerX - iceman["freezeX"]
            freezeDY = playerY - iceman["freezeY"]

            if not playerInvincible and freezeDX * freezeDX + freezeDY * freezeDY <= radius * radius:
                damage = icemanFreezeDamage
                froze = True

    if iceman["slideState"] == "sliding" and currentTime - iceman["slideStart"] >= icemanSlideDuration:
        iceman["slideState"] = "none"
        iceman["lastSlide"] = currentTime

    idle = (
        iceman["slideState"] == "none"
        and iceman["freezeState"] == "none"
        and iceman["dodgeState"] == "none"
    )

    if idle and currentTime >= iceman.get("nextDecision", 0):
        iceman["nextDecision"] = currentTime + icemanDecisionInterval

        dx = playerX - iceman["x"]
        dy = playerY - iceman["y"]
        dist = math.sqrt(dx * dx + dy * dy)

        choice = chooseAbility(iceman, currentTime, dist, playerFrozen, playerInvincible)

        if choice == "slide":
            iceman["slideState"] = "sliding"
            iceman["slideStart"] = currentTime

            if dist > 0:
                iceman["velX"] = dx / dist * iceman["speed"]
                iceman["velY"] = dy / dist * iceman["speed"]

        elif choice == "freeze":
            iceman["freezeState"] = "tracking"
            iceman["freezeStart"] = currentTime
            iceman["freezeX"] = playerX
            iceman["freezeY"] = playerY

    return damage, froze


def updateIcemanBehaviour(iceman, currentTime, projectiles, punching, playerX, playerY, playerSize, punchDirX, punchDirY, playerInvincible, playerFrozen):
    damage, froze = updateIcemanAbilities(iceman, currentTime, playerX, playerY, playerSize, playerInvincible, playerFrozen)

    if iceman["slideState"] == "sliding":
        updateSlideMovement(iceman, playerX, playerY)
    elif not updateIcemanDodge(iceman, currentTime, projectiles, punching, playerX, playerY, punchDirX, punchDirY):
        updateIcemanMovement(iceman, playerX, playerY)

    return damage, froze


def drawFreezeIndicator(surface, iceman, cameraX, cameraY, playerSize, currentTime):
    state = iceman["freezeState"]

    if state == "none":
        return

    if state == "tracking":
        alpha = icemanFreezeAlpha
    else:
        fadeT = min((currentTime - iceman["freezeStart"]) / icemanFreezeFadeDuration, 1)
        alpha = int(icemanFreezeAlpha * (1 - fadeT))

    if alpha <= 0:
        return

    radius = int(playerSize * icemanFreezeSizeMultiplier / 2)
    circle = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    center = (radius, radius)

    pygame.draw.circle(circle, (*icemanFreezeColor, alpha), center, radius)
    pygame.draw.circle(circle, (190, 230, 255, min(255, alpha * 2)), center, radius, width = 4)

    surface.blit(circle, (iceman["freezeX"] - cameraX - radius, iceman["freezeY"] - cameraY - radius))