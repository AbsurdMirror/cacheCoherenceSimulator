from sim_enum import *
from sim_drivers import *
from event import *
from node import *
from bus import *
import traceback
import random  

core0 = CoreNode(0)
core1 = CoreNode(1)
core2 = CoreNode(2)
cache0 = NARAT_Cache(0)
cache1 = NARAT_Cache(1)
cache2 = NARAT_Cache(2)
llc = NARAT_LLC(3)
arat_bus = NARAT_Bus()

core0.connect_cache(cache0)
core1.connect_cache(cache1)
core2.connect_cache(cache2)

arat_bus.connect([cache0, cache1, cache2, llc])

llc.bind_caches([cache0, cache1, cache2])

data_driver = DataDriver()
tick_driver = TickDriver()
print_driver = PrintDriver()
excel_driver = ExcelDriver(
    "./trace.xlsx",
    [v for v in NARAT_MSI_CacheState],
    [v for v in NARAT_MSI_CacheEventCmd],
    [v for v in NARAT_MSI_LLCState],
    [v for v in NARAT_MSI_LLCEventCmd]
)

data_driver.connect([core0, core1, core2])
tick_driver.add_objects([arat_bus, core0, core1, core2, cache0, cache1, cache2, llc, data_driver])
print_driver.add_tick_driver(tick_driver)
print_driver.connect([
    core0, core1, core2,
    cache0, cache1, cache2,
    arat_bus, arat_bus.response_bus, arat_bus.request_bus, arat_bus.data_bus,
    llc,
    data_driver])
print_driver.add_flags(["Verify", "Core", "Bus"])
excel_driver.bind_tick_driver(tick_driver)
excel_driver.bind_nodes([tick_driver, core0, core1, core2, cache0, cache1, cache2, llc, arat_bus.request_bus, arat_bus.data_bus])

data_driver.data_init(0)
llc.data_init(0)

tick_driver.max_tick = 4096
tick_driver.run()

print("core0", core0.verity_load_times, core0.verity_store_times, core0.verity_load_times + core0.verity_store_times)
print("core1", core1.verity_load_times, core1.verity_store_times, core1.verity_load_times + core1.verity_store_times)
print("core2", core2.verity_load_times, core2.verity_store_times, core2.verity_load_times + core2.verity_store_times)
print("data_driver", data_driver.verify_times)

excel_driver.save_workbook()