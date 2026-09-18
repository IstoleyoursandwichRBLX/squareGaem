import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame
import game
import asyncio
import sys

pygame.init()
screen = pygame.display.set_mode((1920, 980))
pygame.display.set_caption("Square Game")

pygame.mixer.init()

secondMusic = pygame.mixer.Sound("Things/OST/changeColorTheme.ogg")
secondChannel = pygame.mixer.Channel(1)
secondChannel.set_volume(0.0)

clock = pygame.time.Clock()
mainFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 50)
smallFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 28)
mainText = mainFont.render("Square Game", False, "White")

textTarget = (670, 200)
buttonTarget = pygame.Rect(740, 500, 400, 120)

buttonColor = (50, 50, 50)
buttonHover = (80, 80, 80)
textColor = (255, 255, 255)

def isWeb():
    return sys.platform == "emscripten"

def saveColor(color):
    if isWeb():
        try:
            import platform
            platform.window.localStorage.setItem("color_save", f"{color[0]},{color[1]},{color[2]}")
        except:
            pass
    else:
        with open("Things/Data/color_save.txt", "w") as f:
            f.write(f"{color[0]},{color[1]},{color[2]}")

def loadColor():
    if isWeb():
        try:
            import platform
            value = platform.window.localStorage.getItem("color_save")
            if value:
                parts = value.split(",")
                return (int(parts[0]), int(parts[1]), int(parts[2]))
        except:
            pass
        return (30, 100, 180)
    else:
        try:
            with open("Things/Data/color_save.txt", "r") as f:
                parts = f.read().strip().split(",")
                return (int(parts[0]), int(parts[1]), int(parts[2]))
        except:
            return (30, 100, 180)

you = loadColor()

