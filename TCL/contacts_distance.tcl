# contacts_distance.tcl
#
# This TCL script is designed to perform contacts analyses using VMD (Visual Molecular Dynamics) based on user-selected atom selections.
#
# Usage:

#vmd -dispdev text -e tcl_script_path -args topology_file
#                                           trajectory_file
#                                           selection1
#                                           selection2
#                                           skip
#                                           cutoff
#                                           contacts_dir
#                                           calc_distance_matrix_value
#                                           reference_file_value
#                                           sirah_tcl_path
# Arguments:
# 1. topology file                - Path to the topology file.
# 2. trajectory file              - Path to the trajectory file.
# 3. selection 1                  - Primary atom selection using VMD syntax.
# 4. selection 2                  - Secondary atom selection using VMD syntax.
# 5. skip value                   - Skip for load trajectory   
# 6. cutoff distance              - Cutoff distance for contact calculation. 
# 7. contacts_dir                 - Directory where analysis output files will be saved (output_dir).
# 8. calculate distance matrix    - If 1 enable distance matrix calculation. 
# 9. reference file               - Path to the reference file (optional).    
# 10. sirah_tcl_path              - Path to the sirah_vmdtk.tcl script

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
puts "║                    CONTACTS ANALYSIS                ║"
puts "╚═════════════════════════════════════════════════════╝"
puts ""
puts "Starting Contacts analysis............................."
puts ""


puts ""
puts "Arguments: "
puts "---------------------------------------------------------------------------------------------"
set topology_file [lindex $argv 0]
set trajectory_file [lindex $argv 1]
set selection1 [lindex $argv 2]
set selection2 [lindex $argv 3]
set skip [lindex $argv 4]
set cutoff [lindex $argv 5]   ;# Capture the cutoff value
set output_dir [lindex $argv 6]
set distance_matrix_flag [lindex $argv 7]
set reference_file [lindex $argv 8]
set script_dir [lindex $argv 9]
puts "---------------------------------------------------------------------------------------------"
puts ""

# Print the script and analysis directories for debugging.
puts ""
puts "Script Directory: "
puts "---------------------------------------------------------------------------------------------"
puts "$script_dir"
puts "---------------------------------------------------------------------------------------------"
puts ""

# Source the additional TCL script 'sirah_vmdtk.tcl' from the provided script directory.
puts ""
puts "Loading sirah_vmdtk.tcl from:" 
puts "---------------------------------------------------------------------------------------------"
set  vmdtk_path [file join $script_dir "sirah_vmdtk.tcl"]
#puts "$vmdtk_path"
puts "---------------------------------------------------------------------------------------------"
puts ""
source $vmdtk_path
puts "---------------------------------------------------------------------------------------------"


###############################################################################
# Function: validate_selection
# Purpose : Validates an atom selection to ensure it is syntactically correct
#           and selects at least one atom.
# Arguments:
#   selection_name - A label for the selection (e.g., "selection1", "selection2").
#   selection      - The atom selection string in VMD syntax.
#
# If the selection is invalid (syntax error or zero atoms selected),
# an error message is printed within a prominent '#' box, and the script exits.
###############################################################################
proc validate_selection {selection_name selection} {
    set atom_select_obj ""
    # Attempt to create an atomselect object; catch any syntax errors.
    set err_code [catch {set atom_select_obj [atomselect top "$selection"]} err_msg]
    if {$err_code} {
        puts "#############################################"
        puts "# Error: Invalid selection syntax for '$selection_name'. #"
        puts "# Details: $err_msg                               #"
        puts "#############################################"
        exit 1
    }

    # Check if the selection includes zero atoms.
    if {[$atom_select_obj num] == 0} {
        puts "#############################################"
        puts "# Error: Your selection '$selection_name' is invalid, it has zero atoms. #"
        puts "#############################################"
        exit 1
    }

    # Clean up the atomselect object to free resources.
    $atom_select_obj delete
}

