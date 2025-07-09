# sirah_analysis.tcl
#
# This TCL script is designed to perform various molecular analyses using VMD (Visual Molecular Dynamics).
# It supports calculations such as RMSD, RMSF, Radius of Gyration, SASA, Distance, and RDF based on user-selected atom selections.
#
# Usage:
#vmd -dispdev text -e sirah_analysis.tcl -args topology_file
#                                              trayectory_file
#                                              selection1
#                                              selection2
#                                              selection3
#                                              analysis_code
#                                              sirah_tcl_path
#                                              analysis_dir
#                                              reference_file
#                                              skip_value
#                                              srad
#                                              RMSF2PDBeta

#Arguments:
#1. topology_file    - Path to the topology file.
#2. trajectory_file  - Path to the trajectory file.
#3. selection1       - Primary atom selection using VMD syntax.
#4. selection2       - Secondary atom selection using VMD syntax.
#5. selection3       - Tertiary atom selection using VMD syntax.
#6. analysis_code    - Integer code representing selected analyses (bitwise flags).
#7. sirah_tcl_path   - Path to the sirah_vmdtk.tcl script (script_dir)
#8. analysis_dir     - Directory where analysis output files will be saved (output_dir).
#9. reference_file   - Path to the reference file (optional).
#10. skip value      - Skip for load trajectory
#11. srad            - Probe radius for SASA and Contact surface 
#12. RMSF2PDBeta     - If 1 RSMF value is write in beta column in a pdb file.

# Requirements:
#   - VMD installed with Tcl support.
#   - sirah_vmdtk.tcl script available at the specified path.
#   - Correctly formatted topology and trajectory files.
#
# Authors: Andres Ballesteros, Jorge Cantero & Lucianna Silva Dos Santos



puts ""
puts ""
puts ""
puts ""
puts ""
puts "╔═════════════════════════════════════════════╗"
puts "║              ANALYSIS TAB                   ║"
puts "╚═════════════════════════════════════════════╝"
puts ""
puts "Starting analysis tab ........................"
puts ""


# Print the number of arguments received and their values for debugging purposes.
puts ""
puts "####################################"
puts "Number of arguments received: [llength $argv]"
puts "####################################"
puts ""

# Verify that at least the minimum number of arguments (12) was received.
if {[llength $argv] < 12} {
    puts ""
    puts "###############################################"
    puts ""
    puts "Usage: $argv0 topology_file trajectory_file sel sel1 sel2 analysis_code script_dir analysis_dir reference_file"
    puts "At least 12 arguments are required."
    puts ""
    puts "###############################################"
    exit 1
}

# Assign arguments to variables for easier reference.
puts ""
puts "======================================================================================================================"
puts ""
puts "Arguments ...."
puts ""
set topology_file    [lindex $argv 0]
set trajectory_file  [lindex $argv 1]
set sel              [lindex $argv 2]
set sel1             [lindex $argv 3]
set sel2             [lindex $argv 4]
set analysis_code    [lindex $argv 5]
set script_dir       [lindex $argv 6]
set analysis_dir     [lindex $argv 7]
set reference_file   [lindex $argv 8]
set skip             [lindex $argv 9]
set srad             [lindex $argv 10]
set rmsf2pdb         [lindex $argv 11]
puts ""
puts "======================================================================================================================"

# Print the script and analysis directories for debugging.
puts ""
puts "Script Directory: $script_dir"
puts "Analysis Directory: $analysis_dir"
puts ""


# Source the additional TCL script 'sirah_vmdtk.tcl' from the provided script directory.
puts ""
puts "###############################################"
puts "Loading sirah_vmdtk.tcl......................."
puts ""
set vmdtk_path [file join $script_dir "sirah_vmdtk.tcl"]
source $vmdtk_path
puts ""
puts "sirah_vmdtk.tcl loaded successfully"
puts "###############################################"
puts ""


