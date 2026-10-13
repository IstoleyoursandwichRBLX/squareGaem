import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame
import game
import asyncio
import sys

import hashlib
import json
import cloud

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
enemyIndexButtonFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 24)
mainText = mainFont.render("Square Game", False, "White")

textTarget = (670, 200)
buttonTarget = pygame.Rect(740, 500, 400, 120)
settingsButtonTarget = pygame.Rect(740, 650, 400, 120)

buttonColor = (50, 50, 50)
buttonHover = (80, 80, 80)
textColor = (255, 255, 255)

def isWeb():
    return sys.platform == "emscripten"

def colorKeyFor(name):
    return f"squareGameColor_{name.lower()}"

def saveColor(name, color):
    cloud.put(colorKeyFor(name), [color[0], color[1], color[2]])

def loadColor(name):
    value = cloud.get(colorKeyFor(name), None)
    try:
        return (int(value[0]), int(value[1]), int(value[2]))
    except:
        return (30, 100, 180)

you = (30, 100, 180)

def makeButton(surface, rect, text, mousePos, scale, alpha = 255, font = mainFont):
    if rect.collidepoint(mousePos):
        color = buttonHover
    else:
        color = buttonColor

    buttonSurface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(buttonSurface, (*color, alpha), (0, 0, rect.width, rect.height))
    pygame.draw.rect(
        buttonSurface,
        (255, 255, 255, alpha),
        (0, 0, rect.width, rect.height),
        width = 3
    )

    textSurface = font.render(text, False, textColor)
    scaledText = pygame.transform.scale(
        textSurface,
        (
            int(textSurface.get_width() * scale),
            int(textSurface.get_height() * scale)
        )
    )

    scaledText.set_alpha(alpha)
    textBase = scaledText.get_rect(center=(rect.width // 2, rect.height // 2))
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

ACCOUNTSPATH = "Things/Data/accounts.json"
ACCOUNTSKEY = "square_game_accounts"
USERNAMEMAX = 20
PASSWORDMAX = 20

def loadAccounts():
    return cloud.get(ACCOUNTSKEY, {})

def saveAccounts(accs):
    cloud.put(ACCOUNTSKEY, accs)

def hashPassword(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def passwordProblem(password):
    if len(password) < 8:
        return "Password needs 8+ characters"
    if not any(c.islower() for c in password):
        return "Needs a lowercase letter"
    if not any(c.isupper() for c in password):
        return "Needs an uppercase letter"
    if not any(c.isdigit() for c in password):
        return "Needs a number"
    if not any(not c.isalnum() and not c.isspace() for c in password):
        return "Needs a special character"
    return ""

def checkNewAccount(username, password):
    if len(username) < 3:
        return "Username needs 3+ characters"
    return passwordProblem(password)

LASTUSERPATH = "Things/Data/lastUser.txt"
LASTUSERKEY = "squareGameLastUser"

def loadLastUser():
    if isWeb():
        try:
            import platform
            return platform.window.localStorage.getItem(LASTUSERKEY) or ""
        except:
            return ""

    try:
        with open(LASTUSERPATH, "r") as f:
            return f.read().strip()
    except:
        return ""

def saveLastUser(username):
    if isWeb():
        try:
            import platform
            platform.window.localStorage.setItem(LASTUSERKEY, username)
        except:
            pass
    else:
        try:
            with open(LASTUSERPATH, "w") as f:
                f.write(username)
        except:
            pass

async def accountScreen():
    accounts = loadAccounts()
    await cloud.pull(ACCOUNTSKEY, {})
    
    signingUp = len(accounts) == 0

    usernameRect = pygame.Rect(610, 380, 700, 60)
    passwordRect = pygame.Rect(610, 480, 700, 60)
    buttonRect = pygame.Rect(610, 590, 700, 90)
    switchRect = pygame.Rect(610, 780, 700, 70)

    username = ""
    password = ""
    focus = 0
    errorMessage = ""
    cursorTimer = 0
    showCursor = True

    while True:
        mousePos = pygame.mouse.get_pos()
        submit = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if usernameRect.collidepoint(event.pos):
                    focus = 0
                elif passwordRect.collidepoint(event.pos):
                    focus = 1
                elif buttonRect.collidepoint(event.pos):
                    submit = True
                elif switchRect.collidepoint(event.pos):
                    signingUp = not signingUp
                    errorMessage = ""
                    password = ""

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    focus = 1 - focus
                elif event.key == pygame.K_RETURN:
                    if focus == 0:
                        focus = 1
                    else:
                        submit = True
                elif event.key == pygame.K_BACKSPACE:
                    if focus == 0:
                        username = username[:-1]
                    else:
                        password = password[:-1]
                    errorMessage = ""
                elif event.unicode and event.unicode.isprintable():
                    if focus == 0:
                        ch = event.unicode
                        if ch.isascii() and (ch.isalnum() or ch == "_") and len(username) < USERNAMEMAX:
                            username += ch
                    elif len(password) < PASSWORDMAX:
                        password += event.unicode
                    errorMessage = ""

        if submit:
            key = username.lower()

            if signingUp:
                errorMessage = checkNewAccount(username, password)

                if not errorMessage and key in accounts:
                    errorMessage = "Username already taken"

                if not errorMessage:
                    salt = os.urandom(8).hex()
                    accounts[key] = {
                        "username": username,
                        "salt": salt,
                        "hash": hashPassword(password, salt)
                    }
                    saveAccounts(accounts)
                    return username
            else:
                account = accounts.get(key)

                if account and account["hash"] == hashPassword(password, account["salt"]):
                    return account["username"]

                errorMessage = "Incorrect username or password"
                password = ""

        cursorTimer += 1
        if cursorTimer >= 30:
            cursorTimer = 0
            showCursor = not showCursor

        screen.fill((20, 20, 20))

        title = mainFont.render("Sign Up" if signingUp else "Log In", False, "White")
        screen.blit(title, title.get_rect(center = (screen.get_width() // 2, 250)))

        fields = ((usernameRect, username, "Username", 0), (passwordRect, "*" * len(password), "Password", 1))

        for rect, text, placeholder, index in fields:
            pygame.draw.rect(screen, (0, 0, 0), rect)
            pygame.draw.rect(screen, (122, 190, 255) if focus == index else (255, 255, 255), rect, width = 3)

            textSurface = smallFont.render(text if text else placeholder, True, (200, 200, 200) if text else (120, 120, 120))
            screen.blit(textSurface, (rect.x + 15, rect.y + 15))

            if focus == index and showCursor:
                cursorX = rect.x + 15 + (textSurface.get_width() + 2 if text else 0)
                pygame.draw.rect(screen, (255, 255, 255), (cursorX, rect.y + 15, 3, 30))

        makeButton(screen, buttonRect, "Sign Up" if signingUp else "Log In", mousePos, 1.0, 255, smallFont)
        makeButton(screen, switchRect, "Switch to Log In" if signingUp else "Switch to Sign Up", mousePos, 1.0, 255, smallFont)

        if errorMessage:
            errSurface = smallFont.render(errorMessage, True, (255, 80, 80))
            screen.blit(errSurface, errSurface.get_rect(center = (screen.get_width() // 2, 735)))

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

DELETESTEPS = 5

def userKeys(name):
    return [f"squareGameSave_{name.lower()}", colorKeyFor(name)]

async def loadUserData(name):
    for key in userKeys(name):
        await cloud.pull(key, None)
    return loadColor(name)

def moveUserData(oldName, newName):
    for oldKey, newKey in zip(userKeys(oldName), userKeys(newName)):
        value = cloud.get(oldKey, None)
        if value is not None:
            cloud.put(newKey, value)
        cloud.remove(oldKey)

def deleteUserData(name):
    for key in userKeys(name):
        cloud.remove(key)

def verifyPassword(username, password):
    account = loadAccounts().get(username.lower())
    return bool(account) and account["hash"] == hashPassword(password, account["salt"])

def renameAccount(oldName, newName):
    if len(newName) < 3:
        return "Username needs 3+ characters"

    if newName == oldName:
        return "That is already your username"

    accounts = loadAccounts()
    oldKey = oldName.lower()
    newKey = newName.lower()

    if oldKey not in accounts:
        return "Account not found"

    if newKey != oldKey and newKey in accounts:
        return "Username already taken"

    account = accounts.pop(oldKey)
    account["username"] = newName
    accounts[newKey] = account
    saveAccounts(accounts)

    if newKey != oldKey:
        moveUserData(oldName, newName)

    saveLastUser(newName)
    return ""

def changePassword(username, oldPassword, newPassword, confirmPassword):
    accounts = loadAccounts()
    account = accounts.get(username.lower())

    if not account:
        return "Account not found"

    if account["hash"] != hashPassword(oldPassword, account["salt"]):
        return "Old password is incorrect"

    problem = passwordProblem(newPassword)

    if problem:
        return problem

    if newPassword != confirmPassword:
        return "New passwords do not match"

    if newPassword == oldPassword:
        return "New password must be different"

    salt = os.urandom(8).hex()
    account["salt"] = salt
    account["hash"] = hashPassword(newPassword, salt)
    saveAccounts(accounts)
    return ""

def deleteAccount(username):
    accounts = loadAccounts()
    accounts.pop(username.lower(), None)

    saveAccounts(accounts)
    deleteUserData(username)
    saveLastUser("")

def drawInputField(surface, rect, text, placeholder, focused, showCursor, font):
    pygame.draw.rect(surface, (0, 0, 0), rect)
    pygame.draw.rect(surface, (122, 190, 255) if focused else (255, 255, 255), rect, width = 3)

    textSurface = font.render(text if text else placeholder, True, (200, 200, 200) if text else (120, 120, 120))
    surface.blit(textSurface, (rect.x + 15, rect.y + 15))

    if focused and showCursor:
        cursorX = rect.x + 15 + (textSurface.get_width() + 2 if text else 0)
        pygame.draw.rect(surface, (255, 255, 255), (cursorX, rect.y + 15, 3, 30))

def drawColorButton(surface, rect, text, mousePos, normalColor, hoverColor, font):
    pygame.draw.rect(surface, hoverColor if rect.collidepoint(mousePos) else normalColor, rect)
    pygame.draw.rect(surface, textColor, rect, width = 3)

    label = font.render(text, False, textColor)
    surface.blit(label, label.get_rect(center = rect.center))

async def profileScreen(currentName):
    labelFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 20)
    red = (255, 80, 80)
    green = (120, 220, 120)
    dimText = (180, 180, 200)

    closeRect = pygame.Rect(1770, 40, 105, 75)

    usernameRect = pygame.Rect(240, 260, 640, 60)
    usernameSaveRect = pygame.Rect(240, 350, 640, 80)
    logoutRect = pygame.Rect(240, 500, 640, 80)

    oldRect = pygame.Rect(1040, 260, 640, 60)
    newRect = pygame.Rect(1040, 350, 640, 60)
    confirmRect = pygame.Rect(1040, 440, 640, 60)
    passwordSaveRect = pygame.Rect(1040, 530, 640, 80)

    deleteRect = pygame.Rect(240, 700, 640, 80)
    yesRect = pygame.Rect(240, 840, 300, 70)
    noRect = pygame.Rect(580, 840, 300, 70)
    deletePasswordRect = pygame.Rect(240, 840, 640, 60)

    name = currentName
    values = [currentName, "", "", "", ""]
    focus = 0

    usernameMessage = None
    passwordMessage = None
    deleteError = ""

    deleteStage = 0
    deleteRound = 0

    cursorTimer = 0
    showCursor = True

    while True:
        mousePos = pygame.mouse.get_pos()
        saveUsername = False
        savePassword = False
        submitDelete = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if closeRect.collidepoint(event.pos):
                    return name

                if usernameRect.collidepoint(event.pos):
                    focus = 0
                elif oldRect.collidepoint(event.pos):
                    focus = 1
                elif newRect.collidepoint(event.pos):
                    focus = 2
                elif confirmRect.collidepoint(event.pos):
                    focus = 3
                elif deleteStage == 2 and deletePasswordRect.collidepoint(event.pos):
                    focus = 4
                elif usernameSaveRect.collidepoint(event.pos):
                    saveUsername = True
                elif passwordSaveRect.collidepoint(event.pos):
                    savePassword = True
                elif logoutRect.collidepoint(event.pos):
                    saveLastUser("")
                    return None
                elif deleteRect.collidepoint(event.pos):
                    if deleteStage == 0:
                        deleteStage = 1
                        deleteRound = 0
                        deleteError = ""
                elif deleteRect.collidepoint(event.pos):
                    if deleteStage == 0:
                        deleteStage = 1
                        deleteRound = 0
                        deleteError = ""
                elif deleteStage == 1 and yesRect.collidepoint(event.pos):
                    deleteStage = 2
                    values[4] = ""
                    deleteError = ""
                    focus = 4
                elif deleteStage == 1 and noRect.collidepoint(event.pos):
                    deleteStage = 0
                    deleteRound = 0
                    values[4] = ""
                    deleteError = ""

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return name

                elif event.key == pygame.K_TAB:
                    order = [0, 1, 2, 3, 4] if deleteStage == 2 else [0, 1, 2, 3]
                    focus = order[(order.index(focus) + 1) % len(order)] if focus in order else 0

                elif event.key == pygame.K_RETURN:
                    if focus == 0:
                        saveUsername = True
                    elif focus == 1 or focus == 2:
                        focus += 1
                    elif focus == 3:
                        savePassword = True
                    elif focus == 4:
                        submitDelete = True

                elif event.key == pygame.K_BACKSPACE or (event.unicode and event.unicode.isprintable()):
                    if event.key == pygame.K_BACKSPACE:
                        values[focus] = values[focus][:-1]
                    else:
                        ch = event.unicode

                        if focus == 0:
                            if ch.isascii() and (ch.isalnum() or ch == "_") and len(values[0]) < USERNAMEMAX:
                                values[0] += ch
                        elif len(values[focus]) < PASSWORDMAX:
                            values[focus] += ch

                    if focus == 0:
                        usernameMessage = None
                    elif focus == 4:
                        deleteError = ""
                    else:
                        passwordMessage = None

        if saveUsername:
            error = renameAccount(name, values[0])

            if error:
                usernameMessage = (error, red)
            else:
                name = values[0]
                usernameMessage = ("Username saved", green)

        if savePassword:
            error = changePassword(name, values[1], values[2], values[3])

            if error:
                passwordMessage = (error, red)
            else:
                values[1] = ""
                values[2] = ""
                values[3] = ""
                passwordMessage = ("Password saved", green)

        if submitDelete:
            if verifyPassword(name, values[4]):
                deleteRound += 1
                values[4] = ""

                if deleteRound >= DELETESTEPS:
                    deleteAccount(name)
                    return None

                deleteStage = 1
                deleteError = ""
                focus = 0
            else:
                deleteError = "Incorrect password"
                values[4] = ""

        cursorTimer += 1
        if cursorTimer >= 30:
            cursorTimer = 0
            showCursor = not showCursor

        screen.fill((15, 15, 22))

        title = mainFont.render("PROFILE", False, textColor)
        screen.blit(title, title.get_rect(center = (screen.get_width() // 2, 100)))
        pygame.draw.line(screen, (115, 115, 145), (170, 165), (1750, 165), width = 4)

        drawColorButton(screen, closeRect, "X", mousePos, (75, 40, 40), (130, 55, 55), smallFont)

        screen.blit(labelFont.render("USERNAME", False, dimText), (usernameRect.x, usernameRect.y - 35))
        screen.blit(labelFont.render("CHANGE PASSWORD", False, dimText), (oldRect.x, oldRect.y - 35))

        drawInputField(screen, usernameRect, values[0], "Username", focus == 0, showCursor, smallFont)
        drawInputField(screen, oldRect, "*" * len(values[1]), "Old Password", focus == 1, showCursor, smallFont)
        drawInputField(screen, newRect, "*" * len(values[2]), "New Password", focus == 2, showCursor, smallFont)
        drawInputField(screen, confirmRect, "*" * len(values[3]), "Confirm New Password", focus == 3, showCursor, smallFont)

        makeButton(screen, usernameSaveRect, "Save Changes", mousePos, 1.0, 255, smallFont)
        makeButton(screen, passwordSaveRect, "Save Changes", mousePos, 1.0, 255, smallFont)
        makeButton(screen, logoutRect, "Log Out", mousePos, 1.0, 255, smallFont)

        if usernameMessage:
            screen.blit(labelFont.render(usernameMessage[0], False, usernameMessage[1]), (usernameSaveRect.x, usernameSaveRect.bottom + 20))

        if passwordMessage:
            screen.blit(labelFont.render(passwordMessage[0], False, passwordMessage[1]), (passwordSaveRect.x, passwordSaveRect.bottom + 20))

        drawColorButton(screen, deleteRect, "Delete Account", mousePos, (110, 30, 30), (170, 45, 45), smallFont)

        if deleteStage == 1:
            prompt = labelFont.render(f"Are you sure? ({deleteRound + 1}/{DELETESTEPS})", False, (255, 120, 120))
            screen.blit(prompt, (deleteRect.x, deleteRect.bottom + 25))

            drawColorButton(screen, yesRect, "Yes", mousePos, (110, 30, 30), (170, 45, 45), smallFont)
            makeButton(screen, noRect, "No", mousePos, 1.0, 255, smallFont)

        elif deleteStage == 2:
            prompt = labelFont.render(f"Enter password to confirm ({deleteRound + 1}/{DELETESTEPS})", False, (255, 120, 120))
            screen.blit(prompt, (deleteRect.x, deleteRect.bottom + 25))

            drawInputField(screen, deletePasswordRect, "*" * len(values[4]), "Password", focus == 4, showCursor, smallFont)

            if deleteError:
                screen.blit(labelFont.render(deleteError, False, red), (deletePasswordRect.x, deletePasswordRect.bottom + 15))

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

async def chooseSaveOption(screen, saveData):
    titleFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 42)
    nameFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 30)
    statFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 20)
    smallIndexFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 15)

    dimText = (180, 180, 200)
    green = (120, 220, 120)

    wave = saveData.get("wave", 1)
    money = saveData.get("money", 0)
    upgradeNames = [
        game.upgradeDefinitions[u]["name"]
        for u in saveData.get("upgrades", [])
        if u in game.upgradeDefinitions
    ]

    upgradeText = ", ".join(upgradeNames) if upgradeNames else "None"
    upgradeLines = game.wrapText(statFont, upgradeText, 890)[:3]

    panel = pygame.Rect(0, 0, 1000, 560)
    panel.center = (screen.get_width() // 2, 520)

    buttonWidth = 440
    buttonHeight = 90
    gap = 60
    buttonsY = panel.bottom - 130
    startX = panel.centerx - (buttonWidth * 2 + gap) // 2

    continueRect = pygame.Rect(startX, buttonsY, buttonWidth, buttonHeight)
    newGameRect = pygame.Rect(startX + buttonWidth + gap, buttonsY, buttonWidth, buttonHeight)

    continueScale = 1.0
    newGameScale = 1.0
    scaleSpeed = 0.18

    while True:
        mousePos = pygame.mouse.get_pos()

        continueScale += ((1.1 if continueRect.collidepoint(mousePos) else 1.0) - continueScale) * scaleSpeed
        newGameScale += ((1.1 if newGameRect.collidepoint(mousePos) else 1.0) - newGameScale) * scaleSpeed

        scaledContinue = pygame.Rect(0, 0, int(buttonWidth * continueScale), int(buttonHeight * continueScale))
        scaledContinue.center = continueRect.center

        scaledNewGame = pygame.Rect(0, 0, int(buttonWidth * newGameScale), int(buttonHeight * newGameScale))
        scaledNewGame.center = newGameRect.center

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if scaledContinue.collidepoint(event.pos):
                    return True
                if scaledNewGame.collidepoint(event.pos):
                    return False

        screen.fill((15, 15, 22))

        title = titleFont.render("SAVE FOUND", False, textColor)
        screen.blit(title, title.get_rect(center = (screen.get_width() // 2, 100)))
        pygame.draw.line(screen, (115, 115, 145), (170, 165), (1750, 165), width = 4)

        pygame.draw.rect(screen, (28, 28, 40), panel)
        pygame.draw.rect(screen, textColor, panel, width = 4)

        name = nameFont.render(game.currentUser, False, textColor)
        screen.blit(name, name.get_rect(center = (panel.centerx, panel.y + 60)))
        pygame.draw.line(screen, green, (panel.x + 55, panel.y + 105), (panel.right - 55, panel.y + 105), width = 5)

        textX = panel.x + 55
        screen.blit(statFont.render(f"Wave: {wave}", False, textColor), (textX, panel.y + 140))
        screen.blit(statFont.render(f"Money: £{money}", False, textColor), (textX, panel.y + 190))
        screen.blit(statFont.render("Upgrades:", False, dimText), (textX, panel.y + 240))

        for i, line in enumerate(upgradeLines):
            screen.blit(statFont.render(line, False, textColor), (textX, panel.y + 280 + i * 38))

        makeButton(screen, scaledContinue, "Continue", mousePos, continueScale, 255, smallFont)
        makeButton(screen, scaledNewGame, "New Game", mousePos, newGameScale, 255, smallFont)

        hint = smallIndexFont.render("NEW GAME KEEPS YOUR SAVE UNTIL YOU SAVE AGAIN", False, (130, 130, 155))
        screen.blit(hint, hint.get_rect(center = (screen.get_width() // 2, panel.bottom + 45)))

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

async def showEnemyIndex():
    enemyData = [
        {
            "name": "Regular Dude",
            "color": (220, 40, 40),
            "stats": [
                "HP: 10",
                "Base Damage: 20"
            ]
        },
        {
            "name": "Shooter",
            "color": (255, 140, 0),
            "stats": [
                "HP: 20",
                "Abilities:",
                "Shoot: 10 Damage,",
                "2 second cooldown."
            ]
        },
        {
            "name": "Charger",
            "color": (20, 20, 140),
            "stats": [
                "HP: 20",
                "Base Damage: 20",
                "Abilities:",
                "Charge: 35 Damage,",
                "5 second cooldown."
            ]
        },
        {
            "name": "Iceman",
            "color": (153, 255, 255),
            "image": "Things/Images/Iceman.png",
            "stats": [
                "HP: 400",
                "Base Damage: 20",
                "Abilities:",
                "Slide: 2x Speed (3s) / 2s CD",
                "Freeze: 35 Damage (1.5s) ",
                "/ 7.5s CD"
            ]
        }
    ]

    titleFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 42)
    nameFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 30)
    statFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 20)
    smallIndexFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 15)

    selectedEnemy = 0
    enemyAngle = 0
    enemySize = 260

    leftArrowRect = pygame.Rect(75, 420, 110, 140)
    rightArrowRect = pygame.Rect(1735, 420, 110, 140)
    closeRect = pygame.Rect(1770, 40, 105, 75)

    fadeDuration = 500
    fadeStart = pygame.time.get_ticks()
    menuSnapshot = screen.copy()

    enemyImageCache = {}
    for enemy in enemyData:
        if "image" in enemy:
            img = pygame.image.load(enemy["image"]).convert_alpha()
            img = pygame.transform.smoothscale(img, (enemySize, enemySize))
            enemyImageCache[enemy["name"]] = img

    while True:
        currentTime = pygame.time.get_ticks()
        fadeT = min((currentTime - fadeStart) / fadeDuration, 1)
        fadeT = easeOut(fadeT)

        screen.blit(menuSnapshot, (0, 0))

        fadeSurface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        fadeSurface.fill((15, 15, 22, int(255 * fadeT)))
        screen.blit(fadeSurface, (0, 0))

        pygame.mixer.music.set_volume(1.0 - fadeT)

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

        if fadeT >= 1:
            break

    pygame.mixer.music.pause()
    secondChannel.play(secondMusic, loops =- 1)
    secondChannel.set_volume(1.0)

    while True:
        mousePos = pygame.mouse.get_pos()
        currentEnemy = enemyData[selectedEnemy]

        leftHover = leftArrowRect.collidepoint(mousePos)
        rightHover = rightArrowRect.collidepoint(mousePos)
        closeHover = closeRect.collidepoint(mousePos)

        enemyAngle = (enemyAngle + 2) % 360

        if currentEnemy["name"] in enemyImageCache:
            enemySurface = enemyImageCache[currentEnemy["name"]]
        else:
            enemySurface = createSquareSurface(currentEnemy["color"], enemySize)

        rotatedEnemy = pygame.transform.rotate(enemySurface, -enemyAngle)
        rotatedEnemyRect = rotatedEnemy.get_rect(center = (610, 510))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if leftArrowRect.collidepoint(mousePos):
                    selectedEnemy = (selectedEnemy - 1) % len(enemyData)

                elif rightArrowRect.collidepoint(mousePos):
                    selectedEnemy = (selectedEnemy + 1) % len(enemyData)

                elif closeRect.collidepoint(mousePos):
                    closeFadeStart = pygame.time.get_ticks()
                    enemyIndexSnapshot = screen.copy()

                    while True:
                        currentTime = pygame.time.get_ticks()
                        fadeT = min((currentTime - closeFadeStart) / fadeDuration, 1)
                        fadeT = easeOut(fadeT)

                        screen.blit(enemyIndexSnapshot, (0, 0))

                        fadeSurface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                        fadeSurface.fill((15, 15, 22, int(255 * fadeT)))
                        screen.blit(fadeSurface, (0, 0))

                        secondChannel.set_volume(1.0 - fadeT)

                        pygame.display.update()
                        clock.tick(60)
                        await asyncio.sleep(0)

                        if fadeT >= 1:
                            secondChannel.stop()
                            pygame.mixer.music.unpause()
                            pygame.mixer.music.set_volume(1.0)
                            return

        screen.fill((15, 15, 22))

        titleSurface = titleFont.render("ENEMY INDEX", False, textColor)
        titleRect = titleSurface.get_rect(center  =(screen.get_width() // 2, 100))
        screen.blit(titleSurface, titleRect)

        pygame.draw.line(screen, (115, 115, 145), (170, 165), (1750, 165), width = 4)

        previewPanel = pygame.Rect(250, 230, 720, 570)
        pygame.draw.rect(screen, (28, 28, 40), previewPanel)
        pygame.draw.rect(screen, textColor, previewPanel, width = 4)

        previewLabel = smallIndexFont.render("ENEMY PREVIEW", False, (180, 180, 200))
        previewLabelRect = previewLabel.get_rect(center = (previewPanel.centerx, 280))
        screen.blit(previewLabel, previewLabelRect)

        pygame.draw.line(
            screen,
            currentEnemy["color"],
            (previewPanel.x + 50, 325),
            (previewPanel.right - 50, 325),
            width = 5
        )

        screen.blit(rotatedEnemy, rotatedEnemyRect)
        statsPanel = pygame.Rect(1030, 230, 640, 570)
        pygame.draw.rect(screen, (28, 28, 40), statsPanel)
        pygame.draw.rect(screen, textColor, statsPanel, width = 4)

        nameSurface = nameFont.render(currentEnemy["name"], False, textColor)
        nameRect = nameSurface.get_rect(center = (statsPanel.centerx, 305))
        screen.blit(nameSurface, nameRect)

        pygame.draw.line(
            screen,
            currentEnemy["color"],
            (statsPanel.x + 55, 365),
            (statsPanel.right - 55, 365),
            width = 5
        )

        statY = 430
        for stat in currentEnemy["stats"]:
            statSurface = statFont.render(stat, False, textColor)
            screen.blit(statSurface, (statsPanel.x + 55, statY))
            statY += 58

        leftColor = buttonHover if leftHover else buttonColor
        pygame.draw.rect(screen, leftColor, leftArrowRect)
        pygame.draw.rect(screen, textColor, leftArrowRect, width = 3)

        leftText = mainFont.render("<", False, textColor)
        leftTextRect = leftText.get_rect(center = leftArrowRect.center)
        screen.blit(leftText, leftTextRect)

        rightColor = buttonHover if rightHover else buttonColor
        pygame.draw.rect(screen, rightColor, rightArrowRect)
        pygame.draw.rect(screen, textColor, rightArrowRect, width = 3)

        rightText = mainFont.render(">", False, textColor)
        rightTextRect = rightText.get_rect(center = rightArrowRect.center)
        screen.blit(rightText, rightTextRect)

        closeColor = (130, 55, 55) if closeHover else (75, 40, 40)
        pygame.draw.rect(screen, closeColor, closeRect)
        pygame.draw.rect(screen, textColor, closeRect, width = 3)

        closeText = nameFont.render("X", False, textColor)
        closeTextRect = closeText.get_rect(center = closeRect.center)
        screen.blit(closeText, closeTextRect)

        pageSurface = smallIndexFont.render(
            f"{selectedEnemy + 1} / {len(enemyData)}",
            False,
            (180, 180, 200)
        )
        pageRect = pageSurface.get_rect(center = (screen.get_width() // 2, 865))
        screen.blit(pageSurface, pageRect)

        hintSurface = smallIndexFont.render(
            "CLICK < OR > TO VIEW ENEMIES",
            False,
            (130, 130, 155)
        )
        hintRect = hintSurface.get_rect(center=(screen.get_width() // 2, 910))
        screen.blit(hintSurface, hintRect)

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)

async def menuMain():
    global you

    await checkPassword()
    await cloud.pull(ACCOUNTSKEY, {})

    lastUser = loadLastUser()
    accounts = loadAccounts()

    if lastUser and lastUser.lower() in accounts:
        game.currentUser = accounts[lastUser.lower()]["username"]
    else:
        game.currentUser = await accountScreen()
        saveLastUser(game.currentUser)

    you = await loadUserData(game.currentUser)
    startMenuMusic()

    duration = 1000
    start = pygame.time.get_ticks()

    textY = -100
    buttonX = -450

    currentScale = 1.0
    targetScale = 1.0

    settingsCurrentScale = 1.0
    settingsTargetScale = 1.0

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

    profileButtonRect = pygame.Rect(1540, 905, 360, 55)
    profileButtonFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 18)
    usernameFont = pygame.font.Font("Things/Fonts/PressStart2P.ttf", 22)

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

        currentSettingsButton = settingsButtonTarget.copy()
        currentSettingsButton.x = lerp(buttonX, settingsButtonTarget.x, t)

        settingsHovering = currentSettingsButton.collidepoint(mousePos) and t >= 1
        settingsTargetScale = 1.15 if settingsHovering else 1.0

        settingsCurrentScale += (settingsTargetScale - settingsCurrentScale) * scaleSpeed

        settingsScaledWidth = int(settingsButtonTarget.width * settingsCurrentScale)
        settingsScaledHeight = int(settingsButtonTarget.height * settingsCurrentScale)

        scaledSettingsButton = pygame.Rect(0, 0, settingsScaledWidth, settingsScaledHeight)
        scaledSettingsButton.center = currentSettingsButton.center

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
                await cloud.pull(game.saveStorageKey(), None)

                loadSave = False
                saveData = game.loadGameData()

                if saveData:
                    loadSave = await chooseSaveOption(screen, saveData)

                await game.startGame(screen, you, loadSave)
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

                if scaledSettingsButton.collidepoint(mousePos) and t >= 1 and not transitioning and not startingGame and not isOnLeft:
                    await showEnemyIndex()

                if profileButtonRect.collidepoint(mousePos) and t >= 1 and not transitioning and not startingGame and not isOnLeft:
                    profileResult = await profileScreen(game.currentUser)

                    if profileResult is None:
                        pygame.mixer.music.stop()
                        game.currentUser = await accountScreen()

                        saveLastUser(game.currentUser)
                        you = await loadUserData(game.currentUser)

                        squareSurface = createSquareSurface(you, squareSize)
                        rotatedCache.clear()

                        startMenuMusic()
                    else:
                        game.currentUser = profileResult

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

                    saveColor(game.currentUser, you)

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
            makeButton(screen, scaledSettingsButton, "Enemy Index", mousePos, settingsCurrentScale,uiAlpha, enemyIndexButtonFont)

            userSurface = usernameFont.render(game.currentUser, False, textColor)
            userSurface.set_alpha(uiAlpha)
            screen.blit(userSurface, userSurface.get_rect(bottomright = (profileButtonRect.right, profileButtonRect.top - 12)))
            makeButton(screen, profileButtonRect, "View Profile", mousePos, 1.0, uiAlpha, profileButtonFont)

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