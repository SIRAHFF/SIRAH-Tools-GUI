# backmapping.tcl
#
#   This Tcl script automates the backmapping process within VMD (Visual
#   Molecular Dynamics) using the `sirah_backmapping` procedure. It handles the
#   loading of molecular topology and trajectory files, configures backmapping
#   parameters, executes the backmapping command, and manages output and error
#   reporting.
#
# Usage:


# vmd -dispdev text -e sirah_backmap_script.tcl -args topology_file
#     |                                               trajectory_file
#                                                     sirah_tcl_path
#                                                     first_frame
#                                                     last_frame
#                                                     each
#                                                     frames_list
#                                                     outname
#                                                     nomin
#                                                     cuda
#                                                     gbsa
#                                                     cutoff
#                                                     mpi
#                                                     maxcyc
#                                                     ncyc
#
# Arguments:
#   1. topology_file      - Path to the topology file (e.g., PDB file).
#   2. trajectory_file    - Path to the trajectory file (e.g., DCD file).
#   3. sirah_tcl_path     - Path to the sirah_vmdtk.tcl script.
#   4. first_frame        - Starting frame number for processing.
#   5. last_frame         - Ending frame number for processing (-1 for all frames).
#   6. each_frame         - Step size between frames to process.
#   7. frames_list        - Specific frames to process (empty or "all" for no restriction).
#   8. outname            - Base name for output files (with output dir).
#   9. nomin              - Flag to disable minimization (1 to disable).
#   10. cuda              - Flag to enable CUDA acceleration (1 to enable).
#   11. gbsa              - Flag to enable GBSA solvent model (1 to enable).
#   12. cutoff            - Cutoff distance for non-bonded interactions.
#   13. mpi               - Number of MPI processes to use.
#   14. maxcyc            - Maximum number of cycles for minimization.
#   15. ncyc              - Number of cycles for iterative process.
#
# Requirements:
#   - VMD installed with Tcl support.
#   - sirah_vmdtk.tcl script available at the specified path.
#   - Correctly formatted topology and trajectory files.
#
# Authors: Andres Ballesteros & Lucianna Silva Dos Santos
# ==============================================================================

puts ""
puts ""
puts "╔═════════════════════════════════════════════════════╗"
puts "║                   BACKMAPPING TAB                   ║"
puts "╚═════════════════════════════════════════════════════╝"
puts ""
puts "Starting Backmapping...................................."
puts ""




# ==============================================================================
# Section: Argument Parsing
# Description:
#   Extracts and assigns command-line arguments to corresponding variables.
# ==============================================================================

# Read the provided arguments
set topology_file [lindex $argv 0]
set trajectory_file [lindex $argv 1]
set sirah_tcl_path [lindex $argv 2]
set first_frame [lindex $argv 3]
set last_frame [lindex $argv 4]
set each_frame [lindex $argv 5]
set frames_list [lindex $argv 6]
set outname [lindex $argv 7]
set nomin [lindex $argv 8]
set cuda [lindex $argv 9]
set gbsa [lindex $argv 10]
set cutoff [lindex $argv 11]
set mpi [lindex $argv 12]
set maxcyc [lindex $argv 13]
set ncyc [lindex $argv 14]

# ==============================================================================
# Section: Loading External Tcl Scripts
# Description:
#   Sources the sirah_vmdtk.tcl script to make the sirah_backmapping procedure
#   available within the current VMD session.
# ==============================================================================


# Load the sirah_vmdtk.tcl script with the sirah_backmapping functionality
puts "Attempting to load sirah_vmdtk.tcl from: $sirah_tcl_path"
if {[catch {source $sirah_tcl_path} err]} {
    puts "Error: Failed to load sirah_vmdtk.tcl - $err"
    quit
}
puts " "
puts "======================================="
puts "# sirah_vmdtk.tcl loaded successfully #"
puts "======================================="
puts " "

# ==============================================================================
# Section: File Existence Verification
# Description:
#   Checks if the specified topology and trajectory files exist. If not, prints
#   an error message and terminates the script to prevent further execution errors.
# ==============================================================================

# Verify the existence of the topology file
if {![file exists $topology_file]} {
    puts " "
    puts "======================================================================================"
    puts "Error: Topology file not found: $topology_file"                                    
    puts "======================================================================================"
    puts " "
    quit
}

# Verify the existence of the trajectory file
if {![file exists $trajectory_file]} {
    puts " "
    puts "======================================================================================"
    puts "Error: Trajectory file not found: $trajectory_file"
    puts "======================================================================================"
    puts " "
    quit
}

