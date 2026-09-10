import pygame
import sys
import random
import asyncio
import enemies as enemyModule
import math

moveSpeed = 6
baseEnemySpeed = moveSpeed * 0.75

def createSquareSurface(color, size):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)

    pygame.draw.rect(surface, color, (0, 0, size, size))
    pygame.draw.rect(surface, (255, 255, 255), (0, 0, size, size), width = 6)
    
    return surface

def lerp(start, end, t):
    return start + (end - start) * t

def easeOut(t):
    return 1 - (1 - t) * (1 - t)

def renderTextWithOutline(font, text, textColor, outlineColor, outlineWidth = 2):
    textSurface = font.render(text, True, textColor)
    outlineSurface = pygame.Surface(
        (textSurface.get_width() + outlineWidth * 2, textSurface.get_height() + outlineWidth * 2),
        pygame.SRCALPHA
    )

    for dx in range(-outlineWidth, outlineWidth + 1):
        for dy in range(-outlineWidth, outlineWidth + 1):
            if dx != 0 or dy != 0:
                outlineText = font.render(text, True, outlineColor)
                outlineSurface.blit(outlineText, (dx + outlineWidth, dy + outlineWidth))

    outlineSurface.blit(textSurface, (outlineWidth, outlineWidth))
    return outlineSurface

deathFrames = None

async def loadDeathFrames(screen):
    global deathFrames
    if deathFrames is not None:
        return

    framesPath = "Things/Videos/deathframes"
    deathFrames = []
    font = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 30)

    try:
        import os
        frameFiles = sorted(os.listdir(framesPath))
        total = len(frameFiles)

        for i, filename in enumerate(frameFiles):
            frame = pygame.image.load(f"{framesPath}/{filename}").convert()
            frame = pygame.transform.scale(frame, (screen.get_width(), screen.get_height()))
            deathFrames.append(frame)

            screen.fill((20, 20, 20))
            text = font.render(f"Loading... {i + 1}/{total}", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=screen.get_rect().center))
            pygame.display.update()

            await asyncio.sleep(0)
    except:
        deathFrames = []

async def die(screen, color):
    global deathFrames
    frames = deathFrames if deathFrames else []

    clock = pygame.time.Clock()
    frameIndex = 0
    font = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 50)
    retryFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 70)

    deathScreenStart = pygame.time.get_ticks()
    retryTextDelay = 1000
    retryFadeDuration = 500
    retryAlpha = 0

    while True:
        currentTime = pygame.time.get_ticks()
        timeSinceDeath = currentTime - deathScreenStart

        if timeSinceDeath >= retryTextDelay:
            fadeElapsed = timeSinceDeath - retryTextDelay
            fadeT = min(fadeElapsed / retryFadeDuration, 1)
            fadeT = easeOut(fadeT)
            retryAlpha = int(lerp(0, 255, fadeT))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and retryAlpha >= 255:
                if event.key == pygame.K_SPACE:
                    await startGame(screen, color)
                    return

        if frames:
            screen.blit(frames[frameIndex], (0, 0))
            frameIndex = (frameIndex + 1) % len(frames)
        else:
            screen.fill((0, 0, 0))
            text = font.render("YOU DIED", True, (255, 0, 0))
            screen.blit(text, text.get_rect(center=screen.get_rect().center))

        if retryAlpha > 0:
            retryText = renderTextWithOutline(retryFont, "Press SPACE to Retry", (255, 255, 255), (0, 0, 0), outlineWidth = 3)
            retryText.set_alpha(retryAlpha)
            screen.blit(retryText, retryText.get_rect(center=screen.get_rect().center))

        pygame.display.update()
        clock.tick(12)
        await asyncio.sleep(0)