###############################################################################
# Function: load_molecules
# Purpose : Loads the molecular topology and trajectory files into VMD.
# Arguments:
#   topology_file   - Path to the topology file.
#   trajectory_file - Path to the trajectory file.
#   reference_file  - Path to the reference file (optional).
#
# If 'reference_file' is "None", only the trajectory file is loaded.
# Otherwise, both the reference and trajectory files are loaded.
###############################################################################
proc load_molecules {topology_file trajectory_file reference_file skip} {
    # Load the topology file.
    puts ""
    mol new $topology_file waitfor all
    puts ""

    # Load the trajectory file, with or without a reference file.
    if { $reference_file == "None" } {
        puts ""
        mol addfile $trajectory_file first 0 last -1 step $skip waitfor all
        puts ""
    } else {
        puts ""
        mol addfile $reference_file waitfor all
        mol addfile $trajectory_file first 0 last -1 step $skip waitfor all
        puts ""
    }
}

###############################################################################
# Function: validate_selection
# Purpose : Validates an atom selection to ensure it is syntactically correct
#           and selects at least one atom.
# Arguments:
#   selection_name - A label for the selection (e.g., "sel", "sel1", "sel2").
#   selection      - The atom selection string in VMD syntax.
#
# If the selection is invalid (syntax error or zero atoms selected),
# an error message is printed within a prominent '#' box, and the script exits.
###############################################################################
proc validate_selection {selection_name selection} {
    set atomselect_obj ""
    # Attempt to create an atomselect object; catch any syntax errors.
    set err_code [catch {set atomselect_obj [atomselect top "$selection"]} err_msg]
    if {$err_code} {
        puts "################################################################"
        puts "# Error: Invalid selection syntax for '$selection_name'.       #"
        puts "# Details: $err_msg                                            #"
        puts "################################################################"
        exit 1
    }

    # Check if the selection includes zero atoms.
    if {[$atomselect_obj num] == 0} {
        puts "##########################################################################"
        puts "# Error: Your selection '$selection_name' is invalid, it has zero atoms. #"
        puts "##########################################################################"
        exit 1
    }

    # Clean up the atomselect object to free resources.
    $atomselect_obj delete
}

###############################################################################
# Function: rmsd_sel
# Purpose : Calculates RMSD (Root Mean Square Deviation) for the specified selection.
# Arguments:
#   sel          - The atom selection string for RMSD calculation.
#   analysis_dir - Directory where RMSD output will be saved.
###############################################################################
proc rmsd_sel {sel analysis_dir} {
    # Replace all whitespace in the selection string with underscores for file naming.
    set str [regsub -all {\s+} $sel "_"]
    set outfile [open "$analysis_dir/RMSD_${str}.dat" w]

    # Create atomselect objects for reference and comparison.
    set all [atomselect top all]
    set reference [atomselect top "$sel" frame 0]
    set compare [atomselect top "$sel"]

    # Get the total number of frames in the trajectory.
    set N [molinfo top get numframes]

    # Iterate over each frame to calculate RMSD.
    for {set i 0} {$i < $N} {incr i} {
        $all frame $i
        set trans_mat [measure fit $compare $reference]
        $all move $trans_mat
        set rmsd [measure rmsd $compare $reference]
        puts $outfile "$i \t $rmsd"
    }
    close $outfile
}

###############################################################################
# Function: rmsf_sel
# Purpose : Calculates RMSF (Root Mean Square Fluctuation) for the specified selection.
# Arguments:
#   sel          - The atom selection string for RMSF calculation.
#   analysis_dir - Directory where RMSF output will be saved.
###############################################################################
proc rmsf_sel {sel analysis_dir} {
    set str [regsub -all {\s+} $sel "_"]
    set outfile [open "$analysis_dir/RMSF_${str}.dat" w]
    set all [atomselect top all]
    set reference [atomselect top "$sel" frame 0]
    set sele [atomselect top "$sel"]
    set N [molinfo top get numframes]

    # Iterate over each frame to fit the selection to the reference.
    for {set i 0} {$i < $N} {incr i} {
        $all frame $i
        set trans_mat [measure fit $sele $reference]
        $all move $trans_mat
    }

    # Calculate RMSF across all frames.
    set rmsf [measure rmsf $sele first 0 last -1 step 1]

    # Write RMSF values to the output file.
    for {set i 0} {$i < [$sele num]} {incr i} {
        puts $outfile "[expr {$i+1}] [lindex $rmsf $i]"
    }
    close $outfile
}

