# Production-output gate — accepted native checkpoint

The production gate passed at commit d7d3736d3c1ecfdb70b911be2b591db9f24cdab6, run37601909063, artifact11473008636 SHAfb9374b8754c741d782516ab237aa4168d1ca1cd1dbcec45af7c979e2517435c. Independent review verified all503 original members, eight saved/reloaded native cases and120 readings. The accepted R9 checkpoint had already proved the chosen native consumer route. This gate separately tests the production converter output. It preserves the same authenticated packages, disposable XDG/None(Dummy) configuration, physical GUI controls, output-only clipboard proof, unchanged PublicEditor file importer and native Session save/fresh reopen. No arbitrary user session is passed to the consumer.

## Native-authored fixture

The official ardour8-lua authors Source and Fractional through TempoMap.write_copy, native tempo/meter methods, TempoMap.update and Session:save_state. A separate initial Target is also native-authored. This is native-API authoring, not manual GUI authoring.

| Quarter | Source tempo | Meter | Source superclock | BBT |
| --- | --- | --- | --- | --- |
|0 |120 quarter notes/min |4/4 |0 |1\|1\|0 |
|8 |100 quarter notes/min |3/4 |1128960000 |3\|1\|0 |
|14 |150 eighth notes/min |7/8 |2145024000 |5\|1\|0 |
|16 |120 quarter notes/min |unchanged |2596608000 |5\|5\|0 |
|20 |123 quarter notes/min requested |unchanged |3161088000 |6\|6\|0 |
|28 |150 quarter notes/min |4/4 |4262512392 |9\|1\|0 |

Sample rate is48000, native superclocks per second282240000, quarter-note ticks1920. Native123 BPM itself has integer superclock note-duration137678049, so its saved decimal can differ slightly from123. The source oracle independently verifies this duration and the exact native coordinates.

The second native fixture adds a tempo at quarter15.5 under7/8, where a half-quarter is a valid native meter beat. Its saved XML must actually contain15:960. The product must reject it with FRACTIONAL_POSITION and create no output.

## Literal wire and native output

The independent Python oracle contains the complete106-byte expected positive SMF. Its six tempo events are500000,600000,800000,500000,487805,400000 microseconds at quarters0,8,14,16,20,28. Four meter events are4/4,3/4,7/8,4/4 at0,8,14,28. FF58 clocks-per-click24 and notated32nds8 are explicit conductor defaults. End-of-track is quarter29, tick55680. Every event is independently parsed with Mido; channel/note events are forbidden.

Source150 eighth notes/minute converts to75 quarter notes/minute. Imported tempo points use quarter-note units. MIDI's microsecond rounding and Ardour's integer native-clock duration are separately accounted for. For the positive fixture, quarter28 remains exact while its target superclock is4262512664,272 later than the source (17/17640000 second, about0.964 microsecond). Every receipt row must match independent Fraction arithmetic, including source/output hashes. No exact wall-clock preservation claim is made after tempo rounding.

The real importer receives the actual file produced by src/session.mjs, not a substitute fixture. All six tempo and four meter points, their native clocks and BBT positions are checked after native save and again in a new process. Fifteen actual native queries cover exact boundaries, immediately following ticks and interior/end positions. Source bytes remain unchanged. Each normal process exit must be0; nonfatal GTK/GObject diagnostics remain in the report.

## Fault controls

Each MIDI fault is derived from the actual positive output, independently checked against its exact expected event set, and imported into a fresh copy of the native-authored initial Target. Both import and fresh reload must show the intended fault and reject the unchanged positive oracle:

- Only final tempo at quarter28 changes150→100 BPM
- Only final meter at quarter28 changes4/4→5/4
- Only the tempo event at quarter16 moves to17; other absolute event coordinates stay fixed. The native point, BBT and subsequent clocks must change exactly

The core also rejects labelled synthetic input mutations for unequal npm/enpm, nonzero omega, nonempty MusicTimes, corrupted BBT and an unrepresentable tempo. These mutated XML files are never executed by Ardour. Unit tests cover malformed XML, size/resource limits and native signed-byte bounds.

## Enumerated native normalization

The importer pastes through maximum AudioTime and adds exactly one terminal `<import` MusicTime. Just-imported quarters must be2147483646:1919; fresh-reloaded quarters must be2147483647:0. Its superclock is4611686018427387903. With the fixed final4/4 beginning at quarter28/bar9, terminal BBT is536870913|3|1919. The final5/4 fault instead requires429496732|4|1919. Both restore the exact prior target120-BPM/4/4 state. Every attribute/child is enumerated, stages cannot accept each other's shape, and source MusicTimes remain empty.

These terminal values are handwritten expectations derived from the pinned native maximum-beat and meter behavior. Actual execution is required; Python synthetic oracle selftests are clearly labelled and are not native evidence.

## Bounds and consumer limits

The input supports at most2048 tempo points and2048 meter points,30000 XML elements, depth64,120000 attributes, and a4-MiB UTF-8 file. Change coordinates are at most quarter1000000; a MIDI delta larger than the28-bit variable-length field blocks output. XML1.0 is required when declared; nonfinite/exponent or oversized numeric forms reject.

Whole-quarter positions are necessary for8.12's importer. Native set_tempo also rounds to meter beats and set_meter uses native bar placement, so the core conservatively rejects off-beat tempo and off-bar meter points. Native note-value and meter fields are signed8-bit values: allowed power-of-two note values stop at64 and numerator stops at127. These are consumer-profile limits, not general SMF limits.

The UI phase was authorized after this independently accepted actual production output was preserved. Actual browser downloads still require the same consumer proof.
