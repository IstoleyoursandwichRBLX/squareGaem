SLOWMULTIPLIER = 0.75
SLOWDURATION = 1000

def slowness(entity, currentTime):
    if "baseSpeed" not in entity:
        entity["baseSpeed"] = entity["speed"]

    entity["slowUntil"] = currentTime + SLOWDURATION

def getEffectiveSpeed(entity, currentTime):
    baseSpeed = entity.get("baseSpeed", entity["speed"])

    if entity.get("slowUntil", 0) > currentTime:
        return baseSpeed * SLOWMULTIPLIER

    return baseSpeed