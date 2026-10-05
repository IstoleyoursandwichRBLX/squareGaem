import asyncio
import math
import os
from dataclasses import dataclass
import pygame
import sys

FONTPATH = "Things/Fonts/PressStart2P.ttf"
BACKGROUND = (18, 18, 28)
PANEL = (42, 42, 58)
PANELHOVER = (70, 70, 92)
BORDER = (235, 235, 245)
MUTED = (176, 176, 198)
NAMEPLATE = (72, 82, 125)
ACCENT = (122, 190, 255)

FONTCACHE = {}
WIDTHCACHE = {}
GLYPHCACHE = {}

COMMAPAUSE = 150
SENTENCEPAUSE = 750
ANSWERFADEDURATION = 300

CHOSENHOLD = 180

PANELMARGIN = 55
PANELBOTTOMMARGIN = 60
PANELMINHEIGHT = 225
PADDING = 35
TEXTTOP = 40
BOTTOMPADDING = 28
HINTSPACE = 50
ANSWERTOPGAP = 24

TEXTSIZE = 20
BIGSIZE = 30
MINLINEHEIGHT = 34

BUTTONHEIGHT = 58
BUTTONGAP = 22
ROWGAP = 14
MAXCOLUMNS = 3

DIMALPHA = 90

@dataclass(frozen = True)
class Glyph:
    character: str
    big: bool = False
    shaky: bool = False



def bigText(text):
    return f"[big]{text}[/big]"

def shakyText(text):
    return f"[shaky]{text}[/shaky]"

def font(size):
    if size not in FONTCACHE:
        if os.path.exists(FONTPATH):
            FONTCACHE[size] = pygame.font.Font(FONTPATH, size)
        else:
            FONTCACHE[size] = pygame.font.SysFont("monospace", size, bold = True)

    return FONTCACHE[size]

def parseText(text):
    glyphs = []
    big = False
    shaky = False
    index = 0

    tags = {
        "[big]": ("big", True),
        "[/big]": ("big", False),
        "[shaky]": ("shaky", True),
        "[/shaky]": ("shaky", False)
    }

    while index < len(text):
        matchedTag = None

        for tag in tags:
            if text.startswith(tag, index):
                matchedTag = tag
                break

        if matchedTag is not None:
            attribute, value = tags[matchedTag]

            if attribute == "big":
                big = value
            else:
                shaky = value

            index += len(matchedTag)
            continue

        glyphs.append(Glyph(text[index], big, shaky))
        index += 1

    return glyphs

def glyphFont(glyph):
    return font(BIGSIZE if glyph.big else TEXTSIZE)


def glyphWidth(glyph):
    key = (glyph.big, glyph.character)
    width = WIDTHCACHE.get(key)

    if width is None:
        width = glyphFont(glyph).size(glyph.character)[0]
        WIDTHCACHE[key] = width

    return width


def glyphSurface(glyph):
    key = (glyph.big, glyph.character)
    rendered = GLYPHCACHE.get(key)

    if rendered is None:
        rendered = glyphFont(glyph).render(glyph.character, False, BORDER)
        GLYPHCACHE[key] = rendered

    return rendered

def typewriterPause(chr):
    if chr == ",":
        return COMMAPAUSE

    if chr in ".!?":
        return SENTENCEPAUSE
    return 0

def normaliseAnswers(answers):
    if isinstance(answers, dict):
        return [(value, str(label)) for value, label in answers.items()]

    normalised = []

    for answer in answers:
        if isinstance(answer, (tuple, list)) and len(answer) == 2:
            normalised.append((answer[0], str(answer[1])))
        else:
            normalised.append((answer, str(answer)))

    return normalised

def splitWords(glyphs):
    words = []
    current = []

    for glyph in glyphs:
        if glyph.character == "\n":
            if current:
                words.append(current)
                current = []

            words.append([glyph])
            continue

        current.append(glyph)

        if glyph.character == " ":
            words.append(current)
            current = []

    if current:
        words.append(current)

    return words


def layoutGlyphs(glyphs, maxWidth):
    lines = [[]]
    lineWidth = 0

    for word in splitWords(glyphs):
        if len(word) == 1 and word[0].character == "\n":
            lines.append([])
            lineWidth = 0
            continue

        wordWidth = sum(glyphWidth(glyph) for glyph in word)
        trailingSpace = glyphWidth(word[-1]) if word[-1].character == " " else 0

        if lines[-1] and lineWidth + wordWidth - trailingSpace > maxWidth:
            lines.append([])
            lineWidth = 0

        for glyph in word:
            width = glyphWidth(glyph)

            if lines[-1] and glyph.character != " " and lineWidth + width > maxWidth:
                lines.append([])
                lineWidth = 0

            lines[-1].append((glyph, lineWidth))
            lineWidth += width

    return lines


