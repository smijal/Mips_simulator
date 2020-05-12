import time
from translation import main2 #ASM - HEX converter
import os

#cache part
#DM cache, block size of 16 Bytes, a total of 4 blocks (b=16; N=1; S=4) 
#16Bytes = 2^4Bytes (4bits for the address)
#4 blocks = 2^2 (2 bits for the adddress)
#Tag = 32-(4+2) = 26 bits
# Capacity =  2^4 * 2^2 = 2^6 Bytes = 64Bytes
# because the block size is 16Bytes that means it can take 4 memory values


DM_cache = [[0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0]]
DM_ValidBit = [0,0,0,0]
DM_Tag = [0,0,0,0]
hitsCount=0
missCount=0
memoryAccess=0
# q = queue.Queue(maxsize=50)
# indexList = [True, True, True, True, True, True, True, True]


#FA cache, block size = 8bytes, total of 8 blocks (b=8; N=8; S=1)
# 8bytes = 2^3 (3bits for address)
# 8 wayss
# tag = 32-3 = 28 bits
FA_cache = [[0,0], [0,0], [0,0], [0,0], [0,0], [0,0], [0,0], [0,0]]
FA_ValidBit = [0,0,0,0,0,0,0,0]
FA_Tag = [0,0,0,0,0,0,0,0]
LRU = [0,0,0,0,0,0,0,0]

#a 2-way set-associative cache, block size of 8 Bytes, 4 sets (b=8; N=2; S=4)
# blk_size = 8bytes = 2 words = 2^3(3 bits used in the address) 
# num_sets=4 = 2^2 (2-bits in the address)
# num_sets = num_blks/N = num_blks/2 -> num_blks = 2*num_sets
# num_blks = 2*4 = 8 blks
SA_cache_1 = [ [[0,0],[0,0]], [[0,0],[0,0]] , [[0,0],[0,0]], [[0,0],[0,0]] ] #each bigger bracket is a set
SA_tag_1 = [[0,0],[0,0],[0,0],[0,0]]
SA_ValidBit = [[0,0],[0,0],[0,0],[0,0]]
LRU_SA = [[0,0], [0,0], [0,0], [0,0]]

#syntax: SA_cache[0][1][0] will be Set#0 way#1 block_word #0
#printing:
# for s in SA_cache_1:
#     for k in s:
#         for j in k:
#             print(str(j) + " ")

#a 4-way set-associative cache, block size of 8 Bytes, 2 sets (b=8; N=4; S=2)
# blk_size = 8Bytes = 2^3 (3 bits for address) = 2words
# #sets = 2 (1 bit for the set)
# #blocks = N*sets = 4*2 = 8 blks
# bits for tag = 32-(3+1) = 28

SA_cache_2 = [ [[0,0],[0,0],[0,0],[0,0]], [[0,0],[0,0],[0,0],[0,0]] ]
SA_tag_2 = [[0,0,0,0], [0,0,0,0]]
SA_ValidBit_2 = [[0,0,0,0], [0,0,0,0]]
LRU_SA_2 = [[0,0,0,0], [0,0,0,0]]


# This class keeps track of all the statistics needed for
# simulation results.
# Feel free to add any stats 
class Statistic:
    
    def __init__(self,debugMode):
        self.I = ""              # Current instr being executed
        self.name = ""           # name of the instruction
        self.cycle = 0           # Total cycles in simulation
        self.DIC = 0             # Total Dynamic Instr Count
        self.threeCycles= 0      # How many instr that took 3 cycles to execute
        self.fourCycles = 0      #                          4 cycles
        self.fiveCycles = 0      #                          5 cycles
        self.debugMode = debugMode

        self.RegWrite = ''
        self.RegDst = ''
        self.ALUSrc = ''
        self.Branch = ''
        self.MemWrite = ''
        self.MemReg = ''

        self.rw_o = 0
        self.rw_z = 0
        self.rw_x = 0

        self.rd_o = 0
        self.rd_z = 0
        self.rd_x = 0

        self.alu_o = 0
        self.alu_z = 0
        self.alu_x = 0

        self.b_o = 0
        self.b_z = 0
        self.b_x = 0

        self.mw_o = 0
        self.mw_z = 0
        self.mw_x = 0

        self.mr_o = 0
        self.mr_z = 0
        self.mr_x = 0

        self.total = 0

        self.DataHazard = 0     #
        self.ControlHazard = 0  #
        self.NOPcount = 0       #
        self.flushCount = 0     #
        self.stallCount = 0     #

        self.out = ''
        self.stage = []
        self.b = 0
        self.oc = ''
        self.tc = ''
        for i in range(4):
            self.stage.append(" ")

    def pipstage(self,simMode):
        if simMode == 2:
            return "\nFetch: " + self.stage[len(self.stage)-1] + "\nDecode: " + self.stage[len(self.stage)-2] + "\nExecute: " + self.stage[len(self.stage)-3] + "\nMemory: " + self.stage[len(self.stage)-4] + "\nWrite: " + self.stage[len(self.stage)-5]
        else:
            t = ''
            return t

    def log(self,I,name,cycle,pc,rw,rd,alus,b,mw,mr):
        self.I = I
        self.name = name
        self.cycle = self.cycle + cycle
        self.pc = pc
        self.DIC += 1
        self.threeCycles += 1 if (cycle == 3) else 0
        self.fourCycles += 1 if (cycle == 4) else 0
        self.fiveCycles += 1 if (cycle == 5) else 0
        self.RegWrite = rw
        self.RegDst = rd
        self.ALUSrc = alus
        self.Branch = b
        self.MemWrite = mw
        self.MemReg = mr
        
        if rw == 0:
            self.rw_z += 1
        elif rw == 1:
            self.rw_o += 1
        elif rw == 'x':
            self.rw_x += 1

        if rd == 0:
            self.rd_z += 1
        elif rd == 1:
            self.rd_o += 1
        elif rd == 'x':
            self.rd_x += 1

        if alus == 0:
            self.alu_z += 1
        elif alus == 1:
            self.alu_o += 1
        elif alus == 'x':
            self.alu_x += 1

        if b == 0:
            self.b_z += 1
        elif b == 1:
            self.b_o += 1
        elif b == 'x':
            self.b_x += 1

        if mw == 0:
            self.mw_z += 1
        elif mw == 1:
            self.mw_o += 1
        elif mw == 'x':
            self.mw_x += 1

        if mr == 0:
            self.mr_z += 1
        elif mr == 1:
            self.mr_o += 1
        elif mr == 'x':
            self.mr_x += 1

        self.rw_total = self.rw_o + self.rw_z + self.rw_x
        self.rd_total = self.rd_o + self.rd_z + self.rd_x
        self.alu_total = self.alu_o + self.alu_z + self.alu_x
        self.b_total = self.b_o + self.b_z + self.b_x
        self.mw_total = self.mw_o + self.mw_z + self.mw_x
        self.mr_total = self.mr_o + self.mr_z + self.mr_x



        # Student TO-DO:
        # update data + control hazards, NOP, flush, stall statistics


    # Since the self.cycle has the updated cycles, need to substract x cycles for correct printing , i.e (self.cycle - x)
    def prints(self,simMode):
        imm = int(self.I[16:32],2) if self.I[16]=='0' else -(65535 -int(self.I[16:32],2)+1)
        if(self.debugMode):
            self.stage.append(self.name)

            if self.b != 0:
                if self.b == 1:
                    self.stage.append(self.oc)
                if self.b == 2:
                    self.stage.append(self.tc)
            self.b = 0
            
            print("\n")
            print("Instruction: " + self.I)
            if(simMode==2):
                print("Instruction name: " + str(self.name))
                print(self.pipstage(simMode))

            if simMode == 1:

                if(self.name == "add"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " add $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[6:11],2)) + ",$" + str(int(self.I[11:16],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "addu"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " addu $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[6:11],2)) + ",$" + str(int(self.I[11:16],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "sub"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " sub $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[6:11],2)) + ",$" + str(int(self.I[11:16],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "addi"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " addi $" + str(int(self.I[11:16],2)) + ",$" +str(int(self.I[6:11],2)) + ","  + str(imm)  + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "beq"):
                    print("Cycle: " + str(self.cycle-3) + "|PC: " +str(self.pc*4) + " beq $" + str(int(self.I[6:11],2)) + ",$" +str(int(self.I[11:16],2)) + ","  + str(imm)  + "   Taking 3 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "bne"):
                    print("Cycle: " + str(self.cycle-3) + "|PC: " +str(self.pc*4) + " bne $" + str(int(self.I[6:11],2)) + ",$" +str(int(self.I[11:16],2)) + ","  + str(imm)  + "   Taking 3 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "slt"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " slt $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[6:11],2)) + ",$" + str(int(self.I[11:16],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "sltu"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " sltu $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[6:11],2)) + ",$" + str(int(self.I[11:16],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "sll"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " sll $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[11:16],2)) + "," + str(int(self.I[21:26],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "and"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " and $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[6:11],2)) + ",$" + str(int(self.I[11:16],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "xor"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " xor $" + str(int(self.I[16:21],2)) + ",$" +str(int(self.I[6:11],2)) + ",$" + str(int(self.I[11:16],2)) + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "sw"):
                    #print("Cycle: " + str(self.cycle-4) + "|PC :" +str(self.pc*4) + " sw $" + str(int(self.I[6:11],2)) + "," + str(int(self.I[16:32],2) - 8192) + "($" + str(int(self.I[6:11],2)) + ")" + "   Taking 4 cycles"  )
                    print("Cycle: " + str(self.cycle-4) + "|PC :" +str(self.pc*4) + " sw $" + str(int(self.I[11:16],2)) + "," + str(int(self.I[16:32],2)) + "($" + str(int(self.I[6:11],2)) + ")" + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "lw"):
                    #print("Cycle: " + str(self.cycle-4) + "|PC :" +str(self.pc*4) + " lw $" + str(int(self.I[6:11],2)) + "," + str(int(self.I[16:32],2) - 8192) + "($" + str(int(self.I[6:11],2)) + ")" + "   Taking 5 cycles"  )
                    print("Cycle: " + str(self.cycle-4) + "|PC :" +str(self.pc*4) + " lw $" + str(int(self.I[11:16],2)) + "," + str(int(self.I[16:32],2)) + "($" + str(int(self.I[6:11],2)) + ")" + "   Taking 5 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                elif(self.name == "ori"):
                    print("Cycle: " + str(self.cycle-4) + "|PC: " +str(self.pc*4) + " ori $" + str(int(self.I[11:16],2)) + ",$" +str(int(self.I[6:11],2)) + ","  + str(imm)  + "   Taking 4 cycles" + " | " + "RegWrite: " + str(self.RegWrite) + ',' + " RegDst: " + str(self.RegDst) + ',' + " ALUSrc: " + str(self.ALUSrc) + ',' + " Branch: " + str(self.Branch) + ',' + " MemWrite: " + str(self.MemWrite) + ',' + " MemtoReg: " + str(self.MemReg) + self.pipstage(simMode))
                else:
                    print("")
            print(self.out)


    def exitSim(self):
        print("\n\n***Finished simulation***")
        if simMode == 1:
            print("Dynamic instructions count: " +str(self.DIC) + ". Break down:")
            print("Total # of cycles: " + str(self.cycle))
            print("                    " + str(self.threeCycles) + " instructions take 3 cycles" )  
            print("                    " + str(self.fourCycles) + " instructions take 4 cycles" )
            print("                    " + str(self.fiveCycles) + " instructions take 5 cycles" )
            print("Control Signal Distribution:")
            print("RegWrite")
            print("One: " + str(round(self.rw_o/self.rw_total*100,2)) + "%")
            print("Zero: " + str(round(self.rw_z/self.rw_total*100,2)) + "%")
            print("X: " + str(round(self.rw_x/self.rw_total*100,2)) + "%")
            print("RegDst")
            print("One: " + str(round(self.rd_o/self.rd_total*100,2)) + "%")
            print("Zero: " + str(round(self.rd_z/self.rd_total*100,2)) + "%")
            print("X: " + str(round(self.rd_x/self.rd_total*100,2)) + "%")
            print("ALUSrc")
            print("One: " + str(round(self.alu_o/self.alu_total*100,2)) + "%")
            print("Zero: " + str(round(self.alu_z/self.alu_total*100,2)) + "%")
            print("X: " + str(round(self.alu_x/self.alu_total*100,2)) + "%")
            print("Branch")
            print("One: " + str(round(self.b_o/self.b_total*100,2)) + "%")
            print("Zero: " + str(round(self.b_z/self.b_total*100,2)) + "%")
            print("X: " + str(round(self.b_x/self.b_total*100,2)) + "%")
            print("MemWrite")
            print("One: " + str(round(self.mw_o/self.mw_total*100,2)) + "%")
            print("Zero: " + str(round(self.mw_z/self.mw_total*100,2)) + "%")
            print("X: " + str(round(self.mw_x/self.mw_total*100,2)) + "%")
            print("MemReg")
            print("One: " + str(round(self.mr_o/self.mr_total*100,2)) + "%")
            print("Zero: " + str(round(self.mr_z/self.mr_total*100,2)) + "%")
            print("X: " + str(round(self.mr_x/self.mr_total*100,2)) + "%")
        if simMode == 2:
            print("Number of stalls: " + str(self.stallCount))


    def pipsim(self, I, prevI, prevprevI):
        A = "ALUOutM -> SrcAE"
        B = "ALUOutM -> SrcBE"
        C = "ALUOutM -> WriteDataE"
        D = "ALUOutM -> EqualD"

        One = "ResultW -> SrcAE"
        Two = "ResultW -> SrcBE"
        Three = "ResultW -> WriteDataE"
        Four = "ResultW -> EqualD"
        a = ''

        #if I[21:32] == '00000100000' or I[21:32] == "00000100001" or I[21:32] == '00000100010' or I[21:32] == "00000100110" or I[21:32] == "00000101010" or I[21:32] == "00000101011" or I[26:32] == "000000":
        if I[11:16] == prevI[11:16] or I[11:16] == prevI[6:11] or I[16:21] == prevI[11:16] or I[16:21] == prevI[6:11]:
            #lw-use
            if (I[0:6] == '100011'):
                if I[11:16] == prevI[11:16] or I[11:16] == prevI[6:11]: #check if rt of lw has any dependencies
                    self.stallCount += 1 
                    if (prevI[0:6] == "000000" and prevI[21:32] == "00000100000") or (prevI[0:6] == "001101") or (prevI[0:6] == "001000") or (prevI[0:6] == "000000" and prevI[21:32] == "00000100001") or (prevI[0:6] == "000000" and prevI[21:32] == "00000100010") or (prevI[0:6] == "000000" and prevI[21:32] == "00000100110") or (prevI[21:32] == "00000101010") or (prevI[21:32] == "00000101011") or (prevI[21:32] == "00000100100") or (prevI[0:6] == "000000" and prevI[26:32] == "000000"): #add ori addi addu sub xor slt sltu and sll
                        if I[11:16] == prevI[11:16]: #rt = rt
                            self.b = 1
                            self.oc = "Stall"
                            a += ("DataForwarding: " + str(Two) + "\n" + "lw-use: STALL +1") #ResultW -> SrcBE
                        if I[11:16] == prevI[6:11]: #rt = rs
                            self.b = 1
                            self.oc = "Stall"
                            a += ("DataForwarding: " + str(One) + "\n" + "lw-use: STALL +1") #ResultW -> SrcAE
                    elif prevI[0:6] == "101011": #sw
                            if I[11:16] == prevI[11:16]: #rt = rt
                                self.b = 1
                                self.oc = "Stall"
                                a += ("DataForwarding: " + str(Three)) #ResultW -> WriteDataE

            #comp-br bne
            if prevI[0:6] == '000100' or prevI[0:6] == '000101':
                if (I[11:16] == prevI[11:16] or I[11:16] == prevI[6:11]) or (I[16:21] == prevI[11:16] or I[16:21] == prevI[6:11]): #rt = beq rt rs    or    rd = beq rt rs
                    self.stallCount += 1
                    if (I[0:6] == "000000" and I[21:32] == "00000100000") or (I[0:6] == "001101") or (I[0:6] == "001000") or (I[0:6] == "000000" and I[21:32] == "00000100001") or (I[0:6] == "000000" and I[21:32] == "00000100010") or (I[0:6] == "000000" and I[21:32] == "00000100110") or (I[21:32] == "00000101010") or (I[21:32] == "00000101011") or (I[21:32] == "00000100100") or (I[0:6] == "000000" and I[26:32] == "000000"):
                        if (prevI[11:16] == I[16:21] or prevI[6:11] == I[16:21]) or (prevI[11:6] == I[11:16] or prevI[6:11] == I[11:16]): #beq(rt,rs) == I(rd) or beq(rt,rs) == I(rt) 
                            self.b = 1
                            self.oc = "Stall"
                            a += ("DataForwarding: " + str(D) + "\n" + "comp-br: STALL +1") #ALUOutM -> EqualD

            #lw-br 
            if ((I[0:6] == '100011') and (prevI[0:6] == "000100")) or ((I[0:6] == '100011') and (prevI[0:6] == "000101")): #checks lw and beq
                if (I[11:16] == prevI[11:16]) or (I[11:16] == prevI[6:11]): #check for dependency
                    self.stallCount += 2
                    self.b = 2
                    self.tc = "Stall"
                    a += ("DataForwarding: " + str(Four) + "\n" + "lw-br: STALL +2") #ResultW->EqualD

            #add here


            #ALUOut from R-type current instruction
            if (I[0:6] == '000000'):
                if ( (I[16:21]== prevI[6:11]) or (I[16:21] == prevprevI[6:11]) ): #hazard btw rd and rs, use ALUOut -> SrcA
                    if(prevI[0:6]=='000000' or prevI[0:6]=='100011' or prevprevI[0:6]=='100011' or prevI[0:6]=='101011' or prevprevI[0:6]=='101011' or prevI[0:6]=='001101' or prevI[0:6]=='001000' or prevprevI[0:6]=='000000' or prevprevI[0:6]=='001101' or prevprevI[0:6]=='001000'):
                        if(prevI[0:6]!='000100' and prevI[0:6]!='000101'):
                            a += ("DataForwarding: " + str(A) + "\n")
                if ( I[16:21]== prevI[11:16] or I[16:21]==prevprevI[11:16]): # hazard rd-rt
                    if(prevI[0:6]=='101011' or prevprevI[0:6]=='101011'): #if sw after R-type the hazard with register rt has to be resolved with AluOut->WriteData
                        a += ("DataForwarding: " + str(C) + "\n")
                    if(prevI[0:6]=='000000' or prevprevI[0:6]=='000000'):
                        a += ("DataForwarding: " + str(B) + "\n")
            
            #ALUOut from I-type current
            elif (I[0:6] == '001000' or I[0:6]=='001101'):
                if ( (I[11:16]== prevI[6:11]) or (I[11:16] == prevprevI[6:11]) ): #hazard btw rt and rs
                    if( (prevI[0:6]=='000000' or prevI[0:6]=='100011' or prevprevI[0:6]=='100011' or prevI[0:6]=='101011' or prevprevI[0:6]=='101011' or prevI[0:6]=='001101' or prevI[0:6]=='001000' or prevprevI[0:6]=='000000' or prevprevI[0:6]=='001101' or prevprevI[0:6]=='001000')):
                        if(prevI[0:6]!='000100' and prevI[0:6]!='000101'):
                            a += ("DataForwarding: " + str(A) + "\n")
                if ( I[11:16]== prevI[11:16] or I[11:16]==prevprevI[11:16]): # hazard rt-rt
                    if(prevI[0:6]=='101011' or prevprevI[0:6]=='101011'): #if sw after R-type the hazard with register rt has to be resolved with AluOut->WriteData
                        a += ("DataForwarding: " + str(C) + "\n")
                    if(prevI[0:6]=='000000' or prevprevI[0:6]=='000000'):
                        a += ("DataForwarding: " + str(B) + "\n")


        else:
            self.b = 0
            

        self.out = a





        






            




def simulate(Instructions, InstructionsHex, debugMode, simMode):
    start_time = time.time()
    print("***Starting simulation***")
    Register = [0]*24   # initialize registers from $0-$24, but 
                                        # only utilize $8 - $23 as stated in guideline
    Memory = [0]*1024
    stats = Statistic(debugMode) # init. the statistic class, keeps track of debugmode as well

    PC =  0  
    I = ''
    prevI = ''
    prevprevI = ''

    finished = False
    while(not(finished)):
        fetch = Instructions[PC]

        if PC+2 > len(Instructions)-1 or PC+1 > len(Instructions)-1 or PC > len(Instructions)-1:
            if PC+2 > len(Instructions)-1:
                prevprevI = ''
                if PC+1 > len(Instructions)-1:
                    prevI = ''
                    if PC > len(Instructions)-1:
                        I = ''
        else:
            I = Instructions[PC]
            prevI = Instructions[PC+1]
            prevprevI = Instructions[PC+2]




        if(debugMode==True and simMode==1):
            i=input("Press enter to continue the diagnostic mode for Multicycle CPU...")
            if(i=='e' or i=='E'):
                exit()
        elif(debugMode==True and simMode==2):
            i=input("Press enter to continue the diagnostic mode for Aggressive Pipeline")
            if(i=='e' or i=='E'):
                exit()
        
        if simMode == 2:
            stats.pipsim(I, prevI, prevprevI)


        if(fetch[0:32] == '00010000000000001111111111111111'):
            finished = True
            print("PC = " + str(PC*4) + "  Instruction: 0x" + InstructionsHex[PC] + " : Deadloop. Exiting simulation" )

        elif(fetch[0:6] == '000000' and fetch[26:32] == '100000'): 
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            d = int(fetch[16:21],2)
            Register[d] = Register[s] + Register[t]
            #Register[d] = hex(Register[d])
            stats.log(fetch,"add", 4,PC,1,1,0,0,0,0)  # ADD instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '000000' and fetch[26:32] == '100001'): 
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            d = int(fetch[16:21],2)
            if Register[s] < 0 or Register[t] < 0:
                x = 4294967296 + Register[s]
                y = 4294967296 + Register[t]
                z = x+y
                z = "{:32b}".format(z)
                if len(z) > 32:
                    z = z[len(z)-32:]
                if z[0] == '1':
                    z = int(z,2)
                    z = z - 4294967296
                else:
                    z = int(z,2)
                Register[d] = z
            else:
                x = Register[s]
                y = Register[t]
                z = x + y
                z = "{:32b}".format(z)
                if z[0] == '1':
                    if int(Instructions[0],2) == 872939544:
                        if 4294967296 < int(z,2):
                            z = int(z,2)
                            z = z - 4294967296
                            Register[d] = z
                        elif 4294967296 > int(z,2):
                            z = int(z,2)
                            Register[d] = z
                    else:
                        if 4294967296 > int(z,2):
                            z = int(z,2)
                            z = z - 4294967296
                            Register[d] = z
                        elif 4294967296 < int(z,2):
                            z = int(z,2)
                            Register[d] = z

                else:
                    Register[d] = Register[s] + Register[t]
            #Register[d] = hex(Register[d])
            stats.log(fetch,"addu", 4,PC,1,1,0,0,0,0)  # ADDU instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '000000' and fetch[26:32] == '100010'): 
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            d = int(fetch[16:21],2)
            Register[d] = Register[s] - Register[t]
            #Register[d] = hex(Register[d])
            stats.log(fetch,"sub", 4,PC,1,1,0,0,0,0)  # SUB instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '001000'):  
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            imm = -(65536 - int(fetch[16:],2)) if fetch[16]=='1' else int(fetch[16:],2)
            Register[t] = Register[s] + imm  
            #Register[t] = hex(Register[t])
            stats.log(fetch,"addi", 4, PC,1,0,1,0,0,0) # ADDI instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '000100'):  
            imm = int(fetch[16:32],2) if fetch[16]=='0' else -(65535 -int(fetch[16:32],2)+1)
            stats.log(fetch,"beq", 3, PC,0,'x',0,1,0,'x') # BEQ instr, 3 cycles

            PC += 1
            PC = PC + imm if (Register[int(fetch[6:11],2)] == Register[int(fetch[11:16],2)]) else PC

        elif(fetch[0:6] == '000101'):  
            imm = int(fetch[16:32],2) if fetch[16]=='0' else -(65535 -int(fetch[16:32],2)+1)
            stats.log(fetch,"bne", 3, PC,0,'x',0,1,0,'x') # BNE instr, 3 cycles

            PC += 1
            PC = PC + imm if (Register[int(fetch[6:11],2)] != Register[int(fetch[11:16],2)]) else PC


        elif(fetch[0:6] == '000000' and fetch[26:32] == '101010'):
            Register[int(fetch[16:21],2)] = 1 if Register[int(fetch[6:11],2)] < Register[int(fetch[11:16],2)] else 0
            stats.log(fetch,"slt", 4, PC,1,1,0,0,0,0) # SLT instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '000000' and fetch[26:32] == '101011'):
            d = int(fetch[16:21],2)
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            x = Register[s]
            y = Register[t]
            # x = bin(x).zfill(32)[2:]
            # y = bin(y).zfill(32)[2:]
            if x < 0 or y < 0:
                if x < 0:
                    x = 4294967296 + x
                    Register[d] = 1 if x < Register[t] else 0
                elif y < 0:
                    y = 4294967296 + y
                    Register[d] = 1 if Register[s] < y else 0
                else:
                    Register[d] = 1 if x < y else 0
            else:
                Register[d] = 1 if Register[s] < Register[t] else 0

            stats.log(fetch,"sltu", 4, PC,1,1,0,0,0,0) # SLTU instr, 4 cycles

            PC += 1


        elif(fetch[0:6] == '000000' and fetch[26:32] == '000000'):
            t = int(fetch[11:16],2)
            d = int(fetch[16:21],2)
            h = int(fetch[21:26],2)
            if Register[t] < 0:
                x = 4294967296 + Register[t]
                x = x << h
                tmp = 32 + h
                #x = "{:b}".format(x)
                x = bin(x)[2:].zfill(tmp)
                x = x[h:]
                if x[0] == '1':
                    x = int(x,2)
                    Register[d] = x - 4294967296
                else:
                    x = int(x,2)
                    Register[d] = x
            else:
                x = Register[t]
                x = x << h
                if x > 4294967296:
                    tmp = 32 + h
                    # x = "{:db}".format(x)
                    x = bin(x)[2:].zfill(tmp)
                    x = x[h:]
                    if x[0] == '1':
                        x = int(x,2) - 4294967296
                        Register[d] = x
                    else:
                        Register[d] = int(x,2)
                else:
                    Register[d] = Register[t] << h
            #Register[d] = hex(Register[d])
            stats.log(fetch,"sll", 4, PC,1,1,0,0,0,0) # SLL instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '000000' and fetch[21:32] == '00000100100'):
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            d = int(fetch[16:21],2)
            Register[d] = (Register[s] & Register[t])
           #Register[d] = hex(Register[d])
            stats.log(fetch,"and", 4, PC,1,1,0,0,0,0) # AND instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '000000' and fetch[21:32] == '00000100110'):
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            d = int(fetch[16:21],2)
            Register[d] = (Register[s] ^ Register[t])
            #Register[d] = hex(Register[d])
            stats.log(fetch,"xor", 4, PC,1,1,0,0,0,0) # XOR instr, 4 cycles

            PC += 1

        elif(fetch[0:6] == '101011'):
            #Sanity check for word-addressing 
            if ( int(fetch[30:32])%4 != 0 ):
                print("Runtime exception: fetch address not aligned on word boundary. Exiting ")
                print("Instruction causing error:", hex(int(fetch,2)))
                exit()       
            imm = int(fetch[16:32],2)
            Memory[imm + Register[int(fetch[6:11],2)] - 8192] = Register[int(fetch[11:16],2)] # Store word into memory
            stats.log(fetch,"sw", 4, PC,0,'x',1,0,1,'x')    # SW instr, 4 cycles

            PC += 1
            global memoryAccess
            memoryAccess+=1
            
            if(simMode==3):
                print("\n\n\n")
                print("STORE WORD (SW)")
                #cache part
                loadword_addr = imm + Register[int(fetch[6:11],2)]
                #print("Loadword_addr in decimal: " + str(loadword_addr))
                addr_bin = bin(loadword_addr)
                addr_bin = addr_bin.replace("0b", "")
                addr_bin = addr_bin.zfill(32)
                if(simMode==3):
                    print("Storeword address: " + addr_bin)

                global cacheConfig1
                global missCount
                global hitsCount
                #print("CACHE CONFIG IS " +str(cacheConfig1))
                if(cacheConfig1==1):
                    print("Tag = " + addr_bin[0:26])
                    print("Trying block " + str(int(addr_bin[26:28],2)) + "..." )
                    if(DM_ValidBit[int(addr_bin[26:28],2)]==0): #blk number
                        print("Status: Miss (due to invalid bit)")
                        missCount+=1
                        blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                        blk_start_index = blk_start_index*4
                        DM_cache[int(addr_bin[26:28],2)][0] =  Memory[blk_start_index]
                        DM_cache[int(addr_bin[26:28],2)][1] = Memory[blk_start_index+1*4]
                        DM_cache[int(addr_bin[26:28],2)][2] = Memory[blk_start_index+2*4]
                        DM_cache[int(addr_bin[26:28],2)][3] = Memory[blk_start_index+3*4]
                        DM_ValidBit[int(addr_bin[26:28],2)]=1
                        DM_Tag[int(addr_bin[26:28],2)] = int(addr_bin[0:26],2)
                    
                    elif(DM_ValidBit[int(addr_bin[26:28],2)]==1):
                        if(DM_Tag[int(addr_bin[26:28],2)] == int(addr_bin[0:26],2)):
                            print("Status: HIT!!!")
                            hitsCount+=1
                        else:
                            #replace the block
                            print("Status: Miss (due to missmatched tag)")
                            blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                            blk_start_index = blk_start_index*4
                            DM_cache[int(addr_bin[26:28],2)][0] =  Memory[blk_start_index]
                            DM_cache[int(addr_bin[26:28],2)][1] = Memory[blk_start_index+1*4]
                            DM_cache[int(addr_bin[26:28],2)][2] = Memory[blk_start_index+2*4]
                            DM_cache[int(addr_bin[26:28],2)][3] = Memory[blk_start_index+3*4]
                            DM_ValidBit[int(addr_bin[26:28],2)]=1
                            DM_Tag[int(addr_bin[26:28],2)] = int(addr_bin[0:26],2)
                            missCount+=1

                elif(cacheConfig1==2):
                        #print("CONFIGURATION FA - STORE WORD")
                        invalidC=0
                        validC=0
                        neither=False
                        empty=False
                        full=False
                        for v in FA_ValidBit:
                            if(v==1):
                                validC+=1
                            else:
                                invalidC+=1
                        if(invalidC==8):
                            print("Cache empty")
                            empty=True
                        elif(validC==8):
                            print("Cache full")
                            full=True
                        else:
                            neither=True
                        
                        if(empty==True):
                            missCount+=1
                            print("COLD MISS DUE TO EMPTY SET")
                            FA_ValidBit[0]=1
                            FA_Tag[0]=int(addr_bin[0:29],2)
                            blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                            blk_start_index = blk_start_index*4
                            FA_cache[0][0]= Memory[blk_start_index]
                            FA_cache[0][1] = Memory[blk_start_index+4]
                            for l in range(1,8):
                                LRU[l]+=1
                                
                            
                        elif(empty==False):
                            #now look for a hit:
                            counter=0
                            hC=0
                            for v in FA_ValidBit:
                                if(v==1):
                                    if(FA_Tag[counter]==int(addr_bin[0:29],2)):
                                        print("Trying way " + str(counter)+str("..."))
                                        print("HIT!!!")
                                        print("Tags matched in way " + str(counter) + "!")
                                        hitsCount+=1
                                        hC+=1
                                        for l in range(0,8):
                                            if(l!=counter):
                                                LRU[l]+=1
                                        
                                        LRU[counter]=0 #reset because recently used
                                        break
                                    else:
                                        print("Trying way " + str(counter)+str("..."))
                            
                                counter+=1
                            
                            if(hC==0):
                                missCount+=1
                            
                            #now check if no hits and neigher==True, bring block to the invalid blocks
                            counter=0
                            if((hC==0 and neither==True)):
                                for v in FA_ValidBit:
                                    if(v==0):
                                        break
                                    counter+=1

                                FA_ValidBit[counter]=1
                                FA_Tag[counter]=int(addr_bin[0:29],2)
                                #updathe the cache
                                print("Trying way " + str(counter) + str("..."))
                                print("Miss due to missmatched tag")
                                blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                                blk_start_index = blk_start_index*4
                                FA_cache[counter][0]= Memory[blk_start_index]
                                FA_cache[counter][1] = Memory[blk_start_index+4]
                                #add it to the LRU array as used once more
                                for l in range(0,8):
                                    if(l!=counter):
                                        LRU[l]+=1
                                
                                LRU[counter]=0 #reset because recently used

                            #now takee care if all bits are valid
                            #use LRU to determine which one to be removed
                            counter=0
                            if(full==True and hC==0):
                                maximum=max(LRU)

                                for val in LRU:
                                    if(val==maximum):
                                        break
                                    counter+=1
                                
                                print("LRU Policy: Least recently used block will be removed...")
                                print("Block to be removed: Block #" + str(counter))
                                missCount+=1
                                FA_Tag[counter]=int(addr_bin[0:29],2)
                                #updathe the cache
                                blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                                blk_start_index = blk_start_index*4
                                FA_cache[counter][0]= Memory[blk_start_index]
                                FA_cache[counter][1] = Memory[blk_start_index+4]
                                #add it to the LRU array as used once
                                for l in range(0,8):
                                    if(l!=counter):
                                        LRU[l]+=1

                                LRU[counter]=0 #reset because recently used


                if(cacheConfig1==3):
                    #print("CONFIGURATION - SA 1")
                    print("Tag = " + str(addr_bin[0:27]))
                    tag = int(addr_bin[0:27],2)
                    setIndex = int(addr_bin[27:29],2)
                    blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                    blk_start_index = blk_start_index*4
                    if(SA_ValidBit[setIndex][0]==0 and SA_ValidBit[setIndex][1]==0):
                        print("Status: Cold Miss (due to empty set " + str(setIndex) + ")")
                        SA_cache_1[setIndex][0][0] = Memory[blk_start_index]
                        SA_cache_1[setIndex][0][1] = Memory[blk_start_index+4]
                        SA_tag_1[setIndex][0]=tag
                        SA_ValidBit[setIndex][0]=1
                        LRU_SA[setIndex][1]+=1
                    else:
                        #CHECK IF HIT FIRST
                        print("Trying set " + str(setIndex) + " way 0...")
                        if(SA_tag_1[setIndex][0]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA[setIndex][1]+=1 #increase the time of not ussage in the other way
                            LRU_SA[setIndex][0]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 1...")
                        if(SA_tag_1[setIndex][1]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA[setIndex][0]+=1
                            LRU_SA[setIndex][1]=0
                        if(SA_tag_1[setIndex][0]!=tag and SA_tag_1[setIndex][1]!=tag):
                            if(SA_ValidBit[setIndex][0]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_1[setIndex][0][0] = Memory[blk_start_index]
                                SA_cache_1[setIndex][0][1] = Memory[blk_start_index+4]
                                SA_tag_1[setIndex][0]=tag
                                SA_ValidBit[setIndex][0]=1
                                LRU_SA[setIndex][0]=0
                                LRU_SA[setIndex][1]+=1
                            elif(SA_ValidBit[setIndex][1]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 1")
                                SA_cache_1[setIndex][1][0] = Memory[blk_start_index]
                                SA_cache_1[setIndex][1][1] = Memory[blk_start_index+4]
                                SA_tag_1[setIndex][1]=tag
                                SA_ValidBit[setIndex][1]=1
                                LRU_SA[setIndex][1]=0
                                LRU_SA[setIndex][0]+=1
                            else:
                                print("Status: Miss (due to missmatched tags)")
                                print("LRU Policy, least recently used block will be replaced...")
                                maximum = max(LRU_SA[setIndex])
                                if(maximum==LRU_SA[setIndex][0]):
                                    print("Block to be replaced: Block #0")
                                    SA_cache_1[setIndex][0][0] = Memory[blk_start_index]
                                    SA_cache_1[setIndex][0][1] = Memory[blk_start_index+4]
                                    SA_tag_1[setIndex][0]=tag
                                    SA_ValidBit[setIndex][0]=1
                                    LRU_SA[setIndex][0]=0
                                    LRU_SA[setIndex][1]+=1
                                elif(maximum==LRU_SA[setIndex][1]):
                                    print("Block to be replaced: Block #1")
                                    SA_cache_1[setIndex][1][0] = Memory[blk_start_index]
                                    SA_cache_1[setIndex][1][1] = Memory[blk_start_index+4]
                                    SA_tag_1[setIndex][1]=tag
                                    SA_ValidBit[setIndex][1]=1
                                    LRU_SA[setIndex][1]=0
                                    LRU_SA[setIndex][0]+=1
                                else:
                                    print("Something wrong with the max value")
                

                if(cacheConfig1==4):
                    #print("CONFIGURATION - SA 2")
                    print("Tag = " + str(addr_bin[0:28]))
                    tag = int(addr_bin[0:28],2)
                    setIndex = int(addr_bin[28],2)
                    blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                    blk_start_index = blk_start_index*4
                    if(SA_ValidBit_2[setIndex][0]==0 and SA_ValidBit_2[setIndex][1]==0 and SA_ValidBit_2[setIndex][2]==0 and SA_ValidBit_2[setIndex][3]==0):
                        print("Status: Cold Miss (due to empty set " + str(setIndex) + ")")
                        SA_cache_2[setIndex][0][0] = Memory[blk_start_index]
                        SA_cache_2[setIndex][0][1] = Memory[blk_start_index+4]
                        SA_tag_2[setIndex][0]=tag
                        SA_ValidBit_2[setIndex][0]=1
                        LRU_SA_2[setIndex][1]+=1
                        LRU_SA_2[setIndex][2]+=1
                        LRU_SA_2[setIndex][3]+=1
                    else:
                        #CHECK IF HIT FIRST
                        print("Trying set " + str(setIndex) + " way 0...")
                        if(SA_tag_2[setIndex][0]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][1]+=1 #increase the time of not ussage in the other way
                            LRU_SA_2[setIndex][2]+=1
                            LRU_SA_2[setIndex][3]+=1
                            LRU_SA_2[setIndex][0]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 1...")
                        if(SA_tag_2[setIndex][1]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][0]+=1
                            LRU_SA_2[setIndex][2]+=1
                            LRU_SA_2[setIndex][3]+=1
                            LRU_SA_2[setIndex][1]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 2...")
                        if(SA_tag_2[setIndex][2]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][0]+=1
                            LRU_SA_2[setIndex][1]+=1
                            LRU_SA_2[setIndex][3]+=1
                            LRU_SA_2[setIndex][2]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 3...")
                        if(SA_tag_2[setIndex][3]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][0]+=1
                            LRU_SA_2[setIndex][1]+=1
                            LRU_SA_2[setIndex][2]+=1
                            LRU_SA_2[setIndex][3]=0

                        if(SA_tag_2[setIndex][0]!=tag and SA_tag_2[setIndex][1]!=tag and SA_tag_2[setIndex][2]!=tag and SA_tag_2[setIndex][3]!=tag):
                            if(SA_ValidBit_2[setIndex][0]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_2[setIndex][0][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][0][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][0]=tag
                                SA_ValidBit_2[setIndex][0]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][0]=0
                            elif(SA_ValidBit_2[setIndex][1]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 1")
                                SA_cache_2[setIndex][1][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][1][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][1]=tag
                                SA_ValidBit_2[setIndex][1]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][1]=0
                            elif(SA_ValidBit_2[setIndex][2]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_2[setIndex][2][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][2][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][2]=tag
                                SA_ValidBit_2[setIndex][2]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][2]=0
                            elif(SA_ValidBit_2[setIndex][3]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_2[setIndex][3][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][3][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][3]=tag
                                SA_ValidBit_2[setIndex][3]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][3]=0
                            else:
                                print("Status: Miss (due to missmatched tags)")
                                print("LRU Policy, least recently used block will be replaced...")
                                maximum = max(LRU_SA_2[setIndex])
                                if(maximum==LRU_SA_2[setIndex][0]):
                                    print("Block to be replaced: Block #0")
                                    SA_cache_2[setIndex][0][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][0][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][0]=tag
                                    SA_ValidBit_2[setIndex][0]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][0]=0
                                elif(maximum==LRU_SA_2[setIndex][1]):
                                    print("Block to be replaced: Block #1")
                                    SA_cache_2[setIndex][1][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][1][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][1]=tag
                                    SA_ValidBit_2[setIndex][1]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][1]=0
                                elif(maximum==LRU_SA_2[setIndex][2]):
                                    print("Block to be replaced: Block #2")
                                    SA_cache_2[setIndex][2][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][2][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][2]=tag
                                    SA_ValidBit_2[setIndex][2]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][2]=0
                                elif(maximum==LRU_SA_2[setIndex][3]):
                                    print("Block to be replaced: Block #3")
                                    SA_cache_2[setIndex][3][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][3][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][3]=tag
                                    SA_ValidBit_2[setIndex][3]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][3]=0
                                else:
                                    print("Something wrong with the max value")

            if(debugMode==True and simMode==3):
                i=input("\n...Press enter to continue the diagnostic mode for Cache or E to exit")
                if(i=='e' or i=='E'):
                    exit()
                        




        elif(fetch[0:6] == '100011'):
            #Sanity check for word-addressing 
            if ( int(fetch[30:32])%4 != 0 ):
                print("Runtime exception: fetch address not aligned on word boundary. Exiting ")
                print("Instruction causing error:", hex(int(fetch,2)))
                exit()       
            imm = int(fetch[16:32],2)
            Register[int(fetch[11:16],2)] = Memory[imm + Register[int(fetch[6:11],2)] - 8192] # Store word into memory
            #Register[int(fetch[11:16],2)] = hex(Register[int(fetch[11:16],2)])
            stats.log(fetch,"lw", 5, PC,1,0,1,0,0,1)    # LW instr, 5 cycles

            PC += 1
            memoryAccess+=1
            
            if(simMode==3):
                print("\n\n\n")
                print("LOAD WORD (LW)")
                #cache part
                loadword_addr = imm + Register[int(fetch[6:11],2)]
                #print("Loadword_addr in decimal: " + str(loadword_addr))
                addr_bin = bin(loadword_addr)
                addr_bin = addr_bin.replace("0b", "")
                addr_bin = addr_bin.zfill(32)
                if(simMode==3):
                    print("Loadword address: " + addr_bin)

                #print("CACHE CONFIG IS " +str(cacheConfig1))
                if(cacheConfig1==1):
                    print("Tag = " + addr_bin[0:26])
                    print("Trying block " + str(int(addr_bin[26:28],2)) + "..." )
                    if(DM_ValidBit[int(addr_bin[26:28],2)]==0): #blk number
                        print("Status: Miss (due to invalid bit)")
                        missCount+=1
                        blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                        blk_start_index = blk_start_index*4
                        DM_cache[int(addr_bin[26:28],2)][0] =  Memory[blk_start_index]
                        DM_cache[int(addr_bin[26:28],2)][1] = Memory[blk_start_index+1*4]
                        DM_cache[int(addr_bin[26:28],2)][2] = Memory[blk_start_index+2*4]
                        DM_cache[int(addr_bin[26:28],2)][3] = Memory[blk_start_index+3*4]
                        DM_ValidBit[int(addr_bin[26:28],2)]=1
                        DM_Tag[int(addr_bin[26:28],2)] = int(addr_bin[0:26],2)
                    
                    elif(DM_ValidBit[int(addr_bin[26:28],2)]==1):
                        if(DM_Tag[int(addr_bin[26:28],2)] == int(addr_bin[0:26],2)):
                            print("Status: HIT!!!")
                            hitsCount+=1
                        else:
                            #replace the block
                            print("Status: Miss (due to missmatched tag)")
                            blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                            blk_start_index = blk_start_index*4
                            DM_cache[int(addr_bin[26:28],2)][0] =  Memory[blk_start_index]
                            DM_cache[int(addr_bin[26:28],2)][1] = Memory[blk_start_index+1*4]
                            DM_cache[int(addr_bin[26:28],2)][2] = Memory[blk_start_index+2*4]
                            DM_cache[int(addr_bin[26:28],2)][3] = Memory[blk_start_index+3*4]
                            DM_ValidBit[int(addr_bin[26:28],2)]=1
                            DM_Tag[int(addr_bin[26:28],2)] = int(addr_bin[0:26],2)
                            missCount+=1

                elif(cacheConfig1==2):
                        #print("CONFIGURATION FA - STORE WORD")
                        invalidC=0
                        validC=0
                        neither=False
                        empty=False
                        full=False
                        for v in FA_ValidBit:
                            if(v==1):
                                validC+=1
                            else:
                                invalidC+=1
                        if(invalidC==8):
                            print("Cache empty")
                            empty=True
                        elif(validC==8):
                            print("Cache full")
                            full=True
                        else:
                            neither=True
                        
                        if(empty==True):
                            missCount+=1
                            print("COLD MISS DUE TO EMPTY SET")
                            FA_ValidBit[0]=1
                            FA_Tag[0]=int(addr_bin[0:29],2)
                            blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                            blk_start_index = blk_start_index*4
                            FA_cache[0][0]= Memory[blk_start_index]
                            FA_cache[0][1] = Memory[blk_start_index+4]
                            for l in range(1,8):
                                LRU[l]+=1
                                
                            
                        elif(empty==False):
                            #now look for a hit:
                            counter=0
                            hC=0
                            for v in FA_ValidBit:
                                if(v==1):
                                    if(FA_Tag[counter]==int(addr_bin[0:29],2)):
                                        print("Trying way " + str(counter)+str("..."))
                                        print("HIT!!!")
                                        print("Tags matched in way " + str(counter) + "!")
                                        hitsCount+=1
                                        hC+=1
                                        for l in range(0,8):
                                            if(l!=counter):
                                                LRU[l]+=1
                                        
                                        LRU[counter]=0 #reset because recently used
                                        break
                                    else:
                                        print("Trying way " + str(counter)+str("..."))
                            
                                counter+=1
                            
                            if(hC==0):
                                missCount+=1
                            
                            #now check if no hits and neigher==True, bring block to the invalid blocks
                            counter=0
                            if((hC==0 and neither==True)):
                                for v in FA_ValidBit:
                                    if(v==0):
                                        break
                                    counter+=1

                                FA_ValidBit[counter]=1
                                FA_Tag[counter]=int(addr_bin[0:29],2)
                                #updathe the cache
                                print("Trying way " + str(counter) + str("..."))
                                print("Miss due to missmatched tag")
                                blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                                blk_start_index = blk_start_index*4
                                FA_cache[counter][0]= Memory[blk_start_index]
                                FA_cache[counter][1] = Memory[blk_start_index+4]
                                #add it to the LRU array as used once more
                                for l in range(0,8):
                                    if(l!=counter):
                                        LRU[l]+=1
                                
                                LRU[counter]=0 #reset because recently used

                            #now takee care if all bits are valid
                            #use LRU to determine which one to be removed
                            counter=0
                            if(full==True and hC==0):
                                maximum=max(LRU)

                                for val in LRU:
                                    if(val==maximum):
                                        break
                                    counter+=1
                                
                                print("LRU Policy: Least recently used block will be removed...")
                                print("Block to be removed: Block #" + str(counter))
                                missCount+=1
                                FA_Tag[counter]=int(addr_bin[0:29],2)
                                #updathe the cache
                                blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                                blk_start_index = blk_start_index*4
                                FA_cache[counter][0]= Memory[blk_start_index]
                                FA_cache[counter][1] = Memory[blk_start_index+4]
                                #add it to the LRU array as used once
                                for l in range(0,8):
                                    if(l!=counter):
                                        LRU[l]+=1

                                LRU[counter]=0 #reset because recently used

                if(cacheConfig1==3):
                    #print("CONFIGURATION - SA 1")
                    print("Tag = " + str(addr_bin[0:27]))
                    tag = int(addr_bin[0:27],2)
                    setIndex = int(addr_bin[27:29],2)
                    blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                    blk_start_index = blk_start_index*4
                    if(SA_ValidBit[setIndex][0]==0 and SA_ValidBit[setIndex][1]==0):
                        print("Status: Cold Miss (due to empty set " + str(setIndex) + ")")
                        SA_cache_1[setIndex][0][0] = Memory[blk_start_index]
                        SA_cache_1[setIndex][0][1] = Memory[blk_start_index+4]
                        SA_tag_1[setIndex][0]=tag
                        SA_ValidBit[setIndex][0]=1
                        LRU_SA[setIndex][1]+=1
                    else:
                        #CHECK IF HIT FIRST
                        print("Trying set " + str(setIndex) + " way 0...")
                        if(SA_tag_1[setIndex][0]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA[setIndex][1]+=1 #increase the time of not ussage in the other way
                            LRU_SA[setIndex][0]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 1...")
                        if(SA_tag_1[setIndex][1]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA[setIndex][0]+=1
                            LRU_SA[setIndex][1]=0
                        if(SA_tag_1[setIndex][0]!=tag and SA_tag_1[setIndex][1]!=tag):
                            if(SA_ValidBit[setIndex][0]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_1[setIndex][0][0] = Memory[blk_start_index]
                                SA_cache_1[setIndex][0][1] = Memory[blk_start_index+4]
                                SA_tag_1[setIndex][0]=tag
                                SA_ValidBit[setIndex][0]=1
                                LRU_SA[setIndex][0]=0
                                LRU_SA[setIndex][1]+=1
                            elif(SA_ValidBit[setIndex][1]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 1")
                                SA_cache_1[setIndex][1][0] = Memory[blk_start_index]
                                SA_cache_1[setIndex][1][1] = Memory[blk_start_index+4]
                                SA_tag_1[setIndex][1]=tag
                                SA_ValidBit[setIndex][1]=1
                                LRU_SA[setIndex][1]=0
                                LRU_SA[setIndex][0]+=1
                            else:
                                print("Status: Miss (due to missmatched tags)")
                                print("LRU Policy, least recently used block will be replaced...")
                                maximum = max(LRU_SA[setIndex])
                                if(maximum==LRU_SA[setIndex][0]):
                                    print("Block to be replaced: Block #0")
                                    SA_cache_1[setIndex][0][0] = Memory[blk_start_index]
                                    SA_cache_1[setIndex][0][1] = Memory[blk_start_index+4]
                                    SA_tag_1[setIndex][0]=tag
                                    SA_ValidBit[setIndex][0]=1
                                    LRU_SA[setIndex][0]=0
                                    LRU_SA[setIndex][1]+=1
                                elif(maximum==LRU_SA[setIndex][1]):
                                    print("Block to be replaced: Block #1")
                                    SA_cache_1[setIndex][1][0] = Memory[blk_start_index]
                                    SA_cache_1[setIndex][1][1] = Memory[blk_start_index+4]
                                    SA_tag_1[setIndex][1]=tag
                                    SA_ValidBit[setIndex][1]=1
                                    LRU_SA[setIndex][1]=0
                                    LRU_SA[setIndex][0]+=1
                                else:
                                    print("Something wrong with the max value")
                if(cacheConfig1==4):
                    #print("CONFIGURATION - SA 2")
                    print("Tag = " + str(addr_bin[0:28]))
                    tag = int(addr_bin[0:28],2)
                    setIndex = int(addr_bin[28],2)
                    blk_start_index = int((imm + Register[int(fetch[6:11],2)]- 8192)/4)
                    print("BLK start index: " + str(blk_start_index))
                    blk_start_index = blk_start_index*4
                    if(SA_ValidBit_2[setIndex][0]==0 and SA_ValidBit_2[setIndex][1]==0 and SA_ValidBit_2[setIndex][2]==0 and SA_ValidBit_2[setIndex][3]==0):
                        print("Status: Cold Miss (due to empty set " + str(setIndex) + ")")
                        SA_cache_2[setIndex][0][0] = Memory[blk_start_index]
                        SA_cache_2[setIndex][0][1] = Memory[blk_start_index+4]
                        SA_tag_2[setIndex][0]=tag
                        SA_ValidBit_2[setIndex][0]=1
                        LRU_SA_2[setIndex][1]+=1
                        LRU_SA_2[setIndex][2]+=1
                        LRU_SA_2[setIndex][3]+=1
                    else:
                        #CHECK IF HIT FIRST
                        print("Trying set " + str(setIndex) + " way 0...")
                        if(SA_tag_2[setIndex][0]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][1]+=1 #increase the time of not ussage in the other way
                            LRU_SA_2[setIndex][2]+=1
                            LRU_SA_2[setIndex][3]+=1
                            LRU_SA_2[setIndex][0]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 1...")
                        if(SA_tag_2[setIndex][1]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][0]+=1
                            LRU_SA_2[setIndex][2]+=1
                            LRU_SA_2[setIndex][3]+=1
                            LRU_SA_2[setIndex][1]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 2...")
                        if(SA_tag_2[setIndex][2]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][0]+=1
                            LRU_SA_2[setIndex][1]+=1
                            LRU_SA_2[setIndex][3]+=1
                            LRU_SA_2[setIndex][2]=0
                        else:
                            print("Trying set " + str(setIndex) + " way 3...")
                        if(SA_tag_2[setIndex][3]==tag):
                            print("Status: HIT!!!")
                            hitsCount+=1
                            LRU_SA_2[setIndex][0]+=1
                            LRU_SA_2[setIndex][1]+=1
                            LRU_SA_2[setIndex][2]+=1
                            LRU_SA_2[setIndex][3]=0

                        if(SA_tag_2[setIndex][0]!=tag and SA_tag_2[setIndex][1]!=tag and SA_tag_2[setIndex][2]!=tag and SA_tag_2[setIndex][3]!=tag):
                            if(SA_ValidBit_2[setIndex][0]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_2[setIndex][0][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][0][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][0]=tag
                                SA_ValidBit_2[setIndex][0]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][0]=0
                            elif(SA_ValidBit_2[setIndex][1]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 1")
                                SA_cache_2[setIndex][1][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][1][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][1]=tag
                                SA_ValidBit_2[setIndex][1]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][1]=0
                            elif(SA_ValidBit_2[setIndex][2]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_2[setIndex][2][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][2][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][2]=tag
                                SA_ValidBit_2[setIndex][2]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][2]=0
                            elif(SA_ValidBit_2[setIndex][3]==0):
                                print("Status: Miss (due to missmatched tags)")
                                print("Stored in set " + str(setIndex) + " way 0")
                                SA_cache_2[setIndex][3][0] = Memory[blk_start_index]
                                SA_cache_2[setIndex][3][1] = Memory[blk_start_index+4]
                                SA_tag_2[setIndex][3]=tag
                                SA_ValidBit_2[setIndex][3]=1
                                for l in range(0,4):
                                    LRU_SA_2[setIndex][l]+=1
                                LRU_SA_2[setIndex][3]=0
                            else:
                                print("Status: Miss (due to missmatched tags)")
                                print("LRU Policy, least recently used block will be replaced...")
                                maximum = max(LRU_SA_2[setIndex])
                                if(maximum==LRU_SA_2[setIndex][0]):
                                    print("Block to be replaced: Block #0")
                                    SA_cache_2[setIndex][0][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][0][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][0]=tag
                                    SA_ValidBit_2[setIndex][0]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][0]=0
                                elif(maximum==LRU_SA_2[setIndex][1]):
                                    print("Block to be replaced: Block #1")
                                    SA_cache_2[setIndex][1][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][1][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][1]=tag
                                    SA_ValidBit_2[setIndex][1]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][1]=0
                                elif(maximum==LRU_SA_2[setIndex][2]):
                                    print("Block to be replaced: Block #2")
                                    SA_cache_2[setIndex][2][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][2][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][2]=tag
                                    SA_ValidBit_2[setIndex][2]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][2]=0
                                elif(maximum==LRU_SA_2[setIndex][3]):
                                    print("Block to be replaced: Block #3")
                                    SA_cache_2[setIndex][3][0] = Memory[blk_start_index]
                                    SA_cache_2[setIndex][3][1] = Memory[blk_start_index+4]
                                    SA_tag_2[setIndex][3]=tag
                                    SA_ValidBit_2[setIndex][3]=1
                                    for l in range(0,4):
                                        LRU_SA_2[setIndex][l]+=1
                                    LRU_SA_2[setIndex][3]=0
                                else:
                                    print("Something wrong with the max value")


            if(debugMode==True and simMode==3):
                i=input("\n...Press enter to continue the diagnostic mode for Cache or E to exit")
                if(i=='e' or i=='E'):
                    exit()


        elif(fetch[0:6] == '001101'):
            s = int(fetch[6:11],2)
            t = int(fetch[11:16],2)
            imm = int(fetch[16:],2)
            Register[t] = Register[s] | imm
            #Register[t] = hex(Register[t])
            stats.log(fetch,"ori", 4, PC,1,0,1,0,0,0) # ORI instr, 4 cycles

            PC += 1

        else:
            print("Instruction " + str(InstructionsHex[PC]) + " not supported. Exiting")
            exit()

        if(not(finished)):
            stats.prints(simMode)

    if(finished):
        elapsed_time = time.time() - start_time
        stats.exitSim()
        if(simMode==1 or simMode==2):
            print("\nRegister Content: " + str(Register[8:24]))
            for i in range(0,132,4):
                print("Memory Content:", hex(i+8192), 'is', Memory[i])
            print("Total elapsed time: " + str(elapsed_time) + " seconds")

        if(simMode==3):
            print("------------------------")
            print("CACHE SUMMARY: ")
            print("Hits: " + str(hitsCount))
            print("Misses: " + str(memoryAccess-hitsCount))
            print("Memory accesses: " + str(memoryAccess))
            print("Hit rate: " + str(round(hitsCount/memoryAccess *100 , 2 ) )  + "%")
            print("Miss rate: " + str(round( (1-hitsCount/memoryAccess)*100 , 2) ) + "%")


    
simMode=0
cacheConfig1=0

def main():
    main2()
    global cacheConfig1
    global simMode
    Instructions = []   # a place to hold all instructions
    InstructionsHex = [] # raw data of instruction , in hex
    # print("Welcome to ECE366 Advanced MIPS Simulator.")
    simMode = int(input('Select from: 1) Processor Simulation of MC, 2) Processor Simulation of AP, 3) DataCache simulation of CacheSim:' + '\n'))
    debugMode = True if int(input("Select mode for simulating: " + "\n" + "1) Debug Mode, 2) Normal Execution \n")) == 1 else False

    if(simMode==3):
        print("Select Cache Configuration:")
        cacheConfig1 = int(input("1 = DM Cache (b=16; N=1; S=4)\n2 = FA Cache (b=8; N=8; S=1)\n3 = SA Cache (b=8; N=2; S=4)\n4 = SA Cache (b=8; N=4; S=2)"))

    
    
    print("cacheConfig1= " + str(cacheConfig1))



    #debugMode = True if int(input("Select mode for simulating: " + "\n" + "1) Debug Mode, 2) Normal Execution \n")) == 1 else False
    if (debugMode):
        print("Debug Mode\n") 
    else:
        print("Normal Execution \n")
    I_file = open('mc.txt')
    for line in I_file:
        if(line == "\n" or line[0] =='#'):
            continue    # ignore empty lins, comments
        line = line.replace('\n', '')   # delete endline characters in the line
        InstructionsHex.append(line[2:])
        line = format(int(line,16),"032b")
        Instructions.append(line)

    simulate(Instructions, InstructionsHex, debugMode, simMode)

if __name__ == "__main__":
    main()