def spawnWave(count, playerX, playerY):
    maxHP = 10
    speed = baseEnemySpeed

    minCloseDist = min(250 + count * 6, 900)
    maxCloseDist = min(400 + count * 8, 1200)

    minFarDist = min(900 + count * 14, 2200)
    maxFarDist = min(1300 + count * 18, 2800)

    newEnemies = []

    for i in range(count):
        if i % 3 == 0:
            dist = random.randint(minCloseDist, maxCloseDist)
        else:
            dist = random.randint(minFarDist, maxFarDist)

        angle = random.uniform(0, math.pi * 2)
        x = playerX + math.cos(angle) * dist
        y = playerY + math.sin(angle) * dist

        newEnemies.append({
            "x": x,
            "y": y,
            "hp": maxHP,
            "max_hp": maxHP,
            "speed": speed,
            "last_hit": -9999
        })

    return newEnemies

def calculateWaveEnemyCount(waveNum):
    count = 5

    for _ in range(waveNum - 1):
        count = math.ceil(count * 1.25)

    return count

def spawnWaveEnemies(waveNum, playerX, playerY):
    totalCount = calculateWaveEnemyCount(waveNum)

    if waveNum >= 3:
        shooterCount = math.ceil(totalCount * 0.25)
        defaultCount = totalCount - shooterCount
    else:
        defaultCount = totalCount
        shooterCount = 0

    newDefaults = spawnWave(defaultCount, playerX, playerY)
    newShooters = enemyModule.spawnShooters(shooterCount, baseEnemySpeed, playerX, playerY) if shooterCount > 0 else []

    return newDefaults, newShooters