###############################################################################
# Function: rgyr_sel
# Purpose : Calculates the Radius of Gyration for the specified selection.
# Arguments:
#   sel          - The atom selection string for Radius of Gyration calculation.
#   analysis_dir - Directory where Radius of Gyration output will be saved.
###############################################################################
proc rgyr_sel {sel analysis_dir} {
    set str [regsub -all {\s+} $sel "_"]
    set output [open "$analysis_dir/RGYR_${str}.dat" w]
    set sel [atomselect top "$sel"]
    set n [molinfo top get numframes]

    # Iterate over each frame to measure Radius of Gyration.
    for {set i 0} {$i < $n} {incr i} {
        molinfo top set frame $i
        set rgyr [measure rgyr $sel]
        puts $output "$i \t $rgyr"
    }
    close $output
}

###############################################################################
# Function: sasa_sel
# Purpose : Calculates SASA (Solvent Accessible Surface Area) for the specified selections.
# Arguments:
#   sel1         - The first atom selection string.
#   sel2         - The second atom selection string.
#   analysis_dir - Directory where SASA output will be saved.
###############################################################################
proc sasa_sel {sel1 sel2 analysis_dir srad} {
    set str1 [regsub -all {\s+} $sel1 "_"]
    set sels [atomselect top "$sel1"]
    set n [molinfo top get numframes]

    if { $sel2 == $sel1 } {
        set output [open "$analysis_dir/SASA_${str1}_${str1}.dat" w]
	# Iterate over each frame to measure SASA.
	for {set i 0} {$i < $n} {incr i} {
	  molinfo top set frame $i
	  set sasa [measure sasa $srad $sels]
	  puts $output "$i \t $sasa"
	}
	close $output

    } else {
	set str2 [regsub -all {\s+} $sel2 "_"]
	set output [open "$analysis_dir/SASA_${str1}_${str2}.dat" w]
	set selres [atomselect top "$sel2"]

	# Iterate over each frame to measure SASA.
	for {set i 0} {$i < $n} {incr i} {
	  molinfo top set frame $i
	  set sasa [measure sasa 2.1 $sels -restrict $selres]
	  puts $output "$i \t $sasa"
	}
	close $output
    }
}

###############################################################################
# Function: contact_surface
# Purpose : computes contact surface areas between two biomolecules (A and B) using SASA method:
# Arguments:
#   sel1         - The first atom selection string.
#   sel2         - The second atom selection string.
#   analysis_dir - Directory where SASA output will be saved.
###############################################################################

proc contact_surface {sel1 sel2 analysis_dir srad} {
    set str1 [regsub -all {\s+} $sel1 "_"]
    set str2 [regsub -all {\s+} $sel2 "_"]
    
    #Hard configuration user settings:
    # Atom selections for molecule A and B
    set selA $sel1
    set selB $sel2
    # Probe radius for SASA calculation (Å)
    set probe $srad
    #Contact distance within A and B
    set dist 6.1
    # Frame range
    set start 0
    set stop -1 
    set step 1
    
    
    
# ==============================================================================================
## Contact Surface calculation function
# ==============================================================================================
    set output [open "$analysis_dir/contact_surface_${str1}_${str2}.dat" w]
    set mol [molinfo top]
    set nframes [molinfo $mol get numframes]
    if {$stop < 0} { set stop [expr {$nframes - 1}] }
    for {set i $start} {$i <= $stop} {incr i $step} {
        molinfo $mol set frame $i
        if {[catch { 
            set selAB [atomselect $mol "$selA and within $dist of $selB"]
            set selBA [atomselect $mol "$selB and within $dist of $selA"]
	    set selAUB [atomselect [molinfo top] "index [$selAB get index] [$selBA get index]"]
	    set sasaAB [measure sasa $probe $selAB -points no]
	    set sasaBA [measure sasa $probe $selBA -points no]
	    set sasaAUB [measure sasa $probe $selAUB -points no]
	    set surface [expr {0.5 * ($sasaAB + $sasaBA - $sasaAUB)}] } return] } {
	    puts $output $i\t0 } else {
	    puts $output $i\t$surface
	    puts "[format "Computing contact surface: %.2f%%" [expr {100.0 * ($i + 1) / $nframes}]]"
	    }
    }    
    close $output
}

