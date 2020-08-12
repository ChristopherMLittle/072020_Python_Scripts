import numpy
from numpy import array
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

from copy import deepcopy

from os import listdir
import gc

import statistics

class Grid:
    def __init__(self, xmin, xmax, ymin, ymax):
        self.xMin = xmin * 1.0
        self.xMax = xmax * 1.0
        self.yMin = ymin * 1.0
        self.yMax = ymax * 1.0


class Gate:
    # num = "0"
    # xPos = 0
    # yPos = 0
    # numNets = 0
    # Nets = []

    def __init__(self, gateNum):
        self.num = gateNum
        self.Nets = []
        self.x = 0
        self.y = 0

    # def __init__(self, gateNum, numNets, netList):
    #     self.num = gateNum
    #     self.Nets = netList

    def add_net(self, net):
        self.Nets.append(net)

    def getNumNets(self):
        return len(self.Nets)

    def __str__(self):
        s = "Gate Num: " + self.num + " Nets: "
        for n in self.Nets:
            s += n.netNum + ", "
        return s

    def get_connected_gates(self):
        gates = []
        #print("Gate " + self.num + " is connected to the nets: ")
        for n in self.Nets:
            #print(str(n))
            for gnum in n.Gates:
                if gnum != self.num: #and not gates.__contains__(gnum):
                    gates.append(gnum)
        #print("Gate " + self.num + " is connected to the gates: " + str(gates))
        return gates

    def get_connected_pads(self):
        pads = []
        for n in self.Nets:
            for p in n.Pads:
                pads.append(p)
                # print("padNum: " + p.padID)
        return pads

    def get_diagonal_value(self):
        return len(self.get_connected_gates()) + len(self.get_connected_pads())

    def deepcopy(self):
        copyGate = Gate(deepcopy(self.num))
        copyGate.x = deepcopy(self.x)
        copyGate.y = deepcopy(self.y)
        for n in self.Nets:
            copyGate.Nets.append(n.deepcopy())
        return copyGate

class Net:
    def __init__(self, netNum):
        self.netNum = netNum
        #self.numGates = 0
        self.Gates = []
        self.Pads = []

    def addGate(self, gateNum):
        self.Gates.append(gateNum)
        #self.numGates += 1

    def __str__(self):
        s = "Net Num: " + self.netNum + " Gates: "
        for g in self.Gates:
            s += g + ", "

        if len(self.Pads) > 0:
            s += " Pads: "
            for p in self.Pads:
                s += str(p)#p.padID + "(" + p.padX + ", " + p.padY + "); "

        s += "; Value: " + str(self.weight())
        return s

    def deepcopy(self):
        copyNet = Net(deepcopy(self.netNum))
        for g in self.Gates:
            copyNet.Gates.append(deepcopy(g))
        if len(self.Pads) > 0:
            for p in self.Pads:
                copyNet.Pads.append(p.deepcopy())
        return copyNet

    def weight(self):
        return ((1.0)/((len(self.Gates) + len(self.Pads))-1))


class Pad:
    def __init__(self, padid, connectednets, padx, pady):
        self.padID = padid
        self.connectedNets = connectednets
        self.padX = padx
        self.padY = pady

    def __str__(self):
        s = ""
        for n in self.connectedNets:
            s += n + ", "
        return self.padID + "(" + str(self.padX) + ", " + str(self.padY) + "); " + "Connected Nets: " + s

    def deepcopy(self):
        nets = []
        for n in self.connectedNets:
            nets.append(deepcopy(n))
        return Pad(deepcopy(self.padID), nets, deepcopy(self.padX), deepcopy(self.padY))

