import os
import sys
import math
import heapq
import operator
from enum import Enum
from os import listdir

class PredTag(Enum):
    NONE  = "NONE"
    NORTH = "NORTH" # 1
    SOUTH = "SOUTH"# 2
    EAST  = "EAST "# 3
    WEST  = "WEST "# 4
    UP    = "UP   "# 5
    DOWN  = "DOWN "# 6

class Cell:
    def __init__(self, layer, x, y, value):
        self.visited = False
        self.cellcost = int(value) # cellcost
        self.x = x
        self.y = y
        self.layer = int(layer)
        self.north = None
        self.south = None
        self.east = None
        self.west = None
        self.up = None
        self.down = None
        if(self.cellcost == -1):
            #print("Cell (" + str(self.layer) + "," + str(self.x) + "," + str(self.y) + ") is blocked")
            self.isBlocked = True
        else:
            self.isBlocked = False
        self.isSource = False
        self.isTarget = False
        self.predecessor = None
        self.predTag = PredTag.NONE
        self.successor = None
        self.pathcost = 0 #pathcost

    def __str__(self):
        predStr = ""
        succStr = ""
        if(self.predecessor is not None):
            predStr = ", pred: " + str(self.predecessor.layer) + " " + str(self.predecessor.x) + " " + str(self.predecessor.y) + " " + str(self.predTag)
        if(self.successor is not None):
            succStr = ", succ: " + str(self.successor.layer) + " " + str(self.successor.x) + " " + str(self.successor.y)
        return str(self.layer) + " " + str(self.x) + " " + str(self.y) + " Blocked = " + str(self.isBlocked) + " " + predStr + succStr


class Grid:
    def __init__(self, layer, xSize, ySize, bendPenalty, viaPenalty, cellsText):
        self.layer = int(layer)
        self.xSize = int(xSize)
        self.ySize = int(ySize)
        self.bendPenalty = int(bendPenalty)
        self.viaPenalty = int(viaPenalty)

        self.cells = []
        for y, line in enumerate(cellsText):
            cellLine = []
            for x, cell in enumerate(line):
                if(cell != ""):
                    cellLine.append(Cell(layer, x, y, cell))
            self.cells.append(cellLine)

        for y, cellLine in enumerate(self.cells):
            for x, cell in enumerate(cellLine):
                if(x-1 >= 0):
                    cell.west = self.cells[y][x - 1]
                if(x+1 < self.xSize):
                    cell.east = self.cells[y][x + 1]
                if(y-1 >= 0):
                    cell.south = self.cells[y - 1][x]
                if(y+1 < self.ySize):
                    cell.north = self.cells[y + 1][x]

    def __str__(self):
        s = "Size: (" + str(self.xSize) + ", " + str(self.ySize) + "); bendPenalty " + str(self.bendPenalty) + " viaPenalty " + str(self.viaPenalty) + "\r\n"
        for line in self.cells:
            for cell in line:
                s += str(cell.cellcost) + " "

            s += "\r\n"
        return s

class Pin:
    def __init__(self, netID, pinLayer, pinX, pinY):
        self.netID = netID
        self.layer = int(pinLayer)
        self.x = int(pinX)
        self.y = int(pinY)

class Net:
    def __init__(self, netID, pin1, pin2):
        self.netID = netID
        self.pin1 = pin1
        self.pin2 = pin2
        self.distance = abs(pin1.x - pin2.x) + abs(pin1.y - pin2.y)
        self.completed = False

    def __lt__(self, other):
        return self.distance < other.distance

