# Native compatibility contract

This is the first bounded consumer probe, before product implementation or UI.

## Official consumer identity

Debian 13/trixie `ardour`, `ardour-data` and `ardour-lv2-plugins`, exact version `1:8.12.0+ds-1`. The workflow uses default authenticated Debian APT metadata without adding trust keys or disabling checks. Before installation/execution it retains each package's full metadata, SHA-256, size and `dpkg-deb` version, then compares downloaded bytes. It records all installed runtime package versions and the actual native Lua interpreter version. The plugin package is a distribution dependency; the probe disables external plugins and supplies an empty instrument pointer.

Upstream tag 8.12 resolves to commit `10517bff2b2c7b882b453296a939cf5d03174831` (tag object `a1bf5c8aa291ec1b815ce7a3c0f8a637ff3c0b71`). Debian may carry distribution patches; the executed consumer identity is the recorded Debian package, not a claim of binary equality to upstream.

## Literal fixture and independent expectations

The native Lua API authors the source, with 48 kHz sample rate, no musical media and no external plugins:

| Quarter | Quarter-note tempo | Meter |
| --- | --- | --- |
| 0 | 120 BPM | 4/4 |
| 8 | 100 BPM | unchanged |
| 16 | 150 BPM | 3/4 |

A separate, literal format-0 MIDI fixture uses PPQN 1920. Tempo events are exactly 500000, 600000 and 400000 microseconds per quarter at ticks 0, 15360 and 30720. Time-signature events are 4/4 and 3/4 at ticks 0 and 30720, clocks-per-click 24 and notated-32nds 8. End-of-track is tick 61440. No channel messages are permitted. This fixture generator is not the future session converter and is labelled accordingly. The independent XML oracle also requires native sample rate 48000 and clock rate 282240000 ticks/second, with point clocks 0, 1128960000 and 2483712000 (0, 4 and 8.8 seconds), plus bar positions 1|1|0, 3|1|0 and 5|1|0.

The target is a separately native-created empty session with only its initial 120 BPM/4/4 map. The official GUI imports the actual MIDI path using `Editor:do_import`, `SMFTempoUse`, and empty plugin/track pointers. The fixed script calls native `TempoMap.read()` and checks real in-memory values at quarters 0, 7, 8, 15, 16 and 24. Native `Session:save_state` writes the result. Python independently checks all saved tempo/meter entries, not only the queried samples. A fresh GUI process repeats the map checks and native save. Both normal GUI exits must return 0; failure cleanup cannot count as success. The original native-authored source hash must remain unchanged.

The native GUI's Scripting console is a test-only means of invoking the unchanged native API. This is not manual-GUI fixture authoring, a copied native parser, or evidence from a rewritten target XML file. The fixed script is pasted as text; no sandbox preference is changed. Screenshots, accessibility trees, logs, original MIDI, native-authored and native-saved XML, and the final report are retained. Only a complete reviewed report can clear this consumer compatibility checkpoint.

The first hosted run reached the normal welcome wizard and passed native fixture authoring, but its accessibility tree exposed only the desktop. The second harness reads actual native control labels with bounded OCR, then clicks their observed coordinates. Raw screenshots, thresholded OCR derivatives, word confidence/geometry and X11 titles are retained. The source-confirmed lower output pane is physically selected and copied only after a fresh clipboard sentinel. Editor/source echoes are rejected, and the six anchored native query lines, standalone completion and native `> OK` are still required. Native XML and fresh-process assertions are unchanged. This repair is an automation route, not a change to the consumer or evidence of successful import.

R3 then completed the wizard and normal first-run exit. Its actual Audio/MIDI menu omitted the bundled Dummy backend. The pinned release source filters it while `hide-dummy-backend` is true. The harness now changes only that ordinary visibility option to false in the newly native-generated `/tmp/beatcourier-native/config/ardour8/config`, while the GUI is closed. Exact before/after synthetic configuration bytes and the one-value delta are retained. This is a disposable test preference; no user profile, system setting, realtime permission, sandbox or consumer code changes. The real GUI must still select and visibly confirm None (Dummy), Normal Speed and Silence before starting.

