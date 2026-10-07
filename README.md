# BeatCourier — native compatibility probe

BeatCourier is a proposed offline exporter for the stepped tempo and meter changes in a saved Ardour session. This repository currently contains a synthetic native compatibility probe, not a finished converter or product interface.

The first question is whether a metadata-only Standard MIDI File can actually pass through Ardour's production importer and survive a native save and fresh-process reload. The hosted probe uses Debian 13's authenticated Ardour **8.12.0+ds-1** package, its real Lua session-authoring API, and its unchanged GUI `PublicEditor::do_import` binding. It does not replace the importer or manufacture the resulting session XML.

## Bounded intended scope

- Explicitly opened, saved session XML; stepped constant tempos and meters; a conductor MIDI with no notes or audio
- For the first Ardour 8.12 compatibility profile, every change must fall on a whole quarter note. A change at quarter 15.5 must be rejected instead of silently moved
- Ramps, nonempty MusicTimes/BBT resets, values MIDI cannot represent, and unsupported XML forms will block export
- Exact rational position/tick accounting and explicit tempo-microsecond rounding review are required before a future product release

Ardour already exports MIDI. The proposed difference is collecting all supported session-map changes into a separate conductor file. It is not a general replacement for native MIDI export. Ardour 9.2 has a different importer that preserves fractional positions at native beat-tick resolution; this probe does not establish 9.2 compatibility.

## What the probe does

It authors two empty synthetic sessions through the packaged native Lua interpreter and creates one original literal conductor MIDI. In the real GUI, it selects the Dummy backend, pastes a fixed test script into the native Scripting console, calls the production file-import API, queries the loaded map, and saves. A fresh GUI process reloads and saves the result again. Independent Python checks require all three tempo points and both meter points at their handwritten quarter positions. An independent Mido parse verifies every input MIDI event and the absence of note/channel events.

The probe never opens a user's session, instantiates an external plugin, accesses audio hardware, or edits a source session. It runs only in hosted CI with disposable XDG/session directories. Source publication excludes native binaries, package archives and profiles.

Run status is pending until actual hosted evidence is reviewed. Startup observation or an exit status alone is not native import acceptance. The converter, rejection controls and browser-output gate remain future work, even if this compatibility probe succeeds.

See [the acceptance contract](docs/native-contract.md). No license grant for original code or fixtures is made by this repository.
