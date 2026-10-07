# BeatCourier — stepped conductor MIDI

BeatCourier is a bounded offline converter from a saved modern Ardour session's stepped tempo and meter map to a metadata-only Standard MIDI File. The source core is present; its full production-output native gate is pending. There is no product interface yet.

The initial compatibility checkpoint passed with official Debian13 Ardour **8.12.0+ds-1**: a literal conductor file went through the unchanged native GUI importer, native save and a fresh-process reload. [Accepted run](https://github.com/Masanori-Spec/beat-courier/actions/runs/37598034673), commit `4dcb13efa45ce161d63454ffcfcbd00d6ce9be8a`. That checkpoint used a handwritten MIDI fixture, so it does not by itself validate the new converter.

## Supported profile

- Saved UTF-8 XML Session version7003, at most4 MiB, with the verified native clock rate
- Every tempo and meter change, starting at quarter0; constant tempos only, with explicit ramp/endpoint/omega checks
- Whole-quarter positions only. Tempo changes must also lie on native meter beats; meter changes must start native bars. Quarter15.5 rejects rather than moving
- Empty MusicTimes. BBT resets and native-resaved import files containing terminal import markers are unsupported inputs
- Power-of-two tempo-note and meter-denominator values1–64; meter numerator1–127, reflecting Ardour's signed-byte representation as well as MIDI limits
- Exact1920-PPQN positions and rational tempo-note conversion. Microseconds per quarter use nearest-integer rounding, with exact value/error in the receipt
- One format0 conductor track containing only FF51 tempo, FF58 meter and end-of-track. No notes, audio, session modification or workspace scan

The inert XML parser rejects DTD/entity declarations, other processing instructions, malformed XML, namespaces, ambiguous structures and bounded-resource violations. It does not load a session into Ardour or execute anything from an input file. The native tests load only original synthetic fixtures in disposable hosted-CI directories.

Ardour already exports MIDI. [ArdourMIDIExport](https://github.com/dbolton/ArdourMIDIExport) also exists and documents an initial-tempo/meter limitation. BeatCourier's modest difference is exporting all supported saved-map changes as a separate conductor. It is not a general MIDI export replacement or a claim of universal DAW compatibility. Ardour9.2 has different fractional-position import code; it is outside the executed8.12 profile.

## Verification

`npm ci --ignore-scripts` and `npm test` run pure converter checks. The hosted workflow adds independent Python/Mido wire checks, native Lua-authored expanded fixtures, actual production MIDI imports, native saves and fresh GUI processes. Three single-fault MIDI controls must show exact wrong tempo, meter or event position. Fractional15.5, ramps and BBT inputs must reject before output. See [the production gate contract](docs/production-gate.md) and [the preserved compatibility contract](docs/native-contract.md).

Native tempo lookups return the preceding segment at an exact boundary; the gate checks both the literal saved point and one tick after it. The native importer creates a narrowly enumerated terminal marker that changes its quarter coordinate on reload. Those output observations do not relax input rejection. Successful compatibility logs include nonfatal GTK/GObject diagnostics around closure; normal exit0 is proven, not error-free logs.

No license grant for original code or fixtures is made. Dependency licensing is recorded in [third-party notices](THIRD_PARTY_NOTICES.md). Public source contains no Ardour binary or package archive.
