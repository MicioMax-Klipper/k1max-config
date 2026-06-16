# K1 Max PRTouch / Cartographer configuration

Experimental configuration for a rooted Creality K1 Max using:

- Cartographer for mesh / bed mapping.
- Creality PRTouch v2 for final Z touch.
- A patched Klipper host branch.
- Creality-style bed firmware.

This config is specific to my machine layout and should be treated as a working
example, not as a universal drop-in config.

## Matching repositories

Use the three matching branches:

- Config:
  - repo: https://github.com/MicioMax-Klipper/k1max-config.git
  - branch: mdf-prtouch-creality-config

- Host Klipper:
  - repo: https://github.com/MicioMax-Klipper/klipper.git
  - branch: mdf-prtouch-creality-host

- Bed firmware:
  - repo: https://github.com/MicioMax-Klipper/k1-klipper-firmware.git
  - branch: k1max-creality-prtouch-bed

## Main peculiarities

This config is built around the following idea:

- Cartographer does the bed mesh.
- Creality PRTouch v2 does the final Z touch.
- The old MDF / Pellcorp load-cell probe path is disabled in this branch.

The known-good order in START_PRINT is:

1. heat bed and start hotend heating
2. wait for bed temperature
3. optional bed warp stabilisation
4. final hotend wait
5. PRTouch nozzle prep
6. Cartographer bed mesh
7. PRTouch final Z home
8. line purge
9. print

The final PRTouch Z home happens after the Cartographer mesh. This is important.

## Nozzle preparation

The macro _PRTOUCH_PREP_NOZZLE does:

- heat the nozzle to at least 180 C if it is cold
- retract to relieve pressure
- run PRTOUCH_HOME_Z_COARSE
- run the silicone brush / nozzle wipe macro

The wipe macro is tuned for my rear silicone brush position. Check the brush,
Cartographer clearance, and nozzle path before using it blindly.

## Z offset

The PRTOUCH_HOME_Z macro applies a small G-code Z offset after ACCURATE_HOME_Z.

Current tested baseline on my printer:

    variable_z_offset: 0.05

Higher values move the nozzle farther from the bed. Lower values move it closer.

## Bed warp stabilisation switch

The config contains a virtual output pin:

    Bed_Warp_Stabilisation

START_PRINT reads it and _WARP_STABILISE respects it.

The config also saves the value seen at START_PRINT and restores it after a
restart using save_variables and delayed_gcode. This is not magic: it remembers
the value used at print start, not every GUI click in real time.

## Line purge

The _LINE_PURGE macro is a simple Creality-style left-side double purge line,
with a small retract before leaving the purge area.

## GuppyScreen

grumpyscreen.ini is included because the active GuppyScreen symlink points to:

    /usr/data/printer_data/config/grumpyscreen.ini

## Brutal install outline

Backup your existing configuration first.

On the K1 Max:

    /etc/init.d/S55klipper_service stop

    cd /usr/data/printer_data
    mv config config.backup.$(date +%Y%m%d_%H%M%S)

    git clone https://github.com/MicioMax-Klipper/k1max-config.git config_repo
    cd /usr/data/printer_data/config_repo
    git checkout mdf-prtouch-creality-config

Create the active config symlink:

    cd /usr/data/printer_data
    ln -sfn /usr/data/printer_data/config_repo/printer_data/config config

Then restart Klipper according to your installation.

## Warning

Do not blindly use this on another K1 Max without checking:

- Cartographer offsets and position.
- Brush / silicone wipe coordinates.
- bed mesh area.
- filament sensor config.
- START_PRINT parameters.
- firmware/host branch compatibility.