###############################################################################
# Function: distance_sel
# Purpose : Calculates the distance between two selections over all frames.
# Arguments:
#   sel1         - The first atom selection string.
#   sel2         - The second atom selection string.
#   analysis_dir - Directory where distance output will be saved.
###############################################################################
proc distance_sel {sel1 sel2 analysis_dir} {
    set str1 [regsub -all {\s+} $sel1 "_"]
    set str2 [regsub -all {\s+} $sel2 "_"]
    set output [open "$analysis_dir/distance_${str1}_${str2}.dat" w]
    set selA [atomselect top "$sel1"]
    set selB [atomselect top "$sel2"]
    set n [molinfo top get numframes]

    # Iterate over each frame to calculate distance between selections.
    for {set i 0} {$i < $n} {incr i} {
        molinfo top set frame $i
        set com1 [measure center $selA weight mass]
        set com2 [measure center $selB weight mass]
        set simdata($i.r) [veclength [vecsub $com1 $com2]]
        puts $output "$i \t $simdata($i.r)"
    }
    close $output
}

###############################################################################
# Function: rdf_sel
# Purpose : Calculates RDF (Radial Distribution Function) for the specified selections.
# Arguments:
#   sel1         - The first atom selection string.
#   sel2         - The second atom selection string.
#   rsel         - The maximum radius to calculate RDF.
#   analysis_dir - Directory where RDF output will be saved.
###############################################################################
proc rdf_sel {sel1 sel2 rsel analysis_dir} {
    set aux1 [atomselect top "$sel1"]
    set aux2 [atomselect top "$sel2"]

    # Calculate g(r) using VMD's measure gofr command.
    set gr [measure gofr $aux1 $aux2 first 0 last -1 step 1 usepbc FALSE rmax $rsel]

    # Prepare the output file with headers.
    set str1 [regsub -all {\s+} $sel1 "_"]
    set str2 [regsub -all {\s+} $sel2 "_"]
    set outfile [open "$analysis_dir/rdf_${str1}_${str2}.dat" w]
    puts $outfile "r\tg\tintegral\tnnintegral"

    # Determine the number of data points.
    set nf [llength [lindex $gr 0]]

    # Iterate over each data point to write RDF values.
    for {set i 0} {$i < $nf} {incr i} {
        # Extract distance and RDF values.
        set r [lindex [lindex $gr 0] $i]
        set g [lindex [lindex $gr 1] $i]
        set inte [lindex [lindex $gr 2] $i]
        set ng [lindex [lindex $gr 3] $i]
        # Write formatted RDF data to the output file.
        puts $outfile [format "%.2f\t%.2f\t%.2f\t%.2f" $r $g $inte $ng]
    }
    close $outfile
}

proc rmsf2pdb_sel {analysis_dir} {

    set outfile "$analysis_dir/RMSF_protein.pdb"
    set reference [atomselect top "sirah_protein or sirah_nucleic or resname MgX or resname CaX or resname ZnX" frame 0]
    set sele [atomselect top "sirah_protein or sirah_nucleic or resname MgX or resname CaX or resname ZnX"]
    set all [atomselect top all]
    set N [molinfo top get numframes]

    for {set i 0} {$i < $N} {incr i} {
      $sele frame $i
      set trans_mat [measure fit $sele $reference]
      $sele move $trans_mat
    }

    set rmsf [measure rmsf $sele first 0 last -1 step 1]

    for {set i 0} {$i < [$sele num]} {incr i} {
      set getindex [atomselect top "index $i" frame 0]
      $getindex set beta [lindex $rmsf $i]
      $getindex delete
    }

    # Write pdb file:
    $all writepdb $outfile
}

