# Offline UI acceptance — verified runtime checkpoint

Accepted runtime commit53c52f6549138aa14d57744fdd7214d04bcdacf5 passed browser/native run37610052361, with39 browser cases and the complete eight-case native gate. See RELEASE.md and evidence/provenance.json for exact original artifact identities.

The standalone Japanese/English HTML contains the unchanged accepted converter in a dedicated Blob Web Worker. It reads one explicitly chosen saved session, displays every tempo/meter change with exact positions and rounding review, and requires confirmation before saving a conductor MIDI. A separate JSON receipt records every exact rational value, input/output hash and filename. Source files remain unchanged.

The worker has an eight-second execution bound. New input, clear and cancellation terminate it and invalidate pending results. Delayed file reads carry revision tokens. There is no persistent storage, network processing, directory scan, audio/media access, native-session execution or plugin execution. File contents and labels are rendered as text. The offline-tool copy comes from the initial clean document and must exclude distinct imported filename/content sentinels.

The actual hosted Chrome process must retain its sandbox; the full observed process command is recorded and both no-sandbox flags reject. The browser is offline before opening the file. Main and reopened offline pages record page errors, console errors, network requests and real Blob workers.

Acceptance requires the actual downloaded106-byte MIDI to equal a handwritten literal wire fixture, with all10 receipt entries and the explicit eighth-note/quarter-note conversion. Repeated downloads remain byte-identical. Native-authored quarter15.5, ramp, BBT, malformed XML, native-range and size failures clear old review/export. Tests exercise keyboard chooser/confirmation/export/cancel/clear, same-file reselection, delayed File reads, superseded input, paused worker dispatch, worker timeout and clean offline reopen. A dispatched empty file-change event is labelled as such; it is not a claim about an operating-system file-dialog cancel.

Japanese and English desktop plus390px/320px mobile views are captured. Mobile checks reset horizontal scroll before each left image and require the entire rightmost rounding column/header to be reachable. Both print PDFs are text-checked and rasterized, including the exact rounding fraction; at most two pages are allowed for the fixed fixture.

The native job downloads that browser artifact and checks the tested HTML against the same shipped bytes. Fresh official native Lua authoring must reproduce both browser input files byte-for-byte. The positive MIDI and receipt are copied directly from the actual downloads, with no positive regeneration. Only the three deliberate faults are derived afterward. The accepted independent Python/Mido/native oracle then requires all eight import/fresh-reload cases,120 native readings, literal XML positions/values, six fault rejections, normal exits and unchanged source bytes. Nonfatal GTK/GObject diagnostics and exact output-only terminal-marker normalizations remain disclosed.

The original browser and native artifacts were independently reviewed. Earlier compatibility/production checkpoints and failed diagnostic attempts remain separately identifiable.