def lineHeight(line):
    height = MINLINEHEIGHT

    for glyph, _xOffset in line:
        height = max(height, glyphFont(glyph).get_height() + 8)

    return height


def answerBlockHeight(answerCount):
    columns = min(answerCount, MAXCOLUMNS)
    rows = math.ceil(answerCount / columns)
    return rows * BUTTONHEIGHT + (rows - 1) * ROWGAP


def answerRectangles(panelRect, answerCount):
    columns = min(answerCount, MAXCOLUMNS)
    availableWidth = panelRect.width - PADDING * 2
    buttonWidth = (availableWidth - BUTTONGAP * (columns - 1)) // columns
    top = panelRect.bottom - BOTTOMPADDING - answerBlockHeight(answerCount)

    rectangles = []

    for index in range(answerCount):
        row, column = divmod(index, columns)

        rectangles.append(
            pygame.Rect(
                panelRect.x + PADDING + column * (buttonWidth + BUTTONGAP),
                top + row * (BUTTONHEIGHT + ROWGAP),
                buttonWidth,
                BUTTONHEIGHT
            )
        )

    return rectangles


def fitLabel(label, maxWidth):
    rendered = None

    for size in (16, 14, 12, 10):
        rendered = font(size).render(label, False, BORDER)

        if rendered.get_width() <= maxWidth:
            break

    return rendered


def panelRectangle(surface, height):
    screenRect = surface.get_rect()

    return pygame.Rect(
        PANELMARGIN,
        screenRect.height - PANELBOTTOMMARGIN - height,
        screenRect.width - PANELMARGIN * 2,
        height
    )


def drawPanel(surface, panelRect, nameSurface):
    shadowRect = panelRect.move(8, 9)
    pygame.draw.rect(surface, (5, 5, 10), shadowRect, border_radius = 14)
    pygame.draw.rect(surface, BACKGROUND, panelRect, border_radius = 14)
    pygame.draw.rect(surface, BORDER, panelRect, width = 4, border_radius = 14)

    nameRect = pygame.Rect(
        panelRect.x + 28,
        panelRect.y - 28,
        nameSurface.get_width() + 40,
        48
    )

    pygame.draw.rect(surface, NAMEPLATE, nameRect, border_radius = 8)
    pygame.draw.rect(surface, BORDER, nameRect, width = 3, border_radius = 8)
    surface.blit(nameSurface, nameSurface.get_rect(center = nameRect.center))


def drawText(surface, lines, heights, visibleCount, panelRect, now):
    visible = 0
    lineY = panelRect.y + TEXTTOP

    for line, height in zip(lines, heights):
        for glyph, xOffset in line:
            if visible >= visibleCount:
                return

            x = panelRect.x + PADDING + xOffset
            y = lineY

            if glyph.shaky:
                phase = visible * 1.91
                x += int(math.sin(now * 0.019 + phase) * 2)
                y += int(math.cos(now * 0.027 + phase * 1.7) * 3)

            surface.blit(glyphSurface(glyph), (x, y))
            visible += 1

        lineY += height