# ==============================================================================
# Section: Loading Topology and Trajectory into VMD
# Description:
#   Imports the molecular topology and trajectory files into VMD using the
#   specified frame range and step size.
# ==============================================================================

# Load the topology file into VMD
puts " "
puts "======================================================================================"
puts "Loading topology file: $topology_file"
puts "======================================================================================"
puts " "
mol new $topology_file waitfor all

# Load the trajectory file into VMD with specified frame parameters
puts " "
puts "======================================================================================"
puts "Loading trajectory file: $trajectory_file"
puts "======================================================================================"
puts " "
mol addfile $trajectory_file first 0 last -1 waitfor all

# ==============================================================================
# Section: Determining Frame Range
# Description:
#   Retrieves the total number of frames from the loaded trajectory. If the
#   last_frame argument is set to -1, it automatically assigns it to the total
#   number of frames, ensuring that the entire trajectory is processed.
# ==============================================================================

# Retrieve the total number of frames from the loaded molecule
set total_frames [molinfo top get numframes]

# If last_frame is set to -1, assign it to the total number of frames
if { $last_frame == "-1" } {
    set last_frame [expr {$total_frames - 1}]
    #set last_frame $total_frames
    puts " "
    puts "================================================================="
    puts "Last frame was set to -1, using total frames: $last_frame"
    puts "================================================================="
    puts " "
}


# ==============================================================================
# Section: Constructing the Backmapping Command
# Description:
#   Builds the sirah_backmap command as a Tcl list, appending necessary parameters.
#   Advanced options are only appended if they differ from their default values.
# ==============================================================================

# Construct the sirah_backmap command as a list
set backmap_cmd [list sirah_backmap]

# Append frame selection based on frames_list if specified and not 'all'
if { $frames_list != "" && $frames_list != "all" } {
    lappend backmap_cmd frames $frames_list
}

# Note: 'first', 'last', and 'each' are not appended to the backmapping command

# Append the output name to the backmapping command
lappend backmap_cmd first $first_frame last $last_frame  each $each_frame outname $outname noload

# Append advanced options only if they differ from their default values
if { $nomin == "1" } {
    lappend backmap_cmd nomin
}
if { $cuda == "1" } {
    lappend backmap_cmd cuda
}
if { $gbsa == "1" } {
    lappend backmap_cmd gbsa
}
if { $cutoff != "12" } {
    lappend backmap_cmd cutoff $cutoff
}
if { $mpi != "1" } {
    lappend backmap_cmd mpi $mpi
}
if { $maxcyc != "150" } {
    lappend backmap_cmd maxcyc $maxcyc
}
if { $ncyc != "100" } {
    lappend backmap_cmd ncyc $ncyc
}

# ==============================================================================
# Section: Debugging Information
# Description:
#   Prints the current values of all relevant variables to the console for
#   debugging purposes.
# ==============================================================================

# Print the values of the variables for debugging purposes
puts " "
puts "========================="
puts "values of the variables"
puts "========================="
puts ""
puts "First frame: $first_frame"
puts "Last frame: $last_frame"
puts "Each frame: $each_frame"
puts "Frames list: $frames_list"
puts "Output name: $outname"
puts "No min: $nomin"
puts "CUDA: $cuda"
puts "GBSA: $gbsa"
puts "Cutoff: $cutoff"
puts "MPI: $mpi"
puts "Maxcyc: $maxcyc"
puts "ncyc: $ncyc"
puts " "
puts "=============================================================================="

#Print the final command before execution for debugging
puts "Command before execution: "
puts ""
puts "Executing backmapping command: $backmap_cmd"
puts "=============================================================================="
puts " "

# ==============================================================================
# Section: Executing the Backmapping Command and Error Handling
# Description:
#   Executes the sirah_backmap command and captures any errors that occur during
#   execution. Provides feedback on the success or failure of the command.
# ==============================================================================

# Execute the sirah_backmap command and capture any errors
if {[catch {eval $backmap_cmd} result]} {
    puts " "
    puts "********************************************"
    puts "Error executing sirah_backmap: $result"
    puts "********************************************"
    puts " "
    puts " "
} else {
    puts " "
    puts "**********************************************"
    puts "    sirah_backmap executed successfully"
    puts "**********************************************"
    puts " "


}

# ==============================================================================
# Section: Termination
# Description:
#   Signals the end of the script execution by terminating the VMD session.
# ==============================================================================

# Terminate VMD after execution
puts "========================"
puts "Execution completed"
puts "========================"
puts " "
puts " "
quit