# Main process - Native Contacts with memory and performance optimization
proc get_contacts {topology_file trajectory_file selection1 selection2 skip cutoff output_dir distance_matrix_flag reference_file} {

    set str1 [regsub -all {\s+} $selection1 ""]
    set str2 [regsub -all {\s+} $selection2 ""]

    # Load the topology
    puts ""
    puts "Loading topology file:" 
    puts "---------------------------------------------------------------------------------------------"
    puts "$topology_file"
    puts "---------------------------------------------------------------------------------------------"
    puts ""
    mol new $topology_file waitfor all
    puts "---------------------------------------------------------------------------------------------"
    puts ""

    # Load the trajectory
    puts ""
    puts "Loading trajectory file: "
    puts "---------------------------------------------------------------------------------------------"
    puts "$trajectory_file"
    puts "---------------------------------------------------------------------------------------------"
    puts ""
    puts "This may take a few minutes.........."
    puts "Loading.............................."
    puts ""
    puts ""
    if { $reference_file == "None" } {
        mol addfile $trajectory_file first 0 last -1 step $skip waitfor all
    } else {
        mol addfile $reference_file waitfor all
        mol addfile $trajectory_file first 0 last -1 step $skip waitfor all
    }
    puts ""
    puts ""
    puts "Trajectory loaded successfully"
    puts "---------------------------------------------------------------------------------------------"
    puts ""
    puts ""

    set mol_id [molinfo top]

    # Verify the number of frames
    set num_frames [molinfo $mol_id get numframes]
    puts "________________________________________"
    puts "Number of Frames: $num_frames"
    puts "$distance_matrix_flag"
    puts "________________________________________"
    puts ""
    if {$num_frames == 0} {
        puts "Error: No frames found in the trajectory."
        return
    }
    
    validate_selection "selection1" $selection1
    validate_selection "selection2" $selection2

    # Start the timer
    set start_time [clock seconds]

    # Initialize output files
    set output_file [open "$output_dir/contacts_${str1}_${str2}.dat" w]
    set timeline_file [open "$output_dir/timeline_${str1}_${str2}.dat" w]
    set intertime_file [open "$output_dir/intertime_${str1}_${str2}.dat" w]

    # Obtain reference contacts
    puts ""
    puts "Obtaining reference contacts"
    puts ""

    set initial_contact_list {}
    set initial_contact_residues {}

    # Select and store contacts only for frame 0
    set selection1_atoms [atomselect top "$selection1"]
    set selection2_atoms [atomselect top "$selection2"]

    $selection1_atoms frame 0
    $selection2_atoms frame 0
    set initial_contacts [measure contacts $cutoff $selection1_atoms $selection2_atoms]

    # Store initial contacts in memory
    foreach x [lindex $initial_contacts 0] y [lindex $initial_contacts 1] {
        if {$x < $y} {
            lappend initial_contact_list "${x}_${y}"
        } else {
            lappend initial_contact_list "${y}_${x}"
        }
        set atom1 [atomselect top "index $x"]
        set atom2 [atomselect top "index $y"]
        set resid1 [$atom1 get resid]
        set resid2 [$atom2 get resid]
        set name1 [$atom1 get name]
        set name2 [$atom2 get name]
        if {$resid1 < $resid2} {
            puts $intertime_file "${resid1}_${name1}_${resid2}_${name2}"
        } else {
            puts $intertime_file "${resid2}_${name2}_${resid1}_${name1}"
        }
        $atom1 delete
        $atom2 delete
    }

    puts ""
    puts "---------------------------------------"
    puts "Searching for contacts.... please wait"
    puts "---------------------------------------"
    puts ""

    # Statistics
    set tc_ref [llength $initial_contact_list]
    set sum_pcc 0
    set sum_pcc_squared 0
    set sum_acc 0
    set sum_acc_squared 0
    set sum_tc 0
    set sum_tc_squared 0

    puts $timeline_file "# frame\tCons(%)\tAcc(%)\tCont\tNative\tNonNative"
    puts $timeline_file "  0    \t100.0  \t100.0  \t$tc_ref \t$tc_ref \t0"

    # Write the number of residues to a file named "contacts_length.dat"
    set num_sel1_atoms [$selection1_atoms num]
    set num_sel2_atoms [$selection2_atoms num]
    set length_file [open "$output_dir/contacts_length_${str1}_${str2}.dat" w]
    puts $length_file "selection1 \"$selection1\" $num_sel1_atoms"
    puts $length_file "selection2 \"$selection2\" $num_sel2_atoms"
    close $length_file

    puts ""
    puts ""
    puts "--------------------------------------------------------------------------------------------"
    puts ""
    puts "Number of residues: $num_sel1_atoms (written to contacts_length.dat)"
    puts "--------------------------------------------------------------------------------------------"
    puts ""
    
    # GC-CC distance for frame 0
    if { ([string first "name" $selection1] >= 0 || [string first "index" $selection1] >= 0 || [string first "serial" $selection1] >= 0) && ([string first "and" $selection1] < 0  && [string first "or" $selection1] < 0) } {
        # Condition 0
        set sel_aux [atomselect top "$selection1"]
        set num_atoms [$sel_aux num]
        set num_unique_residues [llength [lsort -unique [$sel_aux get residue]]]
        if {$num_atoms == $num_unique_residues} {
            set selA [atomselect top "$selection1"]
        } else {
            set selA [atomselect top "($selection1) and (name GC or name PX or name BFO or name CA)"]
        }
    } elseif { ([string first "name" $selection1] >= 0 || [string first "index" $selection1] >= 0 || [string first "serial" $selection1] >= 0) && ([string first "and" $selection1] >= 0  && [string first "or" $selection1] < 0) } {
        # Condition 1
        set sel_aux [atomselect top "$selection1"]
        set num_atoms [$sel_aux num]
        set num_unique_residues [llength [lsort -unique [$sel_aux get residue]]]
        if {$num_atoms == $num_unique_residues} {
            set selA [atomselect top "$selection1"]
        } else {
            set selected_residues [lsort -unique [$sel_aux get residue]]
            set selA [atomselect top "residue $selected_residues and (name GC or name PX or name BFO or name CA)"]
        }
    } else {
        # Condition 2
        set selA [atomselect top "($selection1) and (name GC or name PX or name BFO or name CA)"]
    }
    
    if { ([string first "name" $selection2] >= 0 || [string first "index" $selection2] >= 0 || [string first "serial" $selection2] >= 0) && ([string first "and" $selection2] < 0  && [string first "or" $selection2] < 0) } {
        # Condition 0
        set sel_aux [atomselect top "$selection2"]
        set num_atoms [$sel_aux num]
        set num_unique_residues [llength [lsort -unique [$sel_aux get residue]]]
        if {$num_atoms == $num_unique_residues} {
            set selB [atomselect top "$selection2"]
        } else {
            set selB [atomselect top "($selection2) and (name GC or name PX or name BFO or name CA)"]
        }
    } elseif { ([string first "name" $selection2] >= 0 || [string first "index" $selection2] >= 0 || [string first "serial" $selection2] >= 0) && ([string first "and" $selection2] >= 0  && [string first "or" $selection2] < 0) } {
        # Condition 1
        set sel_aux [atomselect top "$selection2"]
        set num_atoms [$sel_aux num]
        set num_unique_residues [llength [lsort -unique [$sel_aux get residue]]]
        if {$num_atoms == $num_unique_residues} {
            set selB [atomselect top "$selection2"]
        } else {
            set selected_residues [lsort -unique [$sel_aux get residue]]
            set selB [atomselect top "residue $selected_residues and (name GC or name PX or name BFO or name CA)"]
        }
    } else {
        # Condition 2
        set selB [atomselect top "($selection2) and (name GC or name PX or name BFO or name CA)"]
    }
    #set selA [atomselect top "$selection1 and (name GC or name PX or name BFO)"]
    #set selB [atomselect top "$selection2 and (name GC or name PX or name BFO)"]
    set num_selA_atoms [$selA num]
    set num_selB_atoms [$selB num]
    set distance_length_file [open "$output_dir/distance_length_${str1}_${str2}.dat" w]
    puts $distance_length_file "selection1 \"$selection1\" $num_selA_atoms"
    puts $distance_length_file "selection2 \"$selection2\" $num_selB_atoms"
    close $distance_length_file
    if {$distance_matrix_flag == 1} {
        set dist_by_frame [open "$output_dir/distbyframe_${str1}_${str2}.dat" w]
        set dist [distance_matrix $selA $selB $num_selA_atoms $num_selB_atoms 0]
        puts $dist_by_frame "0 $dist"
        flush $dist_by_frame
    }

    # Process contacts per frame
    for {set i 1} {$i < $num_frames} {incr i} {
        $selection1_atoms frame $i
        $selection2_atoms frame $i

        # Process contacts in frame i
        set contacts_i [measure contacts $cutoff $selection1_atoms $selection2_atoms]
        set tc_i [llength [lindex $contacts_i 0]]
        set cc_i [search_contact $initial_contact_list $contacts_i]
        set pcc_i [expr {100.0 * $cc_i / $tc_ref}]
        if {$tc_i > 0} {
            set acc_i [expr {100.0 * $cc_i / $tc_i}]
        } else {
            set acc_i 0
        }

        # Accumulate statistics
        set sum_pcc [expr { $sum_pcc + $pcc_i }]
        set sum_pcc_squared [expr { $sum_pcc_squared + $pcc_i**2 }]
        set sum_acc [expr { $sum_acc + $acc_i }]
        set sum_acc_squared [expr { $sum_acc_squared + $acc_i**2 }]
        set sum_tc [expr { $sum_tc + $tc_i }]
        set sum_tc_squared [expr { $sum_tc_squared + $tc_i**2 }]

        puts $timeline_file [format "  %d\t%5.1f\t%5.1f\t%d\t%d\t%d" $i $pcc_i $acc_i $tc_i $cc_i [expr { $tc_i - $cc_i }]]

        # Save contacts to file
        foreach x [lindex $contacts_i 0] y [lindex $contacts_i 1] {
            set atom1 [atomselect top "index $x"]
            set atom2 [atomselect top "index $y"]
            set resid1 [$atom1 get resid]
            set resid2 [$atom2 get resid]
            set name1 [$atom1 get name]
            set name2 [$atom2 get name]
            if {$resid1 < $resid2} {
                puts $intertime_file "${resid1}_${name1}_${resid2}_${name2}"
            } else {
                puts $intertime_file "${resid2}_${name2}_${resid1}_${name1}"
            }
            $atom1 delete
            $atom2 delete
        }

        # Show progress
        
        set percent_complete [expr {100.0 * $i / $num_frames}]
        puts -nonewline "\rProgress: [format "%.1f" $percent_complete]%"
        flush stdout
        

        # Calculate distance matrix for frame i
        if {$distance_matrix_flag == 1} {
            set dist [distance_matrix $selA $selB $num_selA_atoms $num_selB_atoms $i]
            puts $dist_by_frame "$i $dist"
            flush $dist_by_frame
        }
    }

    # Close output files
    close $timeline_file
    close $intertime_file
    if {$distance_matrix_flag == 1} {
        close  $dist_by_frame
    }

    # Calculate averages and standard deviations
    set avg_pcc [expr {$sum_pcc / ($num_frames - 1)}]
    set std_pcc [expr {sqrt( ($sum_pcc_squared / ($num_frames - 1)) - ($sum_pcc / ($num_frames - 1))**2)}]
    set avg_acc [expr {$sum_acc / ($num_frames - 1)}]
    set std_acc [expr {sqrt( ($sum_acc_squared / ($num_frames - 1)) - ($sum_acc / ($num_frames - 1))**2)}]
    set avg_tc  [expr {$sum_tc / ($num_frames - 1)}]
    set std_tc  [expr {sqrt( ($sum_tc_squared / ($num_frames - 1)) - ($sum_tc / ($num_frames - 1))**2)}]

    puts ""
    puts "----------------------------------"
    puts "\nContact calculation completed."
    puts $output_file [format "<Conserved contacts> %.1f(%.1f)%% <Accuracy> %.1f(%.1f)%% <Contacts> %.1f(%.1f)" $avg_pcc $std_pcc $avg_acc $std_acc $avg_tc $std_tc]
    close $output_file
    puts "----------------------------------"

    # Read the intertime file to calculate contact percentages
    set intertime_in [open "$output_dir/intertime_${str1}_${str2}.dat" r]
    set percentage_file [open "$output_dir/percentage_${str1}_${str2}.dat" w]

    # Counter for each contact
    set contact_counter {}

    while {[gets $intertime_in line] >= 0} {
        # Increment the counter for each contact
        dict incr contact_counter $line
    }
    close $intertime_in

    puts $percentage_file "Resid 1\tAtom 1\tResid 2\tAtom 2\tFrac(%)\tNFrames"
    # Calculate the percentage of each contact
    dict for {contact count} $contact_counter {
        set percentage [expr {100.0 * $count / $num_frames}]
        # Replace underscores with tabs for formatting
        set contact_formatted [regsub -all {[_]} $contact "\t"]
        puts $percentage_file [format "%s\t%6.1f\t%d" $contact_formatted $percentage $count]
    }

    close $percentage_file

    # Delete the intertime file after use
    file delete "$output_dir/intertime_${str1}_${str2}.dat"

    # End timer and print execution time
    set end_time [clock seconds]
    set exec_time [expr {$end_time - $start_time}]
    puts "\nExecution time: $exec_time seconds."
}

