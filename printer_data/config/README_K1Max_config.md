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

Current START_PRINT behaviour:

- Before bed mesh, the nozzle is kept at a low pre-mesh temperature.
- The nozzle is not wiped or PRTouch-probed before the mesh.
- After bed mesh, START_PRINT prepares the nozzle immediately before the final Z reference.
- For the normal Cartographer-mesh + PRTouch-ZTOUCH flow, the nozzle is heated to final print temperature, wiped with _NOZZLE_WIPE_SILICONE, then Z_TOUCH is run.
- _LINE_PURGE reloads the nozzle immediately before printing.

The old PRTouch pre-mesh nozzle-prep macros were removed.
The live nozzle-cleaning primitive is _NOZZLE_WIPE_SILICONE.

## Z offset

PRTOUCH_HOME_Z now dispatches to _Z_PRTOUCH / Z_PRTOUCH.
Z_PRTOUCH is implemented by klippy/extras/prtouch_z.py and bakes the fixed offset into kinematic Z, keeping Fluidd's G-code offset clean.

Current tested baseline on my printer:

    variable_z_offset: 0.00

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

## Probe manager and custom Cartographer mount

This configuration uses `probe_manager.cfg` and `probe_select.cfg` to dispatch
homing, final Z touch, and bed mesh between different probes.

Current tested default on my printer:

    PROBE_SELECT HOME=cartographer ZTOUCH=prtouch MESH=cartographer

Meaning:

- Cartographer is used for Z homing.
- Cartographer is used for bed mesh.
- Creality PRTouch is used for the final Z reference before printing.

Do not remove or bypass the probe manager macros unless you also rewrite
`START_PRINT`, `Z_TOUCH`, and the homing dispatch logic.

### Custom Cartographer offset

My Cartographer is mounted on a custom support.

Current tested offset on my printer:

    [cartographer]
    x_offset: -21.0
    y_offset: 0.0

This is not a stock/default offset. It depends on the physical mount.

The bed mesh area is limited accordingly:

    [bed_mesh]
    mesh_min: 10,10
    mesh_max: 278,270

Do not copy these values blindly to another printer. Measure your own
Cartographer nozzle/probe offset and verify that all mesh points are reachable
before running homing, probing, mesh, or `START_PRINT`.

Wrong Cartographer offsets or mesh limits can cause move-out-of-range errors,
bad probing positions, nozzle/bed contact, or mechanical crashes.

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

- Cartographer physical mount and `x_offset` / `y_offset`.
- Reachable bed mesh area for the selected probe.
- `PROBE_SELECT` defaults in `probe_manager.cfg`.
- Whether final `Z_TOUCH` is Cartographer or PRTouch.
- Brush / silicone wipe coordinates.
- Plate/material Z offset macro.
- Filament sensor config.
- `START_PRINT` parameters.
- Firmware/host branch compatibility.
