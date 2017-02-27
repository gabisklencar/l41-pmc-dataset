import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json

# Setup constants

# Buffer sizes
BUFFER_SIZES = [512 * 2 ** exp for exp in range(0, 16)]

# Total size, kept constant at 16MB
TOTAL_SIZE = BUFFER_SIZES[-1]

# Number of trials for each measurement.
# Note: When the measurements were taken, the first sample was discarded.
NUM_TRIALS = 10

# IPC modes
IPC_MODES = ["-i pipe", "-i local", "-s -i local"];

# Process modes
PROC_MODES = ["2thread", "2proc"]

# Performance counters
PMC = ["l1d", "l1i", "l2", "mem", "axi", "tlb"]

# JSON fields for l1d
L1D = ["INSTR_EXECUTED",
       "CLOCK_CYCLES",
       "CLOCK_CYCLES/INSTR_EXECUTED",
       "L1_DCACHE_ACCESS",
       "L1_DCACHE_ACCESS/INSTR_EXECUTED",
       "L1_DCACHE_ACCESS/CLOCK_CYCLES",
       "L1_DCACHE_REFILL",
       "L1_DCACHE_REFILL/INSTR_EXECUTED",
       "L1_DCACHE_REFILL/CLOCK_CYCLES"]

# JSON fields for l1i
L1I = ["INSTR_EXECUTED",
       "CLOCK_CYCLES",
       "CLOCK_CYCLES/INSTR_EXECUTED",
       "L1_ICACHE_REFILL",
       "L1_ICACHE_REFILL/INSTR_EXECUTED",
       "L1_ICACHE_REFILL/CLOCK_CYCLES"]

# JSON fields for l2
L2 = ["INSTR_EXECUTED",
      "CLOCK_CYCLES",
      "CLOCK_CYCLES/INSTR_EXECUTED",
      "L2_ACCESS",
      "L2_ACCESS/INSTR_EXECUTED",
      "L2_ACCESS/CLOCK_CYCLES"]

# JSON fields for mem
MEM = ["INSTR_EXECUTED",
       "CLOCK_CYCLES",
       "CLOCK_CYCLES/INSTR_EXECUTED",
       "MEM_READ",
       "MEM_READ/INSTR_EXECUTED",
       "MEM_READ/CLOCK_CYCLES",
       "MEM_WRITE",
       "MEM_WRITE/INSTR_EXECUTED",
       "MEM_WRITE/CLOCK_CYCLES"]

# JSON fields for axi
AXI = ["INSTR_EXECUTED",
       "CLOCK_CYCLES",
       "CLOCK_CYCLES/INSTR_EXECUTED",
       "AXI_READ",
       "AXI_READ/INSTR_EXECUTED",
       "AXI_READ/CLOCK_CYCLES",
       "AXI_WRITE",
       "AXI_WRITE/INSTR_EXECUTED",
       "AXI_WRITE/CLOCK_CYCLES"]

# JSON fields for tlb
TLB = ["INSTR_EXECUTED",
       "CLOCK_CYCLES",
       "CLOCK_CYCLES/INSTR_EXECUTED",
       "ITLB_REFILL",
       "ITLB_REFILL/INSTR_EXECUTED",
       "ITLB_REFILL/CLOCK_CYCLES",
       "DTLB_REFILL",
       "DTLB_REFILL/INSTR_EXECUTED",
       "DTLB_REFILL/CLOCK_CYCLES"]

# Note: each data point also has a "bandwidth" field
# Note: when taking measurements, the benchmarks looped over IPC modes, and for each IPC mode over process modes

# Define a helper function for reading in a file and decoding the json
# Arguments:
#   pmc: string, one of ["l1d", "l1i", "l2", "mem", "axi", "tlb"]
def loadFile(pmc):
    filename = "ipc-static-pmc-" + pmc + ".txt"
    f = open(filename, "r")
    res = json.load(f)
    f.close()
    return res

ls = {"-i pipe" : "-", "-i local": "--", "-s -i local": "-."}

