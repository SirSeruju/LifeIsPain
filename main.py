import numpy as np
import pygame as pg
import os
import random


def lifeStep(arr):
    sums = np.roll(arr, (-1, -1), axis=(0, 1)) +\
        np.roll(arr, (-1,  0), axis=(0, 1)) +\
        np.roll(arr, (-1,  1), axis=(0, 1)) +\
        np.roll(arr, (0,  1), axis=(0, 1)) +\
        np.roll(arr, (1,  1), axis=(0, 1)) +\
        np.roll(arr, (1,  0), axis=(0, 1)) +\
        np.roll(arr, (1, -1), axis=(0, 1)) +\
        np.roll(arr, (0, -1), axis=(0, 1))
    lifeSums = sums * arr
    deathSums = sums - lifeSums
    b = np.vectorize(lambda x: 1 if x in [3] else 0)
    s = np.vectorize(lambda x: 1 if x in [2, 3] else 0)
    return s(lifeSums) + b(deathSums)


def loadLevel(filename):
    data = open(filename, "r").read().strip().split("\n")
    name = data[0]
    c = int(data[1])
    data = data[2:]
    a1 = data[:len(data) // 2]
    a2 = data[len(data) // 2:]
    a1 = list(map(lambda x: list(map(int, list(x))), a1))
    a2 = list(map(lambda x: list(map(int, list(x))), a2))
    return (name, c, np.flipud(np.rot90(np.array(a1))), np.flipud(np.rot90(np.array(a2))))


def helpMode(surface, events, modes, info):
    helpLines = [
        "Rules:",
        "  To win you must color all green cells",
        "    and don't color red.",
        "  When you set cells,",
        "  you may will start Game of Life on field.",
        "  Live cell will color cell on field.",
        "Left mouse key to interact with menus.",
        "Left mouse key to set/unset cell.",
        "Right mouse key to move on field.",
        "Mouse wheel to zoom/unzoom field.",
        "Press any key to get back to menu..."
    ]
    indent = info["help"]["indent"]
    hintSize = info["help"]["size"]
    size = surface.get_size()
    font = info["help"]["font"]
    for event in events:
        if event.type == pg.QUIT:
            return (surface, modes["exit"], info)
        if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
            return (surface, modes["menu"], info)

    surface.fill((0, 0, 0))
    pg.draw.rect(surface, info["help"]["color"], ((1 - hintSize[0]) * size[0] / 2, (1 - hintSize[1]) * size[1] / 2,
                                                  size[0] * hintSize[0],
                                                  size[1] * hintSize[1]))

    lineOffset = ((1 - hintSize[0]) * size[0] / 2 + hintSize[0] * size[0] * indent[0],
                  (1 - hintSize[1]) * size[1] / 2 + hintSize[1] * size[1] * indent[1])
    lineSize = hintSize[1] * size[1] * (1 - 2 * indent[1]) / len(helpLines)
    for i in range(len(helpLines)):
        f = font.render(helpLines[i], False, (200, 200, 200))
        surface.blit(f, (lineOffset[0],
                         lineOffset[1] + (lineSize - f.get_size()[1]) / 2 + lineSize * i))

    return (surface, modes["help"], info)


def winMode(surface, events, modes, info):
    font = info["win"]["font"]
    f = font.render(
        "You win! Press any key to get back to levels...", False, (200, 200, 200))
    surface.blit(f, (surface.get_width() / 2 - f.get_size()[0] / 2,
                     surface.get_height() / 2 - f.get_size()[1] / 2))
    for event in events:
        if event.type == pg.QUIT:
            return (surface, modes["exit"], info)
        if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
            return (surface, modes["levels"], info)

    return (surface, modes["win"], info)


def loseMode(surface, events, modes, info):
    font = info["lose"]["font"]
    f = font.render("You lose! Press any key to try again...",
                    False, (200, 200, 200))
    surface.blit(f, (surface.get_width() / 2 - f.get_size()[0] / 2,
                     surface.get_height() / 2 - f.get_size()[1] / 2))
    for event in events:
        if event.type == pg.QUIT:
            return (surface, modes["exit"], info)
        if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
            return (surface, modes["level"], info)
    return (surface, modes["lose"], info)


def levelMode(surface, events, modes, info):
    info["level"]["coloredLevel"] = np.sign(
        info["level"]["coloredLevel"] + info["level"]["currentLevel"])
    if np.any(info["level"]["coloredLevel"] * info["level"]["mustNotColoredLevel"]):
        info["level"]["stop"] = True
        info["level"]["playing"] = False
        info["level"]["coloredLevel"] = np.zeros(info["level"]["level"].shape)
        info["level"]["currentLevel"] = info["level"]["level"].copy()
        return (surface, modes["lose"], info)
        info["level"]["playing"] = False
    elif np.sum(info["level"]["coloredLevel"] * info["level"]["mustColoredLevel"]) == np.sum(info["level"]["mustColoredLevel"]):
        info["level"]["playing"] = False
        info["level"]["stop"] = True
        return (surface, modes["win"], info)
    if info["level"]["playing"]:
        info["level"]["currentLevel"] = lifeStep(info["level"]["currentLevel"])

    buttons = [
        "Reset",
        "Play" if not info["level"]["playing"] else "Pause",
        "Stop",
        "Back",
        "Available: " +
        str(int(info["level"]["cells"] - np.sum(info["level"]["level"])))
    ]
    tileSize = info["level"]["tileSize"]
    zoom = info["level"]["zoom"]
    camera = info["level"]["camera"]
    size = surface.get_size()
    field = info["level"]["currentLevel"]
    mustColoredField = info["level"]["mustColoredLevel"]
    mustNotColoredField = info["level"]["mustNotColoredLevel"]
    coloredField = info["level"]["coloredLevel"]
    font = info["level"]["font"]
    menuIndent = info["level"]["menuIndent"]
    menuOffset = info["level"]["menuOffset"]
    buttonSize = (size[0] * info["level"]["menuSize"][0] * ((1 - 2 * menuIndent[0] + menuOffset) / len(buttons) - menuOffset),
                  size[1] * info["level"]["menuSize"][1] * (1 - 2 * menuIndent[1]))
    offset = (camera[0] * zoom + (size[0] - field.shape[0] * tileSize * zoom) / 2,
              camera[1] * zoom + (size[1] - field.shape[1] * tileSize * zoom) / 2)
    for event in events:
        if event.type == pg.QUIT:
            return (surface, modes["exit"], info)
        if event.type == pg.MOUSEMOTION:
            if info["level"]["moving"] == True:
                p = info["level"]["camera"]
                d = pg.mouse.get_rel()
                info["level"]["camera"] = (
                    p[0] + d[0] / zoom, p[1] + d[1] / zoom)
            pos = (event.pos[0],
                   event.pos[1])
            for row in range(field.shape[1]):
                for col in range(field.shape[0]):
                    p = (offset[0] + col * tileSize * zoom,
                         offset[1] + row * tileSize * zoom)
                    if p[0] <= pos[0] <= p[0] + tileSize * zoom and\
                       p[1] <= pos[1] <= p[1] + tileSize * zoom:
                        info["level"]["activeCell"] = (col, row)
                        info["level"]["activeButton"] = -1
                        break
            for i in range(len(buttons)):
                p = (size[0] * menuIndent[0] + (buttonSize[0] + menuOffset * size[0] * info["level"]["menuSize"][0]) * i,
                     size[1] * menuIndent[1])
                if p[0] <= pos[0] <= p[0] + buttonSize[0] and\
                   p[1] <= pos[1] <= p[1] + buttonSize[1]:
                    info["level"]["activeCell"] = (-1, -1)
                    info["level"]["activeButton"] = i
                    break
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = (event.pos[0],
                   event.pos[1])
            if event.button == 4:
                info["level"]["zoom"] += info["level"]["zoomDelta"]
                info["level"]["zoom"] = min(10, info["level"]["zoom"])
            elif event.button == 5:
                info["level"]["zoom"] -= info["level"]["zoomDelta"]
                info["level"]["zoom"] = max(0.1, info["level"]["zoom"])
            elif event.button == 1:
                if info["level"]["activeCell"] != (-1, -1) and info["level"]["stop"]:
                    c = info["level"]["level"][info["level"]["activeCell"]]
                    if c == 1:
                        info["level"]["level"][info["level"]["activeCell"]] = 0
                        info["level"]["coloredLevel"][info["level"]
                                                      ["activeCell"]] = 0
                    elif mustNotColoredField[info["level"]["activeCell"]] != 1 and\
                            np.sum(info["level"]["currentLevel"]) < info["level"]["cells"]:
                        info["level"]["level"][info["level"]["activeCell"]] = 1
                    info["level"]["currentLevel"] = info["level"]["level"].copy()
                elif info["level"]["activeButton"] != -1:
                    for i in range(len(buttons)):
                        p = (size[0] * menuIndent[0] + (buttonSize[0] + menuOffset * size[0] * info["level"]["menuSize"][0]) * i,
                             size[1] * menuIndent[1])
                        if p[0] <= pos[0] <= p[0] + buttonSize[0] and\
                           p[1] <= pos[1] <= p[1] + buttonSize[1]:
                            if i == 0:
                                info["level"]["stop"] = True
                                info["level"]["playing"] = False
                                info["level"]["coloredLevel"] = np.zeros(
                                    info["level"]["level"].shape)
                                info["level"]["level"] = np.zeros(
                                    info["level"]["level"].shape)
                                info["level"]["currentLevel"] = info["level"]["level"].copy()
                            elif i == 1:
                                info["level"]["stop"] = False
                                info["level"]["playing"] = not info["level"]["playing"]
                            elif i == 2:
                                info["level"]["stop"] = True
                                info["level"]["playing"] = False
                                info["level"]["currentLevel"] = info["level"]["level"].copy()
                                info["level"]["coloredLevel"] = np.zeros(
                                    info["level"]["level"].shape)
                            elif i == 3:
                                info["level"]["stop"] = True
                                info["level"]["playing"] = False
                                info["level"]["activeButton"] = -1
                                info["level"]["activeCell"] = (-1, -1)
                                return (surface, modes["levels"], info)
                            break
            elif event.button == 3:
                info["level"]["moving"] = True
                pg.mouse.get_rel()
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 3:
                info["level"]["moving"] = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                return (surface, modes["levels"], info)

    surface.fill((0, 0, 0))
    for row in range(field.shape[1]):
        for col in range(field.shape[0]):
            colorDelta = 70
            coloredDelta = 30
            color = (10, 10, 10)
            if field[col, row] == 1:
                color = (color[0], color[1], color[2] + colorDelta)
            if mustColoredField[col, row] == 1:
                color = (color[0], color[1] + colorDelta, color[2])
            if mustNotColoredField[col, row] == 1:
                color = (color[0] + colorDelta, color[1], color[2])
            if coloredField[col, row] == 1:
                color = (color[0] + coloredDelta, color[1] +
                         coloredDelta, color[2] + coloredDelta)
            if (col, row) == info["level"]["activeCell"]:
                color = (color[0] + colorDelta, color[1] +
                         colorDelta, color[2] + colorDelta)
            pg.draw.rect(surface, color, (offset[0] + col * tileSize * zoom,
                                          offset[1] + row * tileSize * zoom,
                                          tileSize * zoom, tileSize * zoom))
    for i in range(len(buttons)):
        p = (size[0] * menuIndent[0] + (buttonSize[0] + menuOffset * size[0] * info["level"]["menuSize"][0]) * i,
             size[1] * menuIndent[1])
        color = info["level"]["buttonBackground"]
        if i == info["level"]["activeButton"]:
            color = info["level"]["activeButtonBackground"]
        pg.draw.rect(surface, color, (p[0], p[1],
                                      buttonSize[0], buttonSize[1]))
        f = font.render(buttons[i], False, (200, 200, 200))
        surface.blit(f, (p[0] + (buttonSize[0] - f.get_size()[0]) / 2,
                         p[1] + (buttonSize[1] - f.get_size()[1]) / 2))
    return (surface, modes["level"], info)


def levelsMode(surface, events, modes, info):
    indent = info["levels"]["indent"]
    offset = info["levels"]["offset"]
    size = surface.get_size()
    font = info["levels"]["font"]
    levels = info["levels"]["levels"]
    buttonSize = (size[0] * (1 - 2 * indent[0]),
                  size[1] * (1 - 2 * indent[1] + offset) / (len(levels) + 1) - offset * size[1])

    for event in events:
        if event.type == pg.QUIT:
            return (surface, modes["exit"], info)
        if event.type == pg.MOUSEMOTION:
            pos = event.pos
            for i in range(len(levels) + 1):
                p = (size[0] * indent[0], size[1] * indent[1] +
                     (buttonSize[1] + size[1] * offset) * i)
                if p[0] <= pos[0] <= p[0] + buttonSize[0] and\
                   p[1] <= pos[1] <= p[1] + buttonSize[1]:
                    info["levels"]["activeButton"] = i
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = event.pos
            for i in range(len(levels) + 1):
                p = (size[0] * indent[0], size[1] * indent[1] +
                     (buttonSize[1] + size[1] * offset) * i)
                if p[0] <= pos[0] <= p[0] + buttonSize[0] and\
                   p[1] <= pos[1] <= p[1] + buttonSize[1]:
                    if i == 0:
                        return (surface, modes["menu"], info)
                    info["level"]["cells"] = info["levels"]["levels"][i - 1][1]
                    info["level"]["level"] = np.zeros(
                        info["levels"]["levels"][i - 1][2].shape)
                    info["level"]["currentLevel"] = np.zeros(
                        info["levels"]["levels"][i - 1][2].shape)
                    info["level"]["mustColoredLevel"] = info["levels"]["levels"][i - 1][2].copy()
                    info["level"]["mustNotColoredLevel"] = info["levels"]["levels"][i - 1][3].copy()
                    info["level"]["coloredLevel"] = np.zeros(
                        info["level"]["level"].shape)
                    return (surface, modes["level"], info)
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                return (surface, modes["menu"], info)

    surface.fill((0, 0, 0))
    for i in range(len(levels) + 1):
        p = (size[0] * indent[0], size[1] * indent[1] +
             (buttonSize[1] + size[1] * offset) * i)
        color = info["levels"]["buttonBackground"]
        if i == info["levels"]["activeButton"]:
            color = info["levels"]["activeButtonBackground"]
        pg.draw.rect(surface, color,
                     (p[0], p[1], buttonSize[0], buttonSize[1]))
        f = font.render(
            "Back" if i == 0 else levels[i - 1][0], False, (200, 200, 200))
        surface.blit(f, (p[0] + (buttonSize[0] - f.get_size()[0]) / 2,
                         p[1] + (buttonSize[1] - f.get_size()[1]) / 2))
    return (surface, modes["levels"], info)


def exitMode(surface, events, modes, info):
    return None


def creditsMode(surface, events, modes, info):
    creditLines = [
        "Seruju aka XutXtuX:",
        "  https://github.com/SirSeruju",
        "  https://github.com/XutXtuX",
        "  https://habr.com/users/xutxtux/",
        "Bezlikiy:",
        "  https://github.com/Bez-log",
        "Press any key to get back to menu..."
    ]
    indent = info["credits"]["indent"]
    hintSize = info["credits"]["size"]
    size = surface.get_size()
    font = info["credits"]["font"]
    for event in events:
        if event.type == pg.QUIT:
            return (surface, modes["exit"], info)
        if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
            return (surface, modes["menu"], info)

    surface.fill((0, 0, 0))
    pg.draw.rect(surface, info["credits"]["color"], ((1 - hintSize[0]) * size[0] / 2, (1 - hintSize[1]) * size[1] / 2,
                                                     size[0] * hintSize[0],
                                                     size[1] * hintSize[1]))

    lineOffset = ((1 - hintSize[0]) * size[0] / 2 + hintSize[0] * size[0] * indent[0],
                  (1 - hintSize[1]) * size[1] / 2 + hintSize[1] * size[1] * indent[1])
    lineSize = hintSize[1] * size[1] * (1 - 2 * indent[1]) / len(creditLines)
    for i in range(len(creditLines)):
        f = font.render(creditLines[i], False, (200, 200, 200))
        surface.blit(f, (lineOffset[0],
                         lineOffset[1] + (lineSize - f.get_size()[1]) / 2 + lineSize * i))

    return (surface, modes["credits"], info)


def menuMode(surface, events, modes, info):
    buttons = [
        "Levels",
        "Help",
        "Credits",
        "Exit"
    ]
    returnModes = [
        modes["levels"],
        modes["help"],
        modes["credits"],
        modes["exit"]
    ]
    indent = info["menu"]["indent"]
    offset = info["menu"]["offset"]
    font = info["menu"]["font"]
    size = surface.get_size()
    buttonSize = (size[0] * (1 - 2 * indent[0]),
                  size[1] * (1 - 2 * indent[1] + offset) / len(buttons) - offset * size[1])

    for event in events:
        if event.type == pg.QUIT:
            return (surface, modes["exit"], info)
        if event.type == pg.MOUSEMOTION:
            pos = event.pos
            if indent[0] * size[0] <= pos[0] <= size[0] * (1 - indent[0]):
                for i in range(len(buttons)):
                    p = size[1] * indent[1] + \
                        (buttonSize[1] + size[1] * offset) * i
                    if p <= pos[1] <= p + buttonSize[1]:
                        info["menu"]["activeButton"] = i
        if event.type == pg.MOUSEBUTTONDOWN:
            pos = event.pos
            if indent[0] * size[0] <= pos[0] <= size[0] * (1 - indent[0]):
                for i in range(len(buttons)):
                    p = size[1] * indent[1] + \
                        (buttonSize[1] + size[1] * offset) * i
                    if p <= pos[1] <= p + buttonSize[1]:
                        return (surface, returnModes[i], info)
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                return (surface, modes["exit"], info)

    surface.fill((0, 0, 0))
    for i in range(len(buttons)):
        p = (size[0] * indent[0], size[1] * indent[1] +
             (buttonSize[1] + size[1] * offset) * i)
        color = info["menu"]["activeButtonBackground"] if i == info["menu"]["activeButton"] else info["menu"]["buttonBackground"]
        pg.draw.rect(surface, color,
                     (p[0], p[1], buttonSize[0], buttonSize[1]))
        f = font.render(buttons[i], False, (200, 200, 200))
        surface.blit(f, (p[0] + (buttonSize[0] - f.get_size()[0]) / 2,
                         p[1] + (buttonSize[1] - f.get_size()[1]) / 2))
    return (surface, modes["menu"], info)


def game(surface):
    modes = {
        "menu": menuMode,
        "win": winMode,
        "lose": loseMode,
        "levels": levelsMode,
        "level": levelMode,
        "exit": exitMode,
        "help": helpMode,
        "credits": creditsMode
    }
    mode = modes["menu"]
    levels = list(map(lambda x: loadLevel("data/maps/" + x),
                      sorted(os.listdir("data/maps"))))
    info = {
        "menu": {
            "activeButtonBackground": (100, 100, 100),
            "activeButton": -1,
            "buttonBackground": (66, 66, 66),
            "indent": (0.2, 0.1),
            "offset": 0.1,
            "font": pg.font.Font('data/font.ttf', 50)
        },
        "levels": {
            "activeButtonBackground": (100, 100, 100),
            "activeButton": -1,
            "buttonBackground": (66, 66, 66),
            "indent": (0.2, 0.1),
            "offset": 0.01,
            "font": pg.font.Font('data/font.ttf', 50),
            "levels": levels
        },
        "help": {
            "size": (0.6, 0.8),
            "indent": (0.1, 0.05),
            "font": pg.font.Font('data/font.ttf', 30),
            "color": (66, 66, 66)
        },
        "credits": {
            "size": (0.6, 0.8),
            "indent": (0.1, 0.05),
            "font": pg.font.Font('data/font.ttf', 30),
            "color": (66, 66, 66)
        },
        "level": {
            "activeButtonBackground": (100, 100, 100),
            "activeButton": -1,
            "buttonBackground": (66, 66, 66),
            "tileSize": 10,
            "camera": (0, 0),
            "zoomDelta": 0.5,
            "zoom": 1.0,
            "menuSize": (1.0, 0.05),
            "menuIndent": (0.02, 0.02),
            "menuOffset": 0.05,
            "font": pg.font.Font('data/font.ttf', 30),
            "level": None,
            "currentLevel": None,
            "mustColoredLevel": None,
            "mustNotColoredLevel": None,
            "coloredLevel": None,
            "cells": -1,
            "activeCell": (-1, -1),
            "moving": False,
            "playing": False,
            "stop": True
        },
        "win": {
            "font": pg.font.Font('data/font.ttf', 50),
        },
        "lose": {
            "font": pg.font.Font('data/font.ttf', 50),
        }
    }
    fps = 30
    clock = pg.time.Clock()
    while True:
        events = []
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            else:
                events.append(event)
        mode = mode(screen.copy(), events, modes, info)
        if mode is None:
            return 0
        surface, mode, info = mode
        screen.blit(surface, (0, 0))
        pg.display.flip()
        clock.tick(fps)


if __name__ == '__main__':
    pg.init()
    pg.font.init()
    pg.display.set_caption("Life is pain.")
    size = width, height = 1280, 720
    screen = pg.display.set_mode(size)
    game(screen)

    running = True
    pg.quit()