###############################################################################
# Function: main
# Purpose : The main procedure that orchestrates the execution of selected analyses.
# Arguments:
#   topology_file   - Path to the topology file.
#   trajectory_file - Path to the trajectory file.
#   sel             - Primary atom selection string.
#   sel1            - Secondary atom selection string.
#   sel2            - Tertiary atom selection string.
#   analysis_code   - Integer code representing selected analyses (bitwise flags).
#   script_dir      - Directory where additional TCL scripts are located.
#   analysis_dir    - Directory where analysis output files will be saved.
#   reference_file  - Path to the reference file (optional).
#   skip            - Skip frames into load trajectory
#   srad            - Probe radius for SASA analysis
#   rmsf2pdb        - Enable or disable writing a pdb file with RMSF values in beta column
###############################################################################

proc main {topology_file trajectory_file sel sel1 sel2 analysis_code
           script_dir analysis_dir reference_file skip srad} {

    global rmsf2pdb

    # --------------------------------------------------
    # Load the molecular data into VMD
    # --------------------------------------------------
    
    puts ""
    puts "###################################################"
    puts "Loading trajectory and topology file ..........."
    puts "###################################################"
    load_molecules $topology_file $trajectory_file $reference_file $skip
    puts ""

    # Validate 'sel' if RMSD, RMSF, or Radius of Gyration is selected.
    if {($analysis_code & 1) == 1 || ($analysis_code & 2) == 2 || ($analysis_code & 4) == 4} {
        validate_selection "sel" $sel
    }

    # Validate 'sel1' and 'sel2' if SASA, Distance, Contact Surface or RDF is selected.
    if { (($analysis_code & 8)  == 8)  || (($analysis_code & 16) == 16) || (($analysis_code & 32) == 32) || (($analysis_code & 64) == 64) } {
        validate_selection "sel1" $sel1
        validate_selection "sel2" $sel2
    }

    # -------------------------
    # Execute the analyses
    # -------------------------
    
    if {($analysis_code & 1) == 1} {
        puts ""
        puts "Calculating RMSD ..............................."
        puts ""
        rmsd_sel $sel $analysis_dir
    }
    if {($analysis_code & 2) == 2} {
        puts ""
        puts "Calculating RMSF ..............................."
        puts ""
        rmsf_sel $sel $analysis_dir
    }
    if {($analysis_code & 4) == 4} {
        puts ""
        puts "Calculating Radius of Gyration ................."
        puts ""
        rgyr_sel $sel $analysis_dir
    }
    if {($analysis_code & 8) == 8} {
        puts ""
        puts "Calculating SASA ..............................."
        puts ""
        sasa_sel $sel1 $sel2 $analysis_dir $srad
    }
    if {($analysis_code & 16) == 16} {
        puts ""
        puts "Calculating Distance ..........................."
        puts ""
        distance_sel $sel1 $sel2 $analysis_dir
    }
    if {($analysis_code & 32) == 32} {
        puts ""
        puts "Calculating RDF ..............................."
        puts ""
        rdf_sel $sel1 $sel2 12 $analysis_dir
    }

    if {($analysis_code & 64) == 64} {
        puts ""
        puts "Calculating Contact Surface ..."
        puts ""
        contact_surface $sel1 $sel2 $analysis_dir $srad
    }

    if {$rmsf2pdb == 1} {
        puts ""
        puts ""
        puts "*****************************************************************************************************************"
        puts ""
        puts "Calculating RMSF into beta factor pdb column .............."
        puts ""
        animate delete all
        load_molecules $topology_file $trajectory_file $reference_file $skip
        rmsf2pdb_sel $analysis_dir
        puts ""
        puts "*****************************************************************************************************************"
        puts ""
        puts ""
    }

    # Close VMD after completing the calculations.
    quit
}

# Call the main function with the provided arguments.
main $topology_file $trajectory_file $sel $sel1 $sel2 $analysis_code $script_dir $analysis_dir $reference_file $skip $srad

# Exit the script.
quit
exit 0
