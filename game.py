import pygame
import sys
import random
import asyncio
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

def die(screen):
    videoPath = "Things/Videos/无信号.mp4"
    musicPath = "Things/OST/无信号.ogg"

    try:
        pygame.mixer.music.load(musicPath)
        pygame.mixer.music.play(-1)
    except:
        pass

    try:
        import cv2
        cap = cv2.VideoCapture(videoPath)

        clock = pygame.time.Clock()
        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop video
                continue

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (screen.get_width(), screen.get_height()))
            frameSurface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

            screen.blit(frameSurface, (0, 0))
            pygame.display.update()
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
    except:
        font = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 50)

        while True:
            screen.fill((0, 0, 0))
            text = font.render("YOU DIED", True, (255, 0, 0))
            screen.blit(text, text.get_rect(center=screen.get_rect().center))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

def spawnWave(waveNum, playerX, playerY):
    count = 5
    for _ in range(waveNum - 1):
        count = math.ceil(count * 1.05)

    maxHP = 10 + (waveNum // 5)
    speed = baseEnemySpeed * (1 + 0.0005 * (waveNum - 1))

    newEnemies = []
    for i in range(count):
        if i % 3 == 0:
            dist = random.randint(250, 400)
        else:
            dist = random.randint(550, 900)

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

async def startGame(screen, color):
    clock = pygame.time.Clock()

    wave = 1
    enemies = []
    enemySize = 75
    waveClearTimer = 0
    waitingForNextWave = False
    nextWaveDelay = 600

    enemySurface = createSquareSurface((220, 40, 40), enemySize)

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

        for e in enemies:
            if abs(e["x"] - squareX) < (enemySize + squareSize) / 2 and \
            abs(e["y"] - squareY) < (enemySize + squareSize) / 2:
                
                if currentTime - e["last_hit"] >= 2000:
                    health -= 20
                    e["last_hit"] = currentTime

                    if health <= 0:
                        health = 0
                        deathStart = pygame.time.get_ticks()

                        while pygame.time.get_ticks() - deathStart < 250:
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()

                            pygame.display.update()
                        die(screen)

        if punching:
            for e in enemies[:]:
                if abs(fistX - e["x"]) < (fistSize + enemySize) / 2 and \
                abs(fistY - e["y"]) < (fistSize + enemySize) / 2:
                    e["hp"] -= 10
                    if e["hp"] <= 0 and e in enemies:
                        enemies.remove(e)
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

            for e in enemies[:]:
                if abs(p["x"] - e["x"]) < (projectileSize + enemySize) / 2 and \
                abs(p["y"] - e["y"]) < (projectileSize + enemySize) / 2:
                    
                    e["hp"] -= 5
                    if p in projectiles:
                        projectiles.remove(p)
                    if e["hp"] <= 0 and e in enemies:
                        enemies.remove(e)
                    break

        if wave == 1 and not enemies and not waitingForNextWave and currentTime - fadeStart > 800 and currentTime - fadeStart < 2000:
            enemies = spawnWave(1, squareX, squareY)

        if not enemies and not waitingForNextWave and wave >= 1 and currentTime - fadeStart > 2000:
            waitingForNextWave = True
            waveClearTimer = currentTime

        if waitingForNextWave and currentTime - waveClearTimer >= nextWaveDelay:
            wave += 1
            enemies = spawnWave(wave, squareX, squareY)
            waitingForNextWave = False

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

        if fistSpawned:
            tempFist = fistSurface.copy()
            tempFist.set_alpha(alpha)
            fistRect = tempFist.get_rect(center=(fistX - cameraX, fistY - cameraY))
            screen.blit(tempFist, fistRect)

        for e in enemies:
            rect = enemySurface.get_rect(center = (e["x"] - cameraX, e["y"] - cameraY))
            screen.blit(enemySurface, rect)

        healthText = font.render(f"Health: {health}", True, (255, 255, 255))
        screen.blit(healthText, (20, 20))

        waveText = font.render(f"Wave: {wave}", True, (255, 255, 255))
        screen.blit(waveText, (20, 55))

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)