###############################################################################
# Subroutine: search_contact
# Purpose    : Searches for conserved contacts in the current frame based on
#              the reference contact list.
# Arguments:
#   initial_contact_list - List of reference contacts.
#   contacts_frame       - Contacts in the current frame.
# Returns    : Number of conserved contacts.
###############################################################################
proc search_contact {initial_contact_list contacts_frame} {
    set contact_count 0
    foreach atom1 [lindex $contacts_frame 0] atom2 [lindex $contacts_frame 1] {
        if {[lsearch -regexp $initial_contact_list "^${atom1}_${atom2}$"] >= 0 || [lsearch -regexp $initial_contact_list "^${atom2}_${atom1}$"] >= 0} {
            incr contact_count
        }
    }
    return $contact_count
}

###############################################################################
# Subroutine: distance_matrix
# Purpose    : Computes the distance matrix between two selections for a given frame.
# Arguments:
#   selA   - Atom selection A.
#   selB   - Atom selection B.
#   numA   - Number of atoms in selection A.
#   numB   - Number of atoms in selection B.
#   frame  - Frame number.
# Returns    : List of distances formatted to two decimal places.
###############################################################################
proc distance_matrix {selA selB numA numB frame} {
    $selA frame $frame
    $selA update
    $selB frame $frame
    $selB update
    set coordinatesA [$selA get {x y z}]
    set coordinatesB [$selB get {x y z}]
    set distance_map {}

    for {set indexA 0} {$indexA < $numA} {incr indexA} {
        set coordA [lindex $coordinatesA $indexA]
        for {set indexB 0} {$indexB < $numB} {incr indexB} {
            set coordB [lindex $coordinatesB $indexB]
            set distance [vecdist $coordB $coordA]
            lappend distance_map [format "%.2f" $distance]
        }
    }
    return $distance_map
}

# Execute the main process with the provided arguments
get_contacts $topology_file $trajectory_file $selection1 $selection2 $skip $cutoff $output_dir $distance_matrix_flag $reference_file

puts ""
puts ""
puts "╔═════════════════════════════════════════════════════╗"
puts "║               END CONTACTS ANALYSIS                 ║"
puts "╚═════════════════════════════════════════════════════╝"
puts ""
puts ""

quit