R4 visibly reached that backend and the editor, where a locked-memory informational dialog blocked the menu. The harness acknowledges only that exact observed warning through its unique native OK button. It does not change memory limits or select the dialog's “Do not show this window again” checkbox. The original screenshot and acknowledgement record remain in evidence. Tesseract TSV is parsed without CSV quote interpretation, so a recognized quotation-mark glyph cannot consume later OCR rows.

R6 reached the unchanged native file-import API and failed the literal tempo assertion at quarter 8. Compatibility has not passed. The diagnostic script now prints all six actual map values and performs the normal native save before checking its expected-value flag, so a mismatch retains the complete consumer-produced map. The host still requires every literal query, the completion marker, the independent XML oracle and fresh-process reload. Saving a failed diagnostic does not count as acceptance, and no session map is rewritten by the harness.

R7's native-saved map retained all three tempo and two meter points at the exact expected quarter, superclock and BBT positions. Its query discrepancy is explained by the pinned `tempo_at`/`meter_at` strict-less-than lookup: exact nonzero boundaries return the preceding segment. The corrected native-query oracle retains the six exact-quarter observations with that documented behavior and additionally requires 100 BPM/4/4 at native tick 15361 and 150 BPM/3/4 at tick 30721, one tick after each changed boundary. The independent XML point oracle is unchanged.

The native importer also creates exactly one terminal `<import` MusicTime marker because it copies through maximum AudioTime and restores the prior end state in `TempoMap::paste`. The output-only oracle enumerates the complete observed marker: superclock4611686018427387903, quarters2147483646:1919, BBT715827881|3|1919, name`<import`, and the exact nested constant120BPM/4/4 attributes. Any other marker, extra attribute, changed value or missing/extra child rejects. Native source fixtures and the intended product input profile still reject nonempty MusicTimes. This distinction means a native-resaved imported session containing that terminal marker is outside the intended input profile. Fresh-process reload remains mandatory; these observations alone are not full acceptance.

## Precision boundary

Ardour 8.12's `Editor::import_smf_tempo_map` rounds MIDI pulses to whole quarter notes with `int_div_round`. The first product profile therefore must reject fractional-quarter changes, including 15.5. Ardour 9.2 instead delegates to `Evoral::SMF::tempo_map`, which constructs fractional native beat ticks. That source finding is not a runtime test of 9.2.

## Work still gated

The complete exporter must separately prove bounded inert XML parsing, constant-tempo and MusicTimes rejection, exact rational SMF mapping, tempo rounding receipts, unchanged original inputs, whole-quarter rejection, and independent faulty-tempo/meter/position controls. The eventual offline browser download must pass the actual consumer gate too. No product UI begins before the full native converter gate is accepted.

## Primary sources

- [Debian stable package](https://packages.debian.org/trixie/ardour) and [installed file list](https://packages.debian.org/trixie/amd64/ardour/filelist)
- [Native 8.12 import](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/gtk2_ardour/editor_audio_import.cc#L276)
- [Official GUI Lua import example](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/share/scripts/s_import_files.lua)
- [Native Lua session tool](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/luasession/luasession.cc)
- [TempoMap XML persistence](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/temporal/tempo.cc#L3286)
- [Native clock-rate initialization](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/temporal/enums.cc#L81)
- [Strict native lookup comparator](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/temporal/temporal/tempo.h#L124) and [lookup implementation](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/temporal/temporal/tempo.h#L875)
- [Importer copies through maximum AudioTime](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/gtk2_ardour/editor_audio_import.cc#L329) and [native paste end-marker creation](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/temporal/tempo.cc#L1097)
- [GUI scripting execution](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/gtk2_ardour/luawindow.cc#L277)
- [First-run wizard and saved marker](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/gtk2_ardour/new_user_wizard.cc#L296)
- [Dummy backend](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/backends/dummy/dummy_audiobackend.cc#L1030)
- [Release-build backend visibility filter](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/ardour/audioengine.cc#L968) and [default visibility preference](https://github.com/Ardour/ardour/blob/10517bff2b2c7b882b453296a939cf5d03174831/libs/ardour/ardour/rc_configuration_vars.h#L198)
- [9.2 fractional SMF conversion](https://github.com/Ardour/ardour/blob/9.2/libs/evoral/SMF.cc#L838)