def place(gate_dict, net_dict, pad_dict, grid, step):
    x,y = solve(gate_dict)

    if(step-1 < 0 or len(gate_dict) <= 1):
        for i, xval in enumerate(x):
            gate_dict[list(gate_dict.keys())[i]].x = xval
        for i, yval in enumerate(y):
            gate_dict[list(gate_dict.keys())[i]].y = yval

        return gate_dict

    x_sorted = sorted(x)
    x_median_val = x_sorted[int(len(x) / 2)]
    y_sorted = sorted(y)
    y_median_val = y_sorted[int(len(y) / 2)]
    print("Sorted x values: " + str(x_sorted))
    print("Median x value: " + str(x_sorted[int(len(x) / 2)]))
    print("Sorted y values: " + str(y_sorted))
    print("Median y value: " + str(y_sorted[int(len(y) / 2)]))

    gates_left = {}
    pads_left = {}
    nets_left = {}
    gates_right = {}
    pads_right = {}
    nets_right = {}

    if(step % 2 == 0):
        grid_left = Grid(grid.xMin, grid.xMin + ((grid.xMax - grid.xMin)/2.0), grid.yMin, grid.yMax)
        grid_right = Grid(grid.xMin + ((grid.xMax - grid.xMin)/2.0), grid.xMax, grid.yMin, grid.yMax)
    else:
        grid_left  = Grid(grid.xMin, grid.xMax, grid.yMin, grid.yMin + ((grid.yMax - grid.yMin) / 2.0))
        grid_right = Grid(grid.xMin, grid.xMax, grid.yMin + ((grid.yMax - grid.yMin) / 2.0), grid.yMax)

    for n in net_dict.values():
        nets_left[n.netNum] = n.deepcopy()
        nets_right[n.netNum] = n.deepcopy()

    for p in pad_dict.values():
        p_temp = p.deepcopy()
        pads_left[p.padID] = p.deepcopy()
        pads_right[p.padID] = p.deepcopy()

        if(step % 2 == 0):
            if p_temp.padX < (grid.xMin + ((grid.xMax - grid.xMin)/2.0)): #padX is less than split, move right reference to split
                pads_right[p.padID].padX = (grid.xMin + ((grid.xMax - grid.xMin)/2.0))
                for n in pads_right[p.padID].connectedNets:
                    found = 0
                    foundIdx = 0
                    idx = 0
                    try:
                        for pad in nets_right[n].Pads:
                            if pad.padID == p.padID:
                                found = 1
                                foundIdx = idx
                                break
                            idx += 1
                    except:
                        hi = 2

                    if found == 1:
                        nets_right[n].Pads[foundIdx] = pads_right[p.padID]

            else: #padX is at or greater than split, move left reference to split
                pads_left[p.padID].padX = (grid.xMin + ((grid.xMax - grid.xMin)/2.0))
                for n in pads_left[p.padID].connectedNets:
                    found = 0
                    foundIdx = 0
                    idx = 0
                    try:
                        for pad in nets_left[n].Pads:
                            if pad.padID == p.padID:
                                found = 1
                                foundIdx = idx
                                break
                            idx += 1
                    except:
                        hi = 2

                    if found == 1:
                        nets_left[n].Pads[foundIdx] = pads_left[p.padID]
        else:
            #padY is less than split, move right/up reference to split
            if p_temp.padY < (grid.yMin + ((grid.yMax - grid.yMin) / 2.0)):
                pads_right[p.padID].padY = (grid.yMin + ((grid.yMax - grid.yMin) / 2.0))
                for n in pads_right[p.padID].connectedNets:
                    found = 0
                    foundIdx = 0
                    idx = 0
                    try:
                        for pad in nets_right[n].Pads:
                            if pad.padID == p.padID:
                                found = 1
                                foundIdx = idx
                                break
                            idx += 1
                    except:
                        hi = 2

                    if found == 1:
                        nets_right[n].Pads[foundIdx] = pads_right[p.padID]

            else:
                pads_left[p.padID].padY = (grid.yMin + ((grid.yMax - grid.yMin) / 2.0))
                for n in pads_left[p.padID].connectedNets:
                    found = 0
                    foundIdx = 0
                    idx = 0
                    try:
                        for pad in nets_left[n].Pads:
                            if pad.padID == p.padID:
                                found = 1
                                foundIdx = idx
                                break
                            idx += 1
                    except:
                        hi = 2

                    if found == 1:
                        nets_left[n].Pads[foundIdx] = pads_left[p.padID]

    for g in gate_dict.values():
        if (step % 2 == 0):
            if g.x < x_median_val:  # keep gate left, add pad right
                gates_left[g.num] = g.deepcopy()
                # add pad to right
                tempNets = []
                for n in g.Nets:
                    tempNets.append(deepcopy(n.netNum))
                    try:
                        nets_right[n.netNum].Gates.remove(g.num)
                    except:
                        hi = 2
                pads_right["g" + g.num] = Pad("g" + g.num, tempNets, (grid.xMin + ((grid.xMax - grid.xMin)/2.0)), deepcopy(g.y))
                for n in g.Nets:
                    # n.Gates.remove(g.num)
                    try:
                        nets_right[n.netNum].Pads.append(pads_right["g" + g.num])
                    except:
                        hi = 2

            else:  # move gate right, add pad left
                gates_right[g.num] = g.deepcopy()
                # add pad to left
                tempNets = []
                for n in g.Nets:
                    tempNets.append(deepcopy(n.netNum))
                    try:
                        nets_left[n.netNum].Gates.remove(g.num)
                    except Exception:
                        # print(fileName)
                        # print(str(g))
                        #
                        # print(str(nets_left[n.netNum]))
                        # print(str(n))
                        # raise Exception  # exit# ValueError
                        hi = 2
                pads_left["g" + g.num] = Pad("g" + g.num, tempNets, (grid.xMin + ((grid.xMax - grid.xMin)/2.0)), deepcopy(g.y))
                for n in g.Nets:
                    # n.Gates.remove(g.num)
                    try:
                        nets_left[n.netNum].Pads.append(pads_left["g" + g.num])
                    except:
                        hi = 2
        else:
            if g.y < y_median_val:  # keep gate left, add pad right
                gates_left[g.num] = g.deepcopy()
                # add pad to right
                tempNets = []
                for n in g.Nets:
                    tempNets.append(deepcopy(n.netNum))
                    nets_right[n.netNum].Gates.remove(g.num)
                pads_right["g" + g.num] = Pad("g" + g.num, tempNets, deepcopy(g.x), grid.yMin + ((grid.yMax - grid.yMin) / 2.0))
                for n in g.Nets:
                    # n.Gates.remove(g.num)
                    nets_right[n.netNum].Pads.append(pads_right["g" + g.num])

            else:  # move gate right, add pad left
                gates_right[g.num] = g.deepcopy()
                # add pad to left
                tempNets = []
                for n in g.Nets:
                    tempNets.append(deepcopy(n.netNum))
                    # try:
                    nets_left[n.netNum].Gates.remove(g.num)
                    # except Exception:
                    #     print(fileName)
                    #     print(str(g))
                    #     print(str(n))
                    #     print(str(nets_left[n.netNum]))
                    #     raise Exception  # exit# ValueError
                pads_left["g" + g.num] = Pad("g" + g.num, tempNets, deepcopy(g.x), grid.yMin + ((grid.yMax - grid.yMin) / 2.0))
                for n in g.Nets:
                    # n.Gates.remove(g.num)
                    nets_left[n.netNum].Pads.append(pads_left["g" + g.num])

    print("Step: " + str(step))
    print("gates: " + str(gate_dict.keys()))
    print("gates_left: " + str(gates_left.keys()))
    print("gates_right=: " + str(gates_right.keys()))

    for g in gates_left.values():
        g.Nets = []

    for g in gates_right.values():
        g.Nets = []

    for n in nets_left.values():
        for gnum in n.Gates:
            gates_left[gnum].Nets.append(n)

    for n in nets_right.values():
        for gnum in n.Gates:
            gates_right[gnum].Nets.append(n)

    keyval_left = {}
    valkey_left = {}
    keyval_right = {}
    valkey_right = {}

    idx = 0
    for key in gates_left.keys():
        keyval_left[key] = idx
        valkey_left[idx] = key
        idx += 1

    idx = 0
    for key in gates_right.keys():
        keyval_right[key] = idx
        valkey_right[idx] = key
        idx += 1

    if(len(gates_left) > 0):
        gates_left = place(gates_left, nets_left, pads_left, grid_left, step-1)
    if(len(gates_right) > 0):
        gates_right = place(gates_right, nets_right, pads_right, grid_right, step - 1)

    final_gates = {}

    for g in gates_left.values():
        final_gates[g.num] = g
    for g in gates_right.values():
        final_gates[g.num] = g

    return final_gates


