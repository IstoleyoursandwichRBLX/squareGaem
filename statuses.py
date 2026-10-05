import pygame

SLOWMULTIPLIER = 0.75
SLOWDURATION = 1000

FROZENDURATION = 1500
FROZENFADE = 250
ICECACHE = {}

def slowness(entity, currentTime):
    if "baseSpeed" not in entity:
        entity["baseSpeed"] = entity["speed"]

    entity["slowUntil"] = currentTime + SLOWDURATION

def getEffectiveSpeed(entity, currentTime):
    if isFrozen(entity, currentTime):
        return 0

    baseSpeed = entity.get("baseSpeed", entity["speed"])

    if entity.get("slowUntil", 0) > currentTime:
        return baseSpeed * SLOWMULTIPLIER

    return baseSpeed

def freeze(entity, currentTime, duration = FROZENDURATION):
    entity["frozenUntil"] = currentTime + duration

def isFrozen(entity, currentTime):
    return entity.get("frozenUntil", 0) > currentTime

def createIceSurface(size):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)

    pygame.draw.rect(surface, (140, 210, 255, 150), (0, 0, size, size))
    pygame.draw.rect(surface, (200, 235, 255, 90), (8, 8, size - 16, size - 16))
    pygame.draw.line(surface, (255, 255, 255, 170), (size * 0.2, size * 0.45), (size * 0.45, size * 0.2), 4)
    pygame.draw.line(surface, (255, 255, 255, 120), (size * 0.3, size * 0.6), (size * 0.6, size * 0.3), 3)
    pygame.draw.rect(surface, (230, 248, 255, 235), (0, 0, size, size), width = 5)

    return surface

def drawFrozen(surface, entity, centerX, centerY, size, currentTime):
    remaining = entity.get("frozenUntil", 0) - currentTime

    if remaining <= 0:
        return

    alpha = 255 if remaining > FROZENFADE else int(255 * remaining / FROZENFADE)
    iceSize = int(size + 16)

    if iceSize not in ICECACHE:
        ICECACHE[iceSize] = createIceSurface(iceSize)

    ice = ICECACHE[iceSize]
    ice.set_alpha(alpha)
    surface.blit(ice, ice.get_rect(center = (centerX, centerY)))