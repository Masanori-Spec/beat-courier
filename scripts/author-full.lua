-- Synthetic fixtures authored only by the official packaged native Lua API.
assert(Temporal.ticks_per_beat==1920)
local function author(folder,name,fractional)
 local session=create_session('/tmp/beatcourier-native/'..folder,name,48000)
 assert(session~=nil and Session~=nil)
 local map=Temporal.TempoMap.write_copy()
 map:set_meter(Temporal.Meter(3,4),Temporal.timepos_t.from_ticks(8*1920))
 map:set_meter(Temporal.Meter(7,8),Temporal.timepos_t.from_ticks(14*1920))
 map:set_meter(Temporal.Meter(4,4),Temporal.timepos_t.from_ticks(28*1920))
 map:set_tempo(Temporal.Tempo(120,120,4),Temporal.timepos_t.from_ticks(0))
 map:set_tempo(Temporal.Tempo(100,100,4),Temporal.timepos_t.from_ticks(8*1920))
 map:set_tempo(Temporal.Tempo(150,150,8),Temporal.timepos_t.from_ticks(14*1920))
 map:set_tempo(Temporal.Tempo(120,120,4),Temporal.timepos_t.from_ticks(16*1920))
 map:set_tempo(Temporal.Tempo(123,123,4),Temporal.timepos_t.from_ticks(20*1920))
 map:set_tempo(Temporal.Tempo(150,150,4),Temporal.timepos_t.from_ticks(28*1920))
 if fractional then
  -- Under 7/8 this is a real native meter beat, so the native author does not
  -- round it to a whole quarter. The product must reject this valid input.
  map:set_tempo(Temporal.Tempo(130,130,4),Temporal.timepos_t.from_ticks(15*1920+960))
 end
 Temporal.TempoMap.update(map);map=nil
 assert(Session:save_state('',false,false,false,false,false)==0)
 close_session()
end
author('source','Source',false)
author('fractional','Fractional',true)
local target=create_session('/tmp/beatcourier-native/target','Target',48000)
assert(target~=nil and Session~=nil)
assert(Session:save_state('',false,false,false,false,false)==0)
close_session()
print('BEATCOURIER_FULL_NATIVE_AUTHOR_FINISHED')
