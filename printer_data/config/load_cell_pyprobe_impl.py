toolhead = printer.lookup_object("toolhead")
gcode = printer.lookup_object("gcode")
reactor = printer.get_reactor()
lc = printer.lookup_object("load_cell_probe")._load_cell

STEP = 0.02
FEED = 120
SETTLE = 0.05

# Sharp single-step trigger.
TRIGGER_DF = 10.0

# Persistent slope trigger.
SLOPE_MIN_DF = 1.5
SLOPE_WINDOW = 4
SLOPE_MIN_HITS = 3
SLOPE_SUM_DF = 8.0

# Positive dF integral trigger, gated by a recent peak.
INTEGRAL_MIN_DF = 1.0
INTEGRAL_SUM_DF = 4.5
INTEGRAL_DECAY = 0.5
INTEGRAL_PEAK_DF = 3.0

MAX_FORCE = 200.0
IGNORE_SAMPLES = 5

RETRACT = 0.20
MAX_DEPTH = -0.80

prev = None
i = 0
df_history = []
df_integral = 0.0
df_peak = 0.0

base = lc._force_g()["force_g"]

while True:
    pos = toolhead.get_position()
    z = pos[2]

    raw_f = lc._force_g()["force_g"]
    f = raw_f - base
    df = 0.0 if prev is None else f - prev

    if prev is not None:
        df_history.append(df)
        if len(df_history) > SLOPE_WINDOW:
            df_history.pop(0)

        if i >= IGNORE_SAMPLES:
            if df >= INTEGRAL_MIN_DF:
                df_integral += df
                if df > df_peak:
                    df_peak = df
            else:
                df_integral *= INTEGRAL_DECAY
                df_peak *= INTEGRAL_DECAY

    gcmd.respond_info(
        "i=%02d Z=%.4f F=%.1f raw=%.1f dF=%.1f int=%.1f peak=%.1f"
        % (i, z, f, raw_f, df, df_integral, df_peak)
    )

    if abs(f) >= MAX_FORCE:
        gcmd.respond_info(
            "PYPROBE SAFETY ABORT Z=%.4f F=%.1f raw=%.1f"
            % (z, f, raw_f)
        )
        gcode.run_script_from_command(
            "G91\nG1 Z%.3f F%d\nG90" % (RETRACT, FEED)
        )
        toolhead.wait_moves()
        break

    triggered = False
    trigger_reason = ""

    if i >= IGNORE_SAMPLES and prev is not None:
        if df >= TRIGGER_DF:
            triggered = True
            trigger_reason = "hard_df"

        elif df_integral >= INTEGRAL_SUM_DF and df_peak >= INTEGRAL_PEAK_DF:
            triggered = True
            trigger_reason = (
                "integral sum_dF=%.1f peak_dF=%.1f"
                % (df_integral, df_peak)
            )

        elif len(df_history) == SLOPE_WINDOW:
            hits = sum(1 for x in df_history if x >= SLOPE_MIN_DF)
            sum_df = sum(df_history)

            if hits >= SLOPE_MIN_HITS and sum_df >= SLOPE_SUM_DF:
                triggered = True
                trigger_reason = (
                    "slope hits=%d/%d sum_dF=%.1f"
                    % (hits, SLOPE_WINDOW, sum_df)
                )

    if triggered:
        gcmd.respond_info(
            "PYPROBE TRIGGER %s Z=%.4f F=%.1f raw=%.1f dF=%.1f int=%.1f peak=%.1f"
            % (trigger_reason, z, f, raw_f, df, df_integral, df_peak)
        )
        gcode.run_script_from_command(
            "G91\nG1 Z%.3f F%d\nG90" % (RETRACT, FEED)
        )
        toolhead.wait_moves()

        pos2 = toolhead.get_position()
        gcmd.respond_info("PYPROBE RETRACTED Z=%.4f" % (pos2[2],))
        break

    if z <= MAX_DEPTH:
        gcmd.respond_info("PYPROBE ABORT: max depth reached Z=%.4f" % (z,))
        gcode.run_script_from_command(
            "G91\nG1 Z%.3f F%d\nG90" % (RETRACT, FEED)
        )
        toolhead.wait_moves()
        break

    prev = f
    i += 1

    gcode.run_script_from_command(
        "G91\nG1 Z-%.3f F%d\nG90" % (STEP, FEED)
    )
    toolhead.wait_moves()
    reactor.pause(reactor.monotonic() + SETTLE)
