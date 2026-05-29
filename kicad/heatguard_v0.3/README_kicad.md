# Plugins used

* https://github.com/bennymeg/JLC-Plugin-for-KiCad

  JLC PCB Plug-in for KiCad

  Fill Symbol Field `JLC Part`

* kicad-action-scripts

  ViaStiching, https://github.com/jsreynaud/kicad-action-scripts

## Production

### Increment version number

Update in all sheets (`*.kicad_*`)

`(date "2025-09-02")`

`(rev "0.5")`

### In schematics - final check

Menu `Inspect -> Electrical Rule Chacker`, button `Run ERC`, No violatons

### In pcb - ViaStiching

* remove

  Select one via (which will select a group) and delete

* stich

  PCB -> Toolbar -> Via Stitching Generator

  | Parameter | Value |
  | - | - |
  | Via copper size | 0.5 |
  | Via drill size | 0.3 |
  | Via clearance | 0.15 |
  | Via grid | 10.0 |
  | Net name | GND |
  | Pattern | Rectangular |
  | Checkboxes | Uncheck |



### In pcb - final check and final commit

Menu `Tools -> Cleanup Tracks & Vias`, select all,  `Build Changes`, No violatons

Menu `Inspect -> Design Rules Checker`, check `Refill all zones`, button `Run DRC . No errors, no warnings.

Delete all files in directory `production`.

Icon `Fabricaton Toolkit`, Options empty, check `Apply automatic translatons`, check `Exluce DNP components`.

Rename production folder and add version number

### Print schematics

Schematics, Menu `File -> Print`, check 'Print drawing sheet - Color`, `Print`, `All Pages`, `Print to File`.

Move `~/Documents/output.pdf` to `kicad/heatguard_v0.1/production_v0.1/schematics_heatguard_v0.1.pdf`

### Upload to JLCPCB

Tooling holes: `Added by Customer`

Accept these warnings:
```
The below parts won't be assembled due to data missing.
J2,J3,J4,J5,J6,J7,U4 designators don't exist in the BOM file.
```
BOM

 * Verify that the correct values, specially C and R, have been choosen.
 * ...

Manual correction

 * ...