def makeButton(surface, rect, text, mousePos, scale, alpha = 255):
    if rect.collidepoint(mousePos):
        color = buttonHover
    else:
        color = buttonColor

    buttonSurface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(buttonSurface, (*color, alpha), (0, 0, rect.width, rect.height))
    pygame.draw.rect(buttonSurface, (255, 255, 255, alpha), (0, 0, rect.width, rect.height), width = 3)

    textSurface = mainFont.render(text, False, textColor)
    scaledText = pygame.transform.scale(
        textSurface,
        (int(textSurface.get_width() * scale), int(textSurface.get_height() * scale))
    )

    scaledText.set_alpha(alpha)
    textBase = scaledText.get_rect(center = (rect.width // 2, rect.height // 2))
    buttonSurface.blit(scaledText, textBase)

    surface.blit(buttonSurface, rect.topleft)

def createSquareSurface(color, size):
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(surface, color, (0, 0, size, size))
    pygame.draw.rect(surface, (255, 255, 255), (0, 0, size, size), width = 6)
    return surface

def lerp(start, end, t):
    return start + (end - start) * t

def easeOut(t):
    return 1 - (1 - t) * (1 - t)

def startMenuMusic():
    pygame.mixer.music.load("Things/OST/mainMenu.ogg")
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(1.0)

def tryParseRGB(text):
    try:
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 3:
            return None
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
            return (r, g, b)
    except:
        pass
    return None

async def checkPassword():
    correctPassword = "squaregamea"
    inputText = ""
    errorMessage = ""

    inputRect = pygame.Rect(710, 460, 500, 60)
    cursorTimer = 0
    showCursor = True

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    inputText = inputText[:-1]
                    errorMessage = ""
                elif event.key == pygame.K_RETURN:
                    if inputText == correctPassword:
                        return
                    else:
                        errorMessage = "Incorrect password"
                        inputText = ""
                else:
                    if event.unicode.isprintable() and len(inputText) < 30:
                        inputText += event.unicode
                        errorMessage = ""

        cursorTimer += 1

        if cursorTimer >= 30:
            cursorTimer = 0
            showCursor = not showCursor

        screen.fill((20, 20, 20))

        boxSurf = pygame.Surface((inputRect.width, inputRect.height), pygame.SRCALPHA)
        pygame.draw.rect(boxSurf, (0, 0, 0, 255), (0, 0, inputRect.width, inputRect.height))
        pygame.draw.rect(boxSurf, (255, 255, 255, 255), (0, 0, inputRect.width, inputRect.height), width=3)
        screen.blit(boxSurf, inputRect.topleft)

        displayText = inputText if inputText else "Enter Password"
        color = (200, 200, 200) if inputText else (120, 120, 120)

        textSurface = smallFont.render(displayText, True, color)
        screen.blit(textSurface, (inputRect.x + 15, inputRect.y + 15))

        if showCursor and inputText:
            cursorX = inputRect.x + 15 + textSurface.get_width() + 2
            cursorSurf = pygame.Surface((3, 30))
            cursorSurf.fill((255, 255, 255))
            screen.blit(cursorSurf, (cursorX, inputRect.y + 15))

        if errorMessage:
            errSurface = smallFont.render(errorMessage, True, (255, 80, 80))
            errRect = errSurface.get_rect(center=(inputRect.centerx, inputRect.y - 40))
            screen.blit(errSurface, errRect)

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

async def menuMain():
    global you

    await checkPassword()
    startMenuMusic()

    duration = 1000
    start = pygame.time.get_ticks()

    textY = -100
    buttonX = -450

    currentScale = 1.0
    targetScale = 1.0
    scaleSpeed = 0.18

    angle = 0
    squareSize = 220
    squareSurface = createSquareSurface(you, squareSize)
    rotatedCache = {}

    squareRightX = 1600 + squareSize // 2
    squareLeftX = 50 + squareSize // 2
    squareX = squareRightX

    isOnLeft = False
    transitioning = False
    goingLeft = False
    transitionStart = 0
    transitionDuration = 800

    uiAlpha = 255
    volume = 1.0
    secondVolume = 0.0
    secondMusicStarted = False

    inputActive = False
    inputText = ""
    inputRect = pygame.Rect(710, 460, 500, 60)
    inputAlpha = 0
    cursorTimer = 0
    showCursor = True

    startingGame = False
    startFade = 0
    startDuration = 800
    squareAlpha = 255

    controlsFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 18)
    controlsLines = [
        "WASD - Moving",
        "E - Toggle Fists",
        "M1 - Shooting/Punching",
        "Q + W/A/S/D - Dash"
    ]
    controlsLineSurfaces = [controlsFont.render(line, True, textColor) for line in controlsLines]

    while True:
        mousePos = pygame.mouse.get_pos()
        currentTime = pygame.time.get_ticks()
        elapsed = currentTime - start

        t = min(elapsed / duration, 1)
        t = easeOut(t)

        texty = lerp(textY, textTarget[1], t)
        buttonx = lerp(buttonX, buttonTarget.x, t)

        currentButton = buttonTarget.copy()
        currentButton.x = buttonx

        hovering = currentButton.collidepoint(mousePos) and t >= 1
        targetScale = 1.15 if hovering else 1.0

        currentScale += (targetScale - currentScale) * scaleSpeed

        scaledWidth = int(buttonTarget.width * currentScale)
        scaledheight = int(buttonTarget.height * currentScale)
        scaledButton = pygame.Rect(0, 0, scaledWidth, scaledheight)
        scaledButton.center = currentButton.center

        angle += 2
        if angle >= 360:
            angle = 0

        if transitioning:
            transElapsed = currentTime - transitionStart
            transT = min(transElapsed / transitionDuration, 1)
            transT = easeOut(transT)

            if goingLeft:
                squareX = lerp(squareRightX, squareLeftX, transT)
                uiAlpha = int(lerp(255, 0, transT))
                volume = lerp(1.0, 0.0, transT)
                secondVolume = lerp(0.0, 1.0, transT)
                inputAlpha = int(lerp(0, 255, transT))
            else:
                squareX = lerp(squareLeftX, squareRightX, transT)
                uiAlpha = int(lerp(0, 255, transT))
                volume = lerp(0.0, 1.0, transT)
                secondVolume = lerp(1.0, 0.0, transT)
                inputAlpha = int(lerp(255, 0, transT))

            pygame.mixer.music.set_volume(volume)
            secondChannel.set_volume(secondVolume)

            if transT >= 1:
                transitioning = False
                isOnLeft = goingLeft

                if isOnLeft:
                    pygame.mixer.music.pause()
                    inputActive = True
                else:
                    inputActive = False
                    inputText = ""
                    secondChannel.pause()

        if startingGame:
            fadeElapsed = currentTime - startFade
            fadeT = min(fadeElapsed / startDuration, 1)
            fadeT = easeOut(fadeT)

            uiAlpha = int(lerp(255, 0, fadeT))
            squareAlpha = int(lerp(255, 0, fadeT))

            if fadeT >= 1:
                await game.startGame(screen, you)
                return

        cursorTimer += 1
        if cursorTimer >= 30:
            cursorTimer = 0
            showCursor = not showCursor

        if angle not in rotatedCache:
            rotatedCache[angle] = pygame.transform.rotate(squareSurface, -angle)

        rotatedSquare = rotatedCache[angle]
        rotatedRect = rotatedSquare.get_rect(center=(squareX, 400 + squareSize // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if scaledButton.collidepoint(mousePos) and t >= 1 and not transitioning and not startingGame and not isOnLeft:
                    pygame.mixer.music.stop()
                    startingGame = True
                    startFade = currentTime

                if rotatedRect.collidepoint(mousePos) and t >= 1 and not transitioning:
                    transitioning = True
                    transitionStart = currentTime
                    goingLeft = not isOnLeft

                    if not goingLeft:
                        pygame.mixer.music.unpause()
                        secondChannel.unpause()
                    else:
                        if not secondMusicStarted:
                            secondChannel.play(secondMusic, loops = -1)
                            secondChannel.set_volume(0.0)
                            secondMusicStarted = True
                        else:
                            secondChannel.unpause()

            if event.type == pygame.KEYDOWN and inputActive and isOnLeft and not transitioning:
                if event.key == pygame.K_BACKSPACE:
                    inputText = inputText[:-1]
                elif event.key == pygame.K_RETURN:
                    pass
                else:
                    if event.unicode.isprintable() and len(inputText) < 20:
                        inputText += event.unicode

                newColor = tryParseRGB(inputText)
                if newColor:
                    you = newColor
                    squareSurface = createSquareSurface(you, squareSize)
                    rotatedCache.clear()

                    saveColor(you)

                if rotatedRect.collidepoint(mousePos) and t >= 1 and not transitioning:
                    transitioning = True
                    transitionStart = currentTime
                    goingLeft = not isOnLeft

                    if not goingLeft:
                        pygame.mixer.music.unpause()

        screen.fill((20, 20, 20))

        tempSquare = rotatedSquare.copy()
        tempSquare.set_alpha(squareAlpha)
        screen.blit(tempSquare, rotatedRect)
        titleSurface = mainText.copy()

        titleSurface.set_alpha(uiAlpha)
        screen.blit(titleSurface, (textTarget[0], texty))

        if uiAlpha > 0:
            makeButton(screen, scaledButton, "Play", mousePos, currentScale, uiAlpha)

        if uiAlpha > 0:
            lineSpacing = 26
            startY = screen.get_height() - (len(controlsLineSurfaces) * lineSpacing) - 20

            for i, lineSurface in enumerate(controlsLineSurfaces):
                lineSurface.set_alpha(uiAlpha)
                screen.blit(lineSurface, (20, startY + i * lineSpacing))

        if inputAlpha > 0:
            boxSurf = pygame.Surface((inputRect.width, inputRect.height), pygame.SRCALPHA)
            
            pygame.draw.rect(boxSurf, (0, 0, 0, inputAlpha), (0, 0, inputRect.width, inputRect.height))
            pygame.draw.rect(boxSurf, (255, 255, 255, inputAlpha), (0, 0, inputRect.width, inputRect.height), width = 3)

            screen.blit(boxSurf, inputRect.topleft)

            displayText = inputText if inputText else "Insert RGB Color"
            color = (200, 200, 200) if inputText else (120, 120, 120)

            textSurface = smallFont.render(displayText, True, color)
            textSurface.set_alpha(inputAlpha)

            screen.blit(textSurface, (inputRect.x + 15, inputRect.y + 15))

            if inputActive and showCursor and inputText:
                cursorX = inputRect.x + 15 + textSurface.get_width() + 2
                cursorSurf = pygame.Surface((3, 30), pygame.SRCALPHA)

                cursorSurf.fill((255, 255, 255, inputAlpha))
                screen.blit(cursorSurf, (cursorX, inputRect.y + 15))
        
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)