def solve(gate_dict):
    row = []
    col = []
    val = []
    bx = []
    by = []
    gate2idx = {}
    idx2gate = {}
    col_num = 0
    for gate_col in gate_dict.keys():
        gate2idx[gate_col] = col_num
        idx2gate[col_num] = gate_col
        col_num += 1
    gc.collect()

    idx = 0
    for g in gate_dict.values():
        gate_total = 0.0
        gate_bx = 0.0
        gate_by = 0.0
        row_array = []

        for i in range(len(gate_dict)):
            row_array.append(0)

        for net in g.Nets:
            for gate in net.Gates:
                if gate != g.num:
                    gate_total += net.weight()
                    row_array[gate2idx[gate]] -= net.weight()

            for pad in net.Pads:
                gate_total += net.weight()
                gate_bx += net.weight() * pad.padX
                gate_by += net.weight() * pad.padY

        row_array[idx] = gate_total

        for i in range(len(row_array)):
            if(row_array[i] != 0):
                row.append(idx)
                col.append(i)
                val.append(row_array[i])

        # print("gate: " + g.num)
        #gc.collect()

        bx.append(gate_bx)
        by.append(gate_by)
        idx += 1

    print("Row: " + str(row))
    print("Col: " + str(col))
    print("Val: " + str(val))
    print("bx:  " + str(bx))
    print("by:  " + str(by))

    print("Solve matrix...")
    R = array(row)  # row
    C = array(col)  # column
    V = array(val)  # value
    bx_m = array(bx)
    by_m = array(by)

    A = coo_matrix((V, (R, C)))  # , shape=(numGates, numGates))
    print(str(A.todense()))
    # convert to csr format for efficiency
    x = spsolve(A.tocsr(), bx_m)  #
    print("x = ", x)
    y = spsolve(A.tocsr(), by_m)  #
    print("y = ", y)

    for idx in range(len(x)):
        gate_dict[idx2gate[idx]].x = x[idx]
        gate_dict[idx2gate[idx]].y = y[idx]

    return (x,y)


