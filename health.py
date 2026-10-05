import os
import pygame
import math

FONTPATH = "Things/Fonts/PressStart2P.ttf"

FADEDURATION = 1500
TRAILDELAY = 500
TRAILDRAIN = 0.35

BARWIDTHRATIO = 0.6
BARMAXWIDTH = 900
BARHEIGHT = 22
BARTOP = 40
NAMEGAP = 8

FRAMECOLOR = (12, 8, 8)
BORDERCOLOR = (210, 205, 195)
FILLCOLOR = (165, 25, 25)
HIGHLIGHTCOLOR = (205, 55, 55)
TRAILCOLOR = (215, 175, 60)
NAMECOLOR = (235, 230, 220)
SHADOWCOLOR = (0, 0, 0)

FONTCACHE = {}


def font(size):
    if size not in FONTCACHE:
        if os.path.exists(FONTPATH):
            FONTCACHE[size] = pygame.font.Font(FONTPATH, size)
        else:
            FONTCACHE[size] = pygame.font.SysFont("monospace", size, bold = True)

    return FONTCACHE[size]


def easeOutExpo(t):
    if t >= 1:
        return 1.0

    if t <= 0:
        return 0.0

    return 1 - 2 ** (-10 * t)


def createBossBar(name, maxHealth, startTime):
    nameFont = font(16)

    return {
        "name": name,
        "maxHealth": float(maxHealth),
        "startTime": startTime,
        "trailHealth": float(maxHealth),
        "lastHealth": float(maxHealth),
        "lastDamageTime": startTime,
        "lastTime": startTime,
        "nameSurface": nameFont.render(name, False, NAMECOLOR),
        "shadowSurface": nameFont.render(name, False, SHADOWCOLOR)
    }


def drawBossBar(surface, bar, currentHealth, now):
    maxHealth = bar["maxHealth"]
    currentHealth = max(0.0, min(float(currentHealth), maxHealth))

    if currentHealth < bar["lastHealth"]:
        bar["lastDamageTime"] = now

    bar["lastHealth"] = currentHealth

    deltaTime = max(0, now - bar["lastTime"])
    bar["lastTime"] = now

    if bar["trailHealth"] > currentHealth:
        if now - bar["lastDamageTime"] >= TRAILDELAY:
            bar["trailHealth"] = max(
                currentHealth,
                bar["trailHealth"] - maxHealth * TRAILDRAIN * deltaTime / 1000
            )
    else:
        bar["trailHealth"] = currentHealth

    fade = easeOutExpo((now - bar["startTime"]) / FADEDURATION)
    alpha = int(255 * fade)

    if alpha <= 0:
        return

    barWidth = min(int(surface.get_width() * BARWIDTHRATIO), BARMAXWIDTH)
    nameSurface = bar["nameSurface"]
    shadowSurface = bar["shadowSurface"]

    layerHeight = BARHEIGHT + NAMEGAP + nameSurface.get_height() + 4
    layer = pygame.Surface((barWidth + 4, layerHeight), pygame.SRCALPHA)

    pygame.draw.rect(layer, FRAMECOLOR, (0, 0, barWidth, BARHEIGHT))

    innerX = 3
    innerY = 3
    innerWidth = barWidth - 6
    innerHeight = BARHEIGHT - 6

    trailWidth = int(innerWidth * bar["trailHealth"] / maxHealth)
    fillWidth = int(innerWidth * currentHealth / maxHealth)

    if trailWidth > 0:
        pygame.draw.rect(layer, TRAILCOLOR, (innerX, innerY, trailWidth, innerHeight))

    if fillWidth > 0:
        pygame.draw.rect(layer, FILLCOLOR, (innerX, innerY, fillWidth, innerHeight))
        pygame.draw.rect(layer, HIGHLIGHTCOLOR, (innerX, innerY, fillWidth, max(2, innerHeight // 3)))

    pygame.draw.rect(layer, BORDERCOLOR, (0, 0, barWidth, BARHEIGHT), width = 2)
    shownHealth = int(math.ceil(currentHealth))

    if bar.get("shownHealth") != shownHealth:
        valueFont = font(12)
        bar["shownHealth"] = shownHealth
        bar["valueSurface"] = valueFont.render(str(shownHealth), False, NAMECOLOR)
        bar["valueShadow"] = valueFont.render(str(shownHealth), False, SHADOWCOLOR)

    valueCenter = (barWidth // 2, BARHEIGHT // 2)
    valueSurface = bar["valueSurface"]
    valueShadow = bar["valueShadow"]

    layer.blit(valueShadow, valueShadow.get_rect(center = (valueCenter[0] + 2, valueCenter[1] + 2)))
    layer.blit(valueSurface, valueSurface.get_rect(center = valueCenter))

    nameX = barWidth - nameSurface.get_width()
    nameY = BARHEIGHT + NAMEGAP

    layer.blit(shadowSurface, (nameX + 2, nameY + 2))
    layer.blit(nameSurface, (nameX, nameY))

    layer.set_alpha(alpha)
    surface.blit(layer, ((surface.get_width() - barWidth) // 2, BARTOP))