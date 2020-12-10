from ctypes import CDLL, c_uint64, c_void_p, Structure, c_ulonglong, byref
from sys import argv
from os import execv, wait, WIFSTOPPED, fork, waitpid, WSTOPSIG, system

SIGSTOP = 19


PTRACE_TRACEME    = 0
PTRACE_SINGLESTEP = 9
PTRACE_ATTACH     = 16
PTRACE_DETACH     = 17
PTRACE_SYSCALL    = 24

# Breakpoints --------
# Search memory
PTRACE_PEEKTEXT   = 1
# Insert into memory
PTRACE_POKETEXT   = 4
# Continue execution
PTRACE_CONT       = 7

# Context actions - get registers etc ---
PTRACE_GETREGS    = 12
PTRACE_SETREGS    = 13

libc = CDLL('libc.so.6')
libc.ptrace.argtypes = [c_uint64, c_uint64, c_uint64, c_void_p]
ptrace = libc.ptrace


class RegsStruct(Structure):
    _fields_ = [
        ("r15", c_ulonglong),
        ("r14", c_ulonglong),
        ("r13", c_ulonglong),
        ("r12", c_ulonglong),
        ("rbp", c_ulonglong),
        ("rbx", c_ulonglong),
        ("r11", c_ulonglong),
        ("r10", c_ulonglong),
        ("r9", c_ulonglong),
        ("r8", c_ulonglong),
        ("rax", c_ulonglong),
        ("rcx", c_ulonglong),
        ("rdx", c_ulonglong),
        ("rsi", c_ulonglong),
        ("rdi", c_ulonglong),
        ("orig_rax", c_ulonglong),
        ("rip", c_ulonglong),
        ("cs", c_ulonglong),
        ("eflags", c_ulonglong),
        ("rsp", c_ulonglong),
        ("ss", c_ulonglong),
        ("fs_base", c_ulonglong),
        ("gs_base", c_ulonglong),
        ("ds", c_ulonglong),
        ("es", c_ulonglong),
        ("fs", c_ulonglong),
        ("gs", c_ulonglong),
    ]

regs = RegsStruct()


def set_breakpoint(pid, instr_addr):
    # Pobierz aktualny stan RIP
    ptrace(PTRACE_GETREGS, pid, 0, byref(regs))
    print("\nPotomek zostal zatrzymany na adresie RIP = 0x%x" % (regs.rip))

    # Odczyt instrukcji ze wskazanej komorki pamieci
    org_instr = ptrace(PTRACE_PEEKTEXT, pid, c_ulonglong(instr_addr), 0)
    print("Oryginalna zawartosc pamieci z 0x%x:  0x%x" % (instr_addr, org_instr))

    # Zapis specjalnej instrukcji int3 pod wskazany adres
    instr_trap = (org_instr & 0xFFFFFFFFFFFFFF00) | 0xCC
    ptrace(PTRACE_POKETEXT, pid, instr_addr, instr_trap)
    zm_instr = ptrace(PTRACE_PEEKTEXT, pid, instr_addr, 0)
    print("Zmieniona zawartosc pamieci z 0x%x:  0x%x" % (instr_addr, zm_instr))

    return org_instr
#

def unset_breakpoint(pid, instr_addr, org_instr):
    # Przywroc oryginalna instrukcje, cofnij wskaznik instrukcji (RIP)
    ptrace(PTRACE_POKETEXT, pid, instr_addr, org_instr)
    regs.rip -= 1
    ptrace(PTRACE_SETREGS, pid, 0, byref(regs))
#

def debug(pid):
    print("Debugger started")
   
    status_attach = ptrace(PTRACE_ATTACH, pid, 0, 0)
    if status_attach:
        print("Nie udalo sie podpiac do procesu")

    pid, sts  = waitpid(pid, 0)
    bp_addr = 0x0000000000401ce5

    
    if WIFSTOPPED(sts):
        if WSTOPSIG(sts) == SIGSTOP:
            while WIFSTOPPED(sts):
                original_instr = set_breakpoint(pid, bp_addr)
                ptrace(PTRACE_CONT, pid, -1, 0)

                # Petla debuggera - oczekujemy na dalsze zdarzenia
                status = wait()
                if (WIFSTOPPED(status[1])):
                    print("Potomek otrzymal sygnal: ", WSTOPSIG(status[1]))

                unset_breakpoint(pid, bp_addr, original_instr)
                
                input()

                ptrace(PTRACE_SINGLESTEP, pid, 0, 0)
                pid, sts = wait()
                original_instr = set_breakpoint(pid, bp_addr)

                #ptrace(PTRACE_CONT, pid, -1, 0)

    
    



debug(int(argv[1]))