# A helper function plots two graphs, one for each process mode
# Arguments:
#   data: the output of loadFile
#   key: the counter to plot (e.g. "AXI_READ/INSTR_EXECUTED")
#   ylabel: the y-label for the graph
#   lines: x-coordinates of values at which the function should draw a vertical line
def plotProcModesSeparately(data, key, ylabel, lines):
    fig, read = plt.subplots(1, 2, sharex=True, sharey=True)
    
    i = 0
    for proc_mode in PROC_MODES:
        read[i].set_title(key + " " + proc_mode)
        read[i].set_xlabel("Buffer size (Bytes)")
        read[i].set_ylabel(ylabel)
        read[i].set_xscale("log")
        for ipc_mode in IPC_MODES:
            # Reshape into an array of dimensions len(BUFFER_SIZE) x NUM_TRIALS
            data_float = [float(x) for x in data[ipc_mode][proc_mode][key]]
            data_res = np.reshape(data_float, (len(BUFFER_SIZES), NUM_TRIALS))[:,:]
            # print data
            
            # Convert into a Panda DataFrame
            df = pd.DataFrame(data_res, index=BUFFER_SIZES)
            
            # Compute error bars based on the 25 and 75 quantile values
            # Note: The error bars should be small indicating that the experiment is tightly controlled
            error_bars = df.quantile([.25, .75], axis=1)
            error_bars.loc[[0.25]] = df.median(1) - error_bars.loc[[0.25]]
            error_bars.loc[[0.75]] = error_bars.loc[[0.75]] - df.median(1)
            error_bars_values = [error_bars.values]
            
            # Add the series to the plot
            df.median(1).plot(ax=read[i], figsize=(10, 4), yerr=error_bars_values, label=ipc_mode, legend=True, linestyle=ls[ipc_mode])
        i = i + 1
        
    for i in range(0, 2):
        for l in lines[i]:
            read[i].axvline(x=(l[0])*1024, linestyle=":")
            read[i].text((l[0] + l[0]/4)*1024, l[1], l[2])
    
    plt.show()
    # figname = "graphs/" + key + "_proc_modes_sep.pdf"
    # plt.savefig(figname)

# A helper function plots three graphs, one for each IPC mode
# Arguments:
#   data: the output of loadFile
#   key: the counter to plot (e.g. "AXI_READ/INSTR_EXECUTED")
#   ylabel: the y-label for the graph
#   lines: x-coordinates of values at which the function should draw a vertical line
def plotIPCModesSeparately(data, key, ylabel, lines):
    fig, read = plt.subplots(1, 3, sharex=True, sharey=True)
    plt.suptitle(key)
    
    ls = {"2thread" : "-", "2proc" : "--"}
    
    i = 0
    for ipc_mode in IPC_MODES:
        read[i].set_title(ipc_mode)
        read[i].set_xlabel("Buffer size(Bytes)")
        read[i].set_ylabel(ylabel)
        read[i].set_xscale("log")
        for proc_mode in PROC_MODES:
            # Reshape into an array of dimensions len(BUFFER_SIZE) x NUM_TRIALS
            data_float = [float(x) for x in data[ipc_mode][proc_mode][key]]
            data_res = np.reshape(data_float, (len(BUFFER_SIZES), NUM_TRIALS))[:,:]
            
            # Convert into a Panda DataFrame
            df = pd.DataFrame(data_res, index=BUFFER_SIZES)
            
            # Compute error bars based on the 25 and 75 quantile values
            # Note: The error bars should be small indicating that the experiment is tightly controlled
            error_bars = df.quantile([.25, .75], axis=1)
            error_bars.loc[[0.25]] = df.median(1) - error_bars.loc[[0.25]]
            error_bars.loc[[0.75]] = error_bars.loc[[0.75]] - df.median(1)
            error_bars_values = [error_bars.values]
            
            # Add the series to the plot
            lgnd = ipc_mode == "-s -i local"
            df.median(1).plot(ax=read[i], figsize=(10, 3), yerr=error_bars_values, label=proc_mode, legend=lgnd, linestyle=ls[proc_mode])
        i = i + 1
        
    for i in range(0, 3):
        for l in lines:
            read[i].axvline(x=(l[0])*1024, linestyle=":")
            read[i].text((l[0] + l[0]/4)*1024, l[1], l[2])
            
    plt.subplots_adjust(top=0.85)
    plt.show()
    # figname = "graphs/" + key + "_ipc_modes_sep.pdf"
    # plt.savefig(figname)

# Example usage:
l1d_data = loadFile("l1d")
plotProcModesSeparately(l1d_data, "L1_DCACHE_ACCESS", "Count", [(4, 130000000, "P")])