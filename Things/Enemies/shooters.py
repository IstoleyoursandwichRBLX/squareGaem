import pygame
import math
import random

shooterSize = 75
shooterMaxHP = 20
shooterSpeedMultiplier = 1.3

shooterPreferredMinDistance = 300
shooterPreferredMaxDistance = 550
shooterCowerOffset = 40

shooterShootCooldown = 3000
shooterProjectileSpeed = 10
shooterProjectileSize = 10

def createShooterSurface(size):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surface, (255, 140, 0), (0, 0, size, size))
    pygame.draw.rect(surface, (255, 255, 255), (0, 0, size, size), width=6)
    return surface

def spawnShooters(count, baseEnemySpeed, playerX, playerY):
    speed = baseEnemySpeed * shooterSpeedMultiplier

    newShooters = []
    for _ in range(count):
        dist = random.randint(400, 700)
        angle = random.uniform(0, math.pi * 2)
        x = playerX + math.cos(angle) * dist
        y = playerY + math.sin(angle) * dist

        newShooters.append({
            "x": x,
            "y": y,
            "hp": shooterMaxHP,
            "max_hp": shooterMaxHP,
            "speed": speed,
            "last_hit": -9999,
            "last_shot": -9999
        })

    return newShooters

shooterSeparationDistance = 90

def updateShooterMovement(shooter, playerX, playerY, defaultEnemies, allShooters):
    dx = shooter["x"] - playerX
    dy = shooter["y"] - playerY
    distToPlayer = math.sqrt(dx * dx + dy * dy)

    moveX = 0
    moveY = 0

    nearestDefault = None
    nearestDistSquared = None
    for e in defaultEnemies:
        edx = e["x"] - shooter["x"]
        edy = e["y"] - shooter["y"]
        edistSquared = edx * edx + edy * edy
        if nearestDistSquared is None or edistSquared < nearestDistSquared:
            nearestDistSquared = edistSquared
            nearestDefault = e

    if distToPlayer < shooterPreferredMinDistance:
        if distToPlayer > 0:
            moveX = dx / distToPlayer
            moveY = dy / distToPlayer
    elif distToPlayer > shooterPreferredMaxDistance:
        if distToPlayer > 0:
            moveX = -dx / distToPlayer
            moveY = -dy / distToPlayer
    else:
        if nearestDefault is not None:
            ddx = playerX - shooter["x"]
            ddy = playerY - shooter["y"]
            dDist = math.sqrt(ddx * ddx + ddy * ddy)
            if dDist > 0:
                behindX = nearestDefault["x"] + (ddx / dDist) * -shooterCowerOffset
                behindY = nearestDefault["y"] + (ddy / dDist) * -shooterCowerOffset
                tx = behindX - shooter["x"]
                ty = behindY - shooter["y"]
                tDist = math.sqrt(tx * tx + ty * ty)
                if tDist > 5:
                    moveX = tx / tDist
                    moveY = ty / tDist

    sepX = 0
    sepY = 0
    for other in allShooters:
        if other is shooter:
            continue

        odx = shooter["x"] - other["x"]
        ody = shooter["y"] - other["y"]
        oDist = math.sqrt(odx * odx + ody * ody)

        if 0 < oDist < shooterSeparationDistance:
            pushStrength = (shooterSeparationDistance - oDist) / shooterSeparationDistance
            sepX += (odx / oDist) * pushStrength
            sepY += (ody / oDist) * pushStrength

    moveX += sepX
    moveY += sepY

    moveLength = math.sqrt(moveX * moveX + moveY * moveY)
    if moveLength > 0:
        moveX /= moveLength
        moveY /= moveLength

    shooter["x"] += moveX * shooter["speed"]
    shooter["y"] += moveY * shooter["speed"]

def tryShooterShoot(shooter, currentTime, playerX, playerY):
    if currentTime - shooter["last_shot"] >= shooterShootCooldown:
        shooter["last_shot"] = currentTime

        dx = playerX - shooter["x"]
        dy = playerY - shooter["y"]
        dist = math.sqrt(dx * dx + dy * dy)

        if dist == 0:
            dx, dy = 0, -1
        else:
            dx /= dist
            dy /= dist

        return {
            "x": shooter["x"],
            "y": shooter["y"],
            "dx": dx * shooterProjectileSpeed,
            "dy": dy * shooterProjectileSpeed
        }

    return None