def get_wavefront(cell, bendPenalty, viaPenalty):
    new_wavefront = []
    if (cell.north is not None and not cell.north.isBlocked): #and not cell.north.visited):
        tempCell = cell.north
        tempCost = cell.pathcost + tempCell.cellcost
        tempTag = PredTag.SOUTH
        if (not cell.isSource and tempTag.value != cell.predTag.value):
            tempCost += bendPenalty
        if((not tempCell.visited) or (tempCost < tempCell.pathcost)):
            tempCell.pathcost = tempCost
            tempCell.predecessor = cell
            tempCell.predTag = tempTag
            #cell.successor = tempCell
            new_wavefront.append(cell.north)
    if (cell.south is not None and not cell.south.isBlocked): # and not cell.south.visited):
        tempCell = cell.south
        tempCost = cell.pathcost + tempCell.cellcost
        tempTag = PredTag.NORTH
        if (not cell.isSource and tempTag.value != cell.predTag.value):
            tempCost += bendPenalty
        if ((not tempCell.visited) or (tempCost < tempCell.pathcost)):
            tempCell.pathcost = tempCost
            tempCell.predecessor = cell
            tempCell.predTag = tempTag
            # tempCell.pathcost = cell.pathcost + tempCell.cellcost
            # tempCell.predecessor = cell
            # tempCell.predTag = PredTag.NORTH
            # if (not cell.isSource and cell.predTag != tempCell.predTag):
            #     tempCell.pathcost += bendPenalty
            #cell.successor = tempCell
            new_wavefront.append(cell.south)
    if (cell.east is not None and not cell.east.isBlocked): # and not cell.east.visited):
        tempCell = cell.east
        tempCost = cell.pathcost + tempCell.cellcost
        tempTag = PredTag.WEST
        if (not cell.isSource and tempTag.value != cell.predTag.value):
            tempCost += bendPenalty
        if ((not tempCell.visited) or (tempCost < tempCell.pathcost)):
            tempCell.pathcost = tempCost
            tempCell.predecessor = cell
            tempCell.predTag = tempTag
            # tempCell.pathcost = cell.pathcost + tempCell.cellcost
            # tempCell.predecessor = cell
            # tempCell.predTag = PredTag.WEST
            # if (not cell.isSource and cell.predTag != tempCell.predTag):
            #     tempCell.pathcost += bendPenalty
            #cell.successor = tempCell
            new_wavefront.append(cell.east)
    if (cell.west is not None and not cell.west.isBlocked): # and not cell.west.visited):
        tempCell = cell.west
        tempCost = cell.pathcost + tempCell.cellcost
        tempTag = PredTag.EAST
        if (not cell.isSource and tempTag.value != cell.predTag.value):
            tempCost += bendPenalty
        if ((not tempCell.visited) or (tempCost < tempCell.pathcost)):
            tempCell.pathcost = tempCost
            tempCell.predecessor = cell
            tempCell.predTag = tempTag

            # tempCell.pathcost = cell.pathcost + tempCell.cellcost
            # tempCell.predecessor = cell
            # tempCell.predTag = PredTag.EAST
            # if (not cell.isSource and cell.predTag != tempCell.predTag):
            #     tempCell.pathcost += bendPenalty
            #cell.successor = tempCell
            new_wavefront.append(cell.west)
    if (cell.down is not None and not cell.down.isBlocked): # and not cell.down.visited):
        tempCell = cell.down
        tempCost = cell.pathcost + tempCell.cellcost + viaPenalty
        #tempTag = PredTag.UP
        if ((not tempCell.visited) or (tempCost < cell.pathcost)):
            tempCell.pathcost = tempCost #cell.pathcost + tempCell.cellcost + viaPenalty
            tempCell.predecessor = cell
            tempCell.predTag = PredTag.UP
            #cell.successor = tempCell
            new_wavefront.append(cell.down)
    if (cell.up is not None and not cell.up.isBlocked): # and not cell.up.visited):
        tempCell = cell.up
        tempCost = cell.pathcost + tempCell.cellcost + viaPenalty
        #tempTag = PredTag.DOWN
        if ((not tempCell.visited) or (tempCost < cell.pathcost)):
            tempCell.pathcost = tempCost #cell.pathcost + tempCell.cellcost + viaPenalty
            tempCell.predecessor = cell
            tempCell.predTag = PredTag.DOWN
            #cell.successor = tempCell
            new_wavefront.append(cell.up)

    cell.visited = True

    return new_wavefront