def main():
    # for path in ["benchmarks/3QP/", "benchmarks/8x8 QP/"]:
    #   for f in listdir(path):
        gates = {}
        nets = {}
        pads = {}
        path = "benchmarks/8x8 QP/"
        fileName = "industry2"#f #
        #fileName = ""
        benchmark = open(path + fileName) #open("benchmarks/3QP/toy1")
        print("Opened " + fileName)
        header = benchmark.readline()
        numGates = int(header.split(' ')[0])
        numNets = int(header.split(' ')[1])

        row = []
        col = []
        val = []
        bx = []
        by = []

        print("Number of gates: " + str(numGates))
        print("Number of nets: " + str(numNets))

        for i in range(numNets):
            nets[str(i+1)] = Net(str(i+1))

        print("===")

        for i in range(numGates):
            gateLine = benchmark.readline().replace('\n', '')
            gateLineSplit = gateLine.split(' ')
            gateNum = gateLineSplit[0]

            numNetsConnected = int(gateLineSplit[1])
            #print("Gate: " + gateNum + ", Num Nets Connected: " + str(numNetsConnected))
            gates[gateNum] = Gate(gateNum)

            for j in range(numNetsConnected):
                netNum = gateLineSplit[2+j].replace('\n', '')
                gates[gateNum].add_net(nets[netNum])
                nets[netNum].addGate(gateNum)
                #print("Adding net " + netNum + " Which is represented by: " + str(nets[netNum]))

        #padIndex = 1+numGates+1
        numPads = int(benchmark.readline().split(' ')[0])

        for i in range(numPads):
            padLine = benchmark.readline().replace('\n', '').split()
            padid = "p" + padLine[0]
            padnet = padLine[1]
            padx = float(padLine[2])
            pady = float(padLine[3])
            pads[padid] = Pad(padid, [padnet], padx, pady)
            nets[padnet].Pads.append(pads[padid])

        print("Gates:")
        for g in gates.values():
            print(str(g))
        print("Nets:")
        deleteList = []
        for n in nets.values():
            try:
                print(str(n))
            except:
                deleteList.append(n)
        for i in range(len(deleteList)):
            del nets[deleteList[i].netNum]
        print("Pads:")
        for p in pads.values():
            print(str(p))
        # print(benchmark.readline())

        final_gates = place(gates, nets, pads, Grid(0, 100, 0, 100), 6)

        writeFile = open(fileName, "w")
        print("=========")
        print("RESULTS:")
        print(str(gates.keys()))
        print(str(final_gates.keys()))
        for gate in gates.keys():
            g = final_gates[gate]
            #print(g.num + " " + str(g.x) + " " + str(g.y))
            s = g.num + " " + "{:.8f}".format(g.x) + " " + "{:.8f}".format(g.y)
            print(s)
            writeFile.write(s + "\n")

        writeFile.close()

        benchmark.close()


if __name__ == '__main__':
    main()