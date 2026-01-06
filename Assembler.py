import sys
input_file, output_file = sys.argv[1], sys.argv[2]

B_inst = ["beq", "bne", "blt"]
B_opp = "1100011"
B_funct3 = {"beq": "000", "bne": "001", "blt": "100"}

I_inst = ["lw", "addi", "jalr"]
I_opp = {"lw": "0000011", "addi": "0010011", "jalr": "1100111"}
I_funct3 = {"lw": "010", "addi": "000", "jalr": "000"}

J_inst = ["jal"]
J_opp = "1101111"

R_inst = ["add", "sub", "slt" , "srl", "or", "and"]
R_opp = "0110011"
R_funct3 = {"add": "000", "sub": "000", "slt": "010", "srl": "101", "or": "110", "and": "111"}
R_funct7 = {op: "0000000" if op != "sub" else "0100000" for op in R_inst}

S_inst = ["sw"]
S_opp = "0100011"
S_funct3 = {"sw": "010"}

register_address = {
    "zero": "00000", "ra": "00001", "sp": "00010", "gp": "00011", "tp": "00100", "t0": "00101", "t1": "00110", "t2": "00111", "s0": "01000",
    "fp": "01000", "s1": "01001", "a0": "01010", "a1": "01011", "a2": "01100", "a3": "01101", "a4": "01110", "a5": "01111", "a6": "10000",
    "a7": "10001", "s2": "10010", "s3": "10011", "s4": "10100", "s5": "10101", "s6": "10110", "s7": "10111", "s8": "11000", "s9": "11001",
    "s10": "11010", "s11": "11011", "t3": "11100", "t4": "11101", "t5": "11110", "t6": "11111"
}

#checks errors in register address and immediate value
def error_check(line):
    inst, other = line.split()
    if inst in R_inst or inst in I_inst or inst in B_inst:
        if inst in R_inst:
            rd, rs1, rs2 = other.split(",")
            if not check_register(rd) or not check_register(rs1) or not check_register(rs2):
                 return False, "register-not-found"
            else:
                return True, "ok"
            
        elif inst in I_inst:
            if inst == "lw": 
                rd,oth = other.split(",")

                if not check_register(rd):
                    return False, "register-not-found"
                
                imm, rd = oth.split("(")
                rd=rd.rstrip(")")

                if(not check_register(rd)):
                    return False, "register-not-found"
                
                if int(imm) < -1 * 2**11 or int(imm) > (2**11-1):
                    return False, "out-of-bound"
                return True, "ok"
            else:
                rd,rs,num = other.split(",")
                if(not check_register(rd) or not check_register(rs)):
                    return False, "register-not-found"
                
                if int(num) < -1 * 2**11 or int(num) > (2**11-1):
                    return False, "out-of-bound"
                
                return True, "ok"
        else: 
            rs1, rs2, num = other.split(",") 
            if(not check_register(rs1) or not check_register(rs2)):

                return False, "register-not-found"
            
            if num.isalpha():
                return True, "ok"
            
            if (num.lstrip('-')).isnumeric():
                if int(num) < -1 * (2**12) or int(num) > (2**12-1):
                    return False, "out-of-bound"
                
            return True, "ok"
        
    elif inst in S_inst  or inst in J_inst:
        if inst in S_inst:
            rs2, other = other.split(",")
            num, rs1 = other.split("(")
            rs1 = rs1.rstrip(")")
            if(not check_register(rs1) or not check_register(rs2)):
                return False, "register-not-found"
            
            if int(num) < -1 * 2**11 or int(num) > (2**11-1):
                return False, "out-of-bound"
            
            return True, "ok"
        else: 
            rd, num = other.split(",")
            if not check_register(rd):
                return False, "register-not-found"
            if num.isnumeric() or (num[0]=="-1" and num[1:].isnumeric()):

                if int(num) < -1* 2**19 or int(num) > 2**19 -1:
                    return False, "out-of-bound"

            return True, "ok"
      
    else:
        return False, "opcode-not-found"

#checks error in register naming
def check_register(reg):
    if reg not in register_address.keys():
        return False
    return True