def mark_pathcell(cell):
    if cell.isSource:
        return

    print("mark_pathcell: " + str(cell))

    cell.isBlocked = True
    if (cell.predTag == PredTag.NORTH):
        cell.north.successor = cell
        mark_pathcell(cell.north)
    elif (cell.predTag == PredTag.SOUTH):
        cell.south.successor = cell
        mark_pathcell(cell.south)
    elif (cell.predTag == PredTag.EAST):
        cell.east.successor = cell
        mark_pathcell(cell.east)
    elif (cell.predTag == PredTag.WEST):
        cell.west.successor = cell
        mark_pathcell(cell.west)
    elif (cell.predTag == PredTag.UP):
        cell.up.successor = cell
        mark_pathcell(cell.up)
    elif (cell.predTag == PredTag.DOWN):
        cell.down.successor = cell
        mark_pathcell(cell.down)

    return

def main():
    path = "A4Files/"
    files = ["bench4", "bench5"] # "bench1", "bench2", "bench3",

    testCell1 = Cell(0,0,0,0)
    testCell1.predTag = PredTag.UP
    testCell2 = Cell(0, 0, 0, 0)
    testCell2.predTag = PredTag.DOWN
    testCell3 = Cell(0, 0, 0, 0)
    testCell3.predTag = PredTag.UP

    print(testCell1.predTag != testCell2.predTag)
    print(testCell1.predTag != testCell3.predTag)
    print(testCell1.predTag.value != testCell2.predTag.value)
    print(testCell1.predTag.value != testCell3.predTag.value)
    # return

    for name in files:
        nets = []
        layers = []
        bendPenalty = 0
        viaPenalty = 0
        with open("A4Files/" + name + ".grid", "r") as gridFile:
            # gridFile = open("A4Files/bench1.grid", "r")
            lines = gridFile.readlines()
            vals = list(filter(lambda l: (l != ""), lines[0].strip().split(' ')))
            # if vals.__contains__(""):
            #     vals.remove("")
            lines.remove(lines[0])
            print("File: " + name)
            print("xSize: " + str(vals[0]) + " ySize: " + str(vals[1]))
            numLayers = int(len(lines)/int(vals[1]))
            for i in range(numLayers):
                cellsText = [list(filter(lambda l: (l != ""), line.strip().split())) for line in lines[(i*int(vals[1])):((i+1)*int(vals[1]))]]
                grid = Grid(i+1, vals[0], vals[1], vals[2], vals[3], cellsText)
                layers.append(grid)
            
            for i in range(numLayers):
                for y, yLine in enumerate(layers[i].cells):
                    for x, xCell in enumerate(yLine):
                        if(i-1 >= 0):
                            xCell.down = layers[i-1].cells[y][x]
                        if(i+1 < numLayers):
                            xCell.up = layers[i+1].cells[y][x]

            bendPenalty = int(layers[0].bendPenalty)
            viaPenalty = int(layers[0].viaPenalty)

        with open("A4Files/" + name + ".nl", "r") as netlistFile:
            lines = netlistFile.readlines()
            netNumber = int(list(filter(lambda x: (x!=""), lines[0].strip().split()))[0])
            lines.remove(lines[0])
            for i in range(netNumber):
                vals = list(filter(lambda l: (l != ""), lines[i].strip().split()))
                nets.append(Net(vals[0], Pin(vals[0], vals[1], vals[2], vals[3]), Pin(vals[0], vals[4], vals[5], vals[6])))

        # Mark pins as blocked
        for net in nets:
            tempGrid = layers[net.pin1.layer-1]
            cell = tempGrid.cells[net.pin1.y][net.pin1.x]
            cell.isBlocked = True

            tempGrid = layers[net.pin2.layer-1]
            #print(str(net.pin2.x) + "," + str(net.pin2.y) + " out of " + str(len(tempGrid.cells)) + " " + (str(len(tempGrid.cells))))
            cell = tempGrid.cells[net.pin2.y][net.pin2.x]
            cell.isBlocked = True

        nets.sort()

        # pathfind
        for net in nets:
            wavefront = []

            tempGrid1 = layers[net.pin1.layer-1]
            cell1 = tempGrid1.cells[net.pin1.y][net.pin1.x]
            cell1.pathcost = cell1.cellcost
            cell1.isSource = True
            cell1.isBlocked = False
            print("Cell 1: " + str(cell1))
            wavefront.append(cell1)

            tempGrid2 = layers[net.pin2.layer-1]
            cell2 = tempGrid2.cells[net.pin2.y][net.pin2.x]
            cell2.isTarget = True
            cell2.isBlocked = False
            print("Cell 2 before: " + str(cell2))

            # traverse grid with wavefront
            wavefrontNum = 0
            wavefrontLimit = 10
            try:
                foundTarget = False
                while(not foundTarget):
                    new_wavefront = []
                    mincost = sys.maxsize
                    for cell in wavefront:
                        if(cell.pathcost < mincost):
                            mincost = cell.pathcost

                    for cell in wavefront:
                        if(cell.pathcost != mincost):
                            new_wavefront.append(cell)
                            continue

                        partial_wavefront = get_wavefront(cell, bendPenalty, viaPenalty)
                        for ext_cell in partial_wavefront:
                            if ext_cell.isTarget:
                                foundTarget = True
                                net.completed = True
                                break

                            if not new_wavefront.__contains__(ext_cell):
                                new_wavefront.append(ext_cell)
                        #new_wavefront.extend(partial_wavefront)

                    if(len(new_wavefront) == 0):
                        print("wavefront is empty at level " + str(wavefrontNum))
                        break

                    # print("Wavefront " + str(wavefrontNum) + ": ")
                    # for cell in new_wavefront:
                    #     print("\t" + str(cell))
                    wavefront = new_wavefront
                    wavefrontNum+=1
                    # if(wavefrontNum > wavefrontLimit):
                    #     raise Exception("Wavefront limit reached")
            except Exception as e:
                print(e)

            # finished traverse, preserve path
            print("Cell 1 after: " + str(cell1))
            print("Cell 2 after: " + str(cell2))
            if(net.completed):
                mark_pathcell(cell2)

            cell1.isBlocked = True
            cell2.isBlocked = True

            # finished traverse, clear grid
            for tempGrid in layers:
                for yLine in tempGrid.cells:
                    for xCell in yLine:
                        if(not xCell.isBlocked):
                            xCell.predecessor = None
                            xCell.sucessor = None
                            xCell.visited = False
                            xCell.pathcost = 0

        # format and save output
        if(os.path.exists("A4Files/" + name)):
            os.remove("A4Files/" + name)
        with open("A4Files/" + name, "w") as outFile:
            outFile.write(str(netNumber) + "\n")
            for net in nets:
                outFile.write(net.netID + "\n")
                pin2Cell = layers[net.pin2.layer-1].cells[net.pin2.y][net.pin2.x]
                pin1Cell = layers[net.pin1.layer-1].cells[net.pin1.y][net.pin1.x]
                tempCell = pin1Cell
                foundSource = False
                while(not foundSource):
                    outFile.write(str(tempCell.layer) + " " + str(tempCell.x) + " " + str(tempCell.y) + "\n")
                    if(pin2Cell != tempCell and tempCell.successor is not None):
                        tempCell = tempCell.successor
                        #print("out pred: " + str(tempCell))
                    else:
                        foundSource = True
                outFile.write("0" + "\n")

        print("layers: " + str(len(layers)))
        print("xSize: " + str(len(layers[0].cells[0])))
        print("ySize: " + str(len(layers[0].cells)))
        print("bendPenalty: " + str(layers[0].bendPenalty))
        print("viaPenalty:  " + str(layers[0].viaPenalty))


if __name__ == '__main__':
    main()