def drawContinueHint(surface, panelRect, now):
    if (now // 500) % 2 != 0:
        return

    hint = font(14).render("CLICK TO CONTINUE", False, MUTED)
    hintRect = hint.get_rect(bottomright = (panelRect.right - 24, panelRect.bottom - 18))
    surface.blit(hint, hintRect)


def drawAnswers(surface, answerRects, labels, numbers, hoveredIndex, chosenIndex, alpha):
    for index, buttonRect in enumerate(answerRects):
        active = index == hoveredIndex or index == chosenIndex
        color = PANELHOVER if active else PANEL
        borderColor = ACCENT if active else BORDER

        buttonSurface = pygame.Surface(buttonRect.size, pygame.SRCALPHA)
        localRect = (0, 0, buttonRect.width, buttonRect.height)

        pygame.draw.rect(buttonSurface, (*color, alpha), localRect, border_radius = 8)
        pygame.draw.rect(buttonSurface, (*borderColor, alpha), localRect, width = 3, border_radius = 8)

        label = labels[index]
        label.set_alpha(alpha)
        buttonSurface.blit(label, label.get_rect(center = (buttonRect.width // 2, buttonRect.height // 2)))

        if numbers is not None:
            number = numbers[index]
            number.set_alpha(alpha)
            buttonSurface.blit(number, (10, 8))

        surface.blit(buttonSurface, buttonRect.topleft)


def fadeAlpha(now, startTime):
    if startTime is None:
        return 0

    progress = min((now - startTime) / ANSWERFADEDURATION, 1)
    return int(255 * progress)


async def runDialogue(surface, name, text, speed, answers):
    glyphs = parseText(str(text))
    textWidth = surface.get_width() - PANELMARGIN * 2 - PADDING * 2
    lines = layoutGlyphs(glyphs, textWidth)
    heights = [lineHeight(line) for line in lines]
    flatGlyphs = [glyph for line in lines for glyph, _xOffset in line]
    totalGlyphs = len(flatGlyphs)
    textHeight = sum(heights)

    if answers:
        contentHeight = TEXTTOP + textHeight + ANSWERTOPGAP + answerBlockHeight(len(answers)) + BOTTOMPADDING
    else:
        contentHeight = TEXTTOP + textHeight + HINTSPACE

    panelRect = panelRectangle(surface, max(PANELMINHEIGHT, contentHeight))
    nameSurface = font(22).render(str(name), False, BORDER)

    answerRects = []
    labels = []
    numbers = None

    if answers:
        answerRects = answerRectangles(panelRect, len(answers))
        labels = [fitLabel(label, rect.width - 24) for (_value, label), rect in zip(answers, answerRects)]

        if len(answers) <= 9:
            numbers = [font(10).render(str(index + 1), False, MUTED) for index in range(len(answers))]

    background = surface.copy()
    dim = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    dim.fill((0, 0, 0, DIMALPHA))
    background.blit(dim, (0, 0))

    clock = pygame.time.Clock()
    speedMs = max(float(speed), 0.001) * 1000

    visibleCount = 0
    nextCharacterTime = pygame.time.get_ticks() + speedMs
    completeTime = None
    chosenIndex = None
    chosenTime = 0

    while True:
        now = pygame.time.get_ticks()

        while visibleCount < totalGlyphs and now >= nextCharacterTime:
            typed = flatGlyphs[visibleCount].character
            visibleCount += 1
            nextCharacterTime += speedMs + typewriterPause(typed)

        complete = visibleCount >= totalGlyphs

        if complete and completeTime is None:
            completeTime = now

        answerAlpha = fadeAlpha(now, completeTime)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if chosenIndex is not None:
                continue

            advance = False
            clickPosition = None
            pressedIndex = None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                advance = True
                clickPosition = event.pos
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    advance = True
                elif answers and pygame.K_1 <= event.key <= pygame.K_9:
                    pressedIndex = event.key - pygame.K_1

            if not advance and pressedIndex is None:
                continue

            if not complete:
                if advance:
                    visibleCount = totalGlyphs
                    complete = True
                    completeTime = now
                continue

            if not answers:
                if advance:
                    return None
                continue

            if answerAlpha < 255:
                continue

            if clickPosition is not None:
                for index, buttonRect in enumerate(answerRects):
                    if buttonRect.collidepoint(clickPosition):
                        chosenIndex = index
                        break
            elif pressedIndex is not None and pressedIndex < len(answers):
                chosenIndex = pressedIndex

            if chosenIndex is not None:
                chosenTime = now

        if chosenIndex is not None and now - chosenTime >= CHOSENHOLD:
            return answers[chosenIndex][0]

        hoveredIndex = None

        if answers and complete and chosenIndex is None and fadeAlpha(now, completeTime) >= 255:
            mousePosition = pygame.mouse.get_pos()

            for index, buttonRect in enumerate(answerRects):
                if buttonRect.collidepoint(mousePosition):
                    hoveredIndex = index
                    break

        surface.blit(background, (0, 0))
        drawPanel(surface, panelRect, nameSurface)
        drawText(surface, lines, heights, visibleCount, panelRect, now)

        if complete:
            if answers:
                drawAnswers(
                    surface,
                    answerRects,
                    labels,
                    numbers,
                    hoveredIndex,
                    chosenIndex,
                    fadeAlpha(now, completeTime)
                )
            else:
                drawContinueHint(surface, panelRect, now)

        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)


async def createDialogue(surface, name, text, speed = 0.025):
    await runDialogue(surface, name, text, speed, None)


async def createAnswerDialogue(surface, name, text, speed = 0.025, answers = ()):
    if not isinstance(speed, (int, float)):
        answers = speed
        speed = 0.025

    answers = normaliseAnswers(answers)

    if not answers:
        raise ValueError("Needs at least one answer.")

    return await runDialogue(surface, name, text, speed, answers)