#conversion of immediate value
def imm_conversion(num, length):

    return bin(num & ((1 << length) - 1))[2:].zfill(length)

def R_type_inst(inp):
    rd, rs1, rs2 = inp[1].split(",")
    return R_funct7[inp[0]] + register_address[rs2] + register_address[rs1] + R_funct3[inp[0]] + register_address[rd] + R_opp

def I_type_inst(inp):
    final = I_opp[inp[0]]
    if inp[0] == "lw":
        rd, other = inp[1].split(",")
        tempimm, rs = other.split("(")
        rs = rs.rstrip(")")
        final = imm_conversion(int(tempimm), 12) + register_address[rs] + I_funct3[inp[0]] + register_address[rd] + final
       
    else:
        rd, rs, other = inp[1].split(",")   
        final = imm_conversion(int(other), 12) + register_address[rs] + I_funct3[inp[0]] + register_address[rd] + final
    return final

def S_type_inst(inp):
    rs2,k = inp[1].split(',')
    k = k.rstrip(')')               
    imm,rs1 = k.split('(')   
    
    imm_bin = imm_conversion(int(imm),12)
    
    return imm_bin[-12:-5] + register_address[rs2] + register_address[rs1] + S_funct3[inp[0]] + imm_bin[-5:] + S_opp


def J_type_inst(inp, pc):
    rd, imm = inp[1].split(",")
    
    imm_val = int(imm) if imm.lstrip('-').isdigit() else labels[imm] - pc
    imm_bin = imm_conversion(imm_val, 21)
    
    return imm_bin[-21] + imm_bin[-11:-1] + imm_bin[-12] + imm_bin[-20:-12] + register_address[rd] + J_opp

def B_type_inst(inp, pc):
    rs1, rs2, imm = inp[1].split(",")
    
    imm_val = int(imm) if imm.lstrip('-').isdigit() else labels[imm] - pc
    imm_bin = imm_conversion(imm_val, 13)
    
    return imm_bin[-13] + imm_bin[-11] + imm_bin[-10:-5] + register_address[rs2] + register_address[rs1] + B_funct3[inp[0]] + imm_bin[-5:-1] + imm_bin[-12] + B_opp


labels = {}
def main():
    global labels
    with open(input_file, "r") as assembly:
        temp = [x.strip() for x in assembly.readlines()]
        instructions = []
        for i in temp:
            if i != "":
                instructions.append(i)

    #saves labels in dict with its pc counter value
    for i, line in enumerate(instructions):

        parts = line.split(" ")
        if parts[0].endswith(":"):
            labels[parts[0][:-1]] = i * 4
            instructions[i] = " ".join(parts[1:])
        elif ":" in parts[0]:
            x = parts[0].find(":",0)
            labels[parts[0][:x]] = i * 4
            parts[0] = (parts[0])[x+1:]
            instructions[i] = " ".join(parts[:])

    count = 0
    for i in instructions:
        if i == "beq zero,zero,0":
            count += 1
    
    if count == 0:
        print("No Virtal Halt")
        exit()
    elif count > 1:
        print("Multiple Virtual Halts")
    elif count == 1:
        if(instructions[-1] != "beq zero,zero,0"):
            print("Virtual Halt Not At The End")
            exit()


    for i, instr in enumerate(instructions):

        valid, error_type = error_check(instr)
        if not valid:
            print(f"{error_type} error in  {instr}")
            exit()

    final_output = []
    pc = 0
    while pc < len(instructions) * 4:
        instr = instructions[pc // 4].split(" ")
        if instr[0] in R_inst:
            final_output.append(R_type_inst(instr))
        elif instr[0] in I_inst:
            final_output.append(I_type_inst(instr))
        elif instr[0] in J_inst:
            final_output.append(J_type_inst(instr, pc))
        elif instr[0] in B_inst:
            final_output.append(B_type_inst(instr, pc))
        elif instr[0] in S_inst:
            final_output.append(S_type_inst(instr))
        pc += 4

    with open(output_file, "w") as output:
        output.write("\n".join(final_output) + "\n")

main()

   
    
    

