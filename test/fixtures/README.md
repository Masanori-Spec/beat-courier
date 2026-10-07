# Retained native input fixture

`native-authored.ardour` is the actual synthetic Source saved by the official Debian Ardour 8.12 Lua API during the first compatibility probe. SHA-256: `b4f4c9f34a82751973be1ca7bdb8c9be498fb9d6527407d33dd9d2b3966df410`.

It is byte-identical to the source in accepted [R9 run 37598034673](https://github.com/Masanori-Spec/beat-courier/actions/runs/37598034673), artifact 11471272861. It contains the initial three-tempo/two-meter fixture and no musical media. The expanded fixture is authored afresh in the hosted production gate; synthetic oracle selftests are not presented as native fixture evidence.

No license grant for this original fixture is made.

The UI sample and input tests use the actual expanded native source from accepted production run37601909063, artifact11473008636:

- `expanded-native.ardour`: SHA-256 `f84c16e8f167fc5f351ee584e2dbd92f9459dff25874a71d7036c926b1509829`
- `fractional-native.ardour`: SHA-256 `2844ac587dcfbd2c94aa572a32863c2f53bffca32c9d97872acacb6b2d8aadb8`

Both are retained native-API saves. The second contains a genuine quarter15.5 tempo under7/8 and must be rejected. The hosted browser-native job re-authors both and requires byte identity to the actual browser inputs before importing its downloaded MIDI.