async def startGame(screen, color):
    clock = pygame.time.Clock()
    await loadDeathFrames(screen)

    pygame.mixer.music.load("Things/OST/waves1to10.ogg")
    pygame.mixer.music.play(-1)

    shootChannel = pygame.mixer.Channel(2)
    shootChannel.set_volume(0.6)

    wave = 1
    enemies = []
    enemySize = 75
    waveClearTimer = 0
    waitingForNextWave = False
    nextWaveDelay = 600

    enemySurface = createSquareSurface((220, 40, 40), enemySize)
    shooterSurface = enemyModule.createShooterSurface(enemyModule.shooterSize)
    shooters = []

    squareSize = 75
    squareSurface = createSquareSurface(color, squareSize)
    squareRect = squareSurface.get_rect(center = screen.get_rect().center)

    cameraX = 0
    cameraY = 0
    cameraSmooth = 0.12

    squareX = float(squareRect.centerx)
    squareY = float(squareRect.centery)

    dashing = False
    dashDuration = 180
    dashSpeed = 35
    dashStart = 0
    dashDirX = 0
    dashDirY = 0
    dashCooldown = 500
    lastDashTime = -dashCooldown

    afterimages = []

    health = 100
    maxHealth = 100
    font = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 28)

    fistSize = 35
    fistSurface = createSquareSurface(color, fistSize)

    fistSpawned = False
    fistX = squareX

    fistY = squareY
    fistLeash = 150

    punching = False
    punchStart = 0
    punchHitPlayed = False

    punchStartDistance = fistLeash
    punchOutDuration = 90
    punchBackDuration = 140
    punchExtraDistance = 120

    returning = False
    returnStart = 0
    returnDuration = 150
    returnStartX = fistX
    returnStartY = fistY

    punchDirX = 0
    punchDirY = 0
    punchCooldown = 1000

    lastPunchTime = -punchCooldown

    projectiles = []
    projectileSize = 12
    projectileSpeed = 14
    projectileCooldown = 100
    lastShotTime = -projectileCooldown

    shooterProjectiles = []

    fadeInDuration = 500
    fadeStart = pygame.time.get_ticks()
    alpha = 0

    while True:
        currentTime = pygame.time.get_ticks()
        elapsed = currentTime - fadeStart

        fadeT = min(elapsed / fadeInDuration, 1)
        fadeT = easeOut(fadeT)
        alpha = int(lerp(0, 255, fadeT))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if fistSpawned:
                        fistSpawned = False
                        punching = False
                    else:
                        fistSpawned = True
                        fistX = squareX
                        fistY = squareY

                if event.key == pygame.K_q and not dashing and currentTime - lastDashTime >= dashCooldown:
                    dx = 0
                    dy = 0
                    if keys[pygame.K_a]: dx -= 1
                    if keys[pygame.K_d]: dx += 1
                    if keys[pygame.K_w]: dy -= 1
                    if keys[pygame.K_s]: dy += 1

                    if dx != 0 or dy != 0:
                        length = math.sqrt(dx * dx + dy * dy)
                        dashDirX = dx / length
                        dashDirY = dy / length
                        dashing = True
                        dashStart = currentTime
                        lastDashTime = currentTime

                        dashSound = pygame.mixer.Sound("Things/SFX/dashSFX.wav")
                        dashSound.play()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if fistSpawned and not punching and currentTime - lastPunchTime >= punchCooldown:
                    mouseX, mouseY = pygame.mouse.get_pos()
                    mouseWorldX = mouseX + cameraX
                    mouseWorldY = mouseY + cameraY

                    dirX = mouseWorldX - squareX
                    dirY = mouseWorldY - squareY
                    dirLength = math.sqrt(dirX * dirX + dirY * dirY)

                    if dirLength == 0:
                        dirX, dirY = 0, -1
                    else:
                        dirX /= dirLength
                        dirY /= dirLength

                    punchDirX = dirX
                    punchDirY = dirY

                    currentOffsetX = fistX - squareX
                    currentOffsetY = fistY - squareY
                    punchStartDistance = math.sqrt(currentOffsetX * currentOffsetX + currentOffsetY * currentOffsetY)

                    punching = True
                    punchStart = currentTime
                    lastPunchTime = currentTime
                    punchHitPlayed = False

                    punchSound = pygame.mixer.Sound("Things/SFX/punchSwish.wav")
                    punchSound.play()

                elif not fistSpawned and currentTime - lastShotTime >= projectileCooldown:
                    mouseX, mouseY = pygame.mouse.get_pos()
                    
                    mouseWorldX = mouseX + cameraX
                    mouseWorldY= mouseY + cameraY

                    dirX = mouseWorldX - squareX
                    dirY = mouseWorldY - squareY
                    length = math.sqrt(dirX * dirX + dirY * dirY)

                    if length == 0:
                        dirX, dirY = 0, -1
                    else:
                        dirX /= length
                        dirY /= length

                    projectiles.append({
                        "x": squareX,
                        "y": squareY,
                        "dx": dirX * projectileSpeed,
                        "dy": dirY * projectileSpeed
                    })
                    lastShotTime = currentTime

                    shootSound = pygame.mixer.Sound("Things/SFX/Shoot.wav")
                    shootChannel.play(shootSound)

        keys = pygame.key.get_pressed()

        if dashing:
            squareX += dashDirX * dashSpeed
            squareY += dashDirY * dashSpeed

            afterimages.append({
                "x": squareX,
                "y": squareY,
                "alpha": 160
            })

            if currentTime - dashStart >= dashDuration:
                dashing = False
        else:
            dx = 0
            dy = 0

            if keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_d]: dx += 1
            if keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_s]: dy += 1

            if dx != 0 and dy != 0:
                length = math.sqrt(dx * dx + dy * dy)
                dx /= length
                dy /= length

            squareX += dx * moveSpeed
            squareY += dy * moveSpeed

        squareRect.center = (squareX, squareY)

        targetCamX = squareX - screen.get_width() // 2
        targetCamY = squareY - screen.get_height() // 2

        cameraX += (targetCamX - cameraX) * cameraSmooth
        cameraY += (targetCamY - cameraY) * cameraSmooth

        for e in enemies:
            dx = squareX - e["x"]
            dy = squareY - e["y"]

            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                e["x"] += (dx / dist) * e["speed"]
                e["y"] += (dy / dist) * e["speed"]

        for s in shooters:
            enemyModule.updateShooterMovement(s, squareX, squareY, enemies, shooters)
            newPellet = enemyModule.tryShooterShoot(s, currentTime, squareX, squareY)
            
            if newPellet:
                shooterProjectiles.append(newPellet)

        for e in enemies:
            if abs(e["x"] - squareX) < (enemySize + squareSize) / 2 and \
            abs(e["y"] - squareY) < (enemySize + squareSize) / 2:
                
                if currentTime - e["last_hit"] >= 2000:
                    health -= 20
                    e["last_hit"] = currentTime

                    if health <= 0:
                        health = 0
                        pygame.mixer.music.stop()
                        deathStart = pygame.time.get_ticks()

                        while pygame.time.get_ticks() - deathStart < 250:
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()

                            pygame.display.update()
                            await asyncio.sleep(0)
                        await die(screen, color)
                        return

        if punching:
            for e in (enemies + shooters)[:]:
                if abs(fistX - e["x"]) < (fistSize + enemySize) / 2 and \
                abs(fistY - e["y"]) < (fistSize + enemySize) / 2:
                    e["hp"] -= 10

                    if not punchHitPlayed:
                        punchHitSound = pygame.mixer.Sound("Things/SFX/punchHit.wav")
                        punchHitSound.play()
                        punchHitPlayed = True

                    if e["hp"] <= 0:
                        if e in enemies:
                            enemies.remove(e)
                        if e in shooters:
                            shooters.remove(e)

            punchElapsed = currentTime - punchStart

            if punchElapsed <= punchOutDuration:
                punchT = punchElapsed / punchOutDuration
                punchDistance = lerp(punchStartDistance, punchStartDistance + punchExtraDistance, punchT)
            elif punchElapsed <= punchOutDuration + punchBackDuration:
                punchT = (punchElapsed - punchOutDuration) / punchBackDuration
                punchT = easeOut(punchT)
                punchDistance = lerp(punchStartDistance + punchExtraDistance, fistLeash, punchT)
            else:
                punching = False
                returning = True
                returnStart = currentTime
                returnStartX = fistX
                returnStartY = fistY
                punchDistance = fistLeash

            fistX = squareX + punchDirX * punchDistance
            fistY = squareY + punchDirY * punchDistance

        elif returning:
            mouseX, mouseY = pygame.mouse.get_pos()
            mouseWorldX = mouseX + cameraX
            mouseWorldY = mouseY + cameraY

            offsetX = mouseWorldX - squareX
            offsetY = mouseWorldY - squareY
            distance = math.sqrt(offsetX * offsetX + offsetY * offsetY)

            if distance > fistLeash:
                scale = fistLeash / distance
                offsetX *= scale
                offsetY *= scale

            targetX = squareX + offsetX
            targetY = squareY + offsetY

            returnElapsed = currentTime - returnStart
            returnT = min(returnElapsed / returnDuration, 1)
            returnT = easeOut(returnT)

            fistX = lerp(returnStartX, targetX, returnT)
            fistY = lerp(returnStartY, targetY, returnT)

            if returnT >= 1:
                returning = False

        elif fistSpawned:
            mouseX, mouseY = pygame.mouse.get_pos()
            mouseWorldX = mouseX + cameraX
            mouseWorldY = mouseY + cameraY

            offsetX = mouseWorldX - squareX
            offsetY = mouseWorldY - squareY
            distance = math.sqrt(offsetX * offsetX + offsetY * offsetY)

            if distance > fistLeash:
                scale = fistLeash / distance
                offsetX *= scale
                offsetY *= scale

            fistX = squareX + offsetX
            fistY = squareY + offsetY

        for p in projectiles[:]:
            p["x"] += p["dx"]
            p["y"] += p["dy"]

            dist = math.sqrt((p["x"] - squareX) ** 2 + (p["y"] - squareY) ** 2)
            if dist > 2000:
                projectiles.remove(p)
                continue

            for e in (enemies + shooters)[:]:
                if abs(p["x"] - e["x"]) < (projectileSize + enemySize) / 2 and \
                abs(p["y"] - e["y"]) < (projectileSize + enemySize) / 2:
                    
                    e["hp"] -= 5
                    if p in projectiles:
                        projectiles.remove(p)
                    if e["hp"] <= 0:
                        if e in enemies:
                            enemies.remove(e)
                        if e in shooters:
                            shooters.remove(e)
                    break

        for sp in shooterProjectiles[:]:
            sp["x"] += sp["dx"]
            sp["y"] += sp["dy"]

            dist = math.sqrt((sp["x"] - squareX) ** 2 + (sp["y"] - squareY) ** 2)
            if dist > 2000:
                shooterProjectiles.remove(sp)
                continue

            if abs(sp["x"] - squareX) < (enemyModule.shooterProjectileSize + squareSize) / 2 and \
            abs(sp["y"] - squareY) < (enemyModule.shooterProjectileSize + squareSize) / 2:
                health -= 10
                shooterProjectiles.remove(sp)

                if health <= 0:
                    health = 0
                    pygame.mixer.music.stop()
                    deathStart = pygame.time.get_ticks()

                    while pygame.time.get_ticks() - deathStart < 250:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()

                        pygame.display.update()
                        await asyncio.sleep(0)
                    await die(screen, color)
                    return

        if wave == 1 and not enemies and not shooters and not waitingForNextWave and currentTime - fadeStart > 800 and currentTime - fadeStart < 2000:
            enemies, shooters = spawnWaveEnemies(wave, squareX, squareY)

        if not enemies and not shooters and not waitingForNextWave and wave >= 1 and currentTime - fadeStart > 2000:
            waitingForNextWave = True
            waveClearTimer = currentTime

        if waitingForNextWave and currentTime - waveClearTimer >= nextWaveDelay:
            if wave % 5 == 0:
                health = maxHealth

            wave += 1
            enemies, shooters = spawnWaveEnemies(wave, squareX, squareY)
            waitingForNextWave = False

            if wave == 11:
                pygame.mixer.music.stop()

        screen.fill((20, 20, 20))
        for img in afterimages[:]:
            img["alpha"] -= 12
            if img["alpha"] <= 0:
                afterimages.remove(img)

        for img in afterimages:
            temp = squareSurface.copy()
            temp.set_alpha(img["alpha"])
            rect = temp.get_rect(center=(img["x"] - cameraX, img["y"] - cameraY))
            screen.blit(temp, rect)

        tempSquare = squareSurface.copy()
        tempSquare.set_alpha(alpha)
        screen.blit(tempSquare, (squareRect.x - cameraX, squareRect.y - cameraY))

        for p in projectiles:
            pygame.draw.rect(screen, (255, 255, 255), 
                            (p["x"] - cameraX - projectileSize // 2, 
                            p["y"] - cameraY - projectileSize // 2, 
                            projectileSize, projectileSize))

        for sp in shooterProjectiles:
            pygame.draw.rect(screen, (255, 140, 0), 
                            (sp["x"] - cameraX - enemyModule.shooterProjectileSize // 2, 
                            sp["y"] - cameraY - enemyModule.shooterProjectileSize // 2, 
                            enemyModule.shooterProjectileSize, enemyModule.shooterProjectileSize))

        if fistSpawned:
            tempFist = fistSurface.copy()
            tempFist.set_alpha(alpha)
            fistRect = tempFist.get_rect(center=(fistX - cameraX, fistY - cameraY))
            screen.blit(tempFist, fistRect)

        for e in enemies:
            rect = enemySurface.get_rect(center = (e["x"] - cameraX, e["y"] - cameraY))
            screen.blit(enemySurface, rect)

        for s in shooters:
            rect = shooterSurface.get_rect(center = (s["x"] - cameraX, s["y"] - cameraY))
            screen.blit(shooterSurface, rect)

        healthText = font.render(f"Health: {health}", True, (255, 255, 255))
        screen.blit(healthText, (20, 20))

        enemiesLeftText = font.render(f"Enemies Left: {len(enemies) + len(shooters)}", True, (255, 255, 255))
        screen.blit(enemiesLeftText, (20 + healthText.get_width() + 30, 20))

        waveText = font.render(f"Wave: {wave}", True, (255, 255, 255))
        screen.blit(waveText, (20, 55))

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)