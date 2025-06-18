<img src="./assets/HarpLogo.svg" width="200">

# Synchronization Clock Protocol (1.0)

## Introduction
The `Harp Synchronization Clock` is a dedicated bus that disseminates the current time to/across Harp devices. It is a serial communication protocol that relays the time information. The last byte in each message can be used as a trigger, and allows a `Device`` to align itself with the current `Harp` time.

## Serial configuration

* The Baud rate used is 100kbps;
* The last byte starts *exactly* 672 us before the elapse of the current second (e.g.:)

    !["SynchClockOscilloscope](./assets/SynchClockOscilloscope.png)

* The packet is composed of 6 bytes (`header[2]` and `timestamp_s[4]`):
  - `header[2] = {0xAA, 0xAF)`
  - `timestamp_s` is of type U32, little-endian, and contains the previous elapsed second.

A sample logic trace is shown below:
    !["SynchClockLogicAnalyzer](./assets/SyncLogicTrace.png)

## Example code

Example of a microcontroller C code dispatching the serialized data:

```C

ISR(TCD0_OVF_vect, ISR_NAKED)
    {
        if ((*timestamp_byte0 == 0xAA) && (*timestamp_byte1 == 0xAF)) reti();
        if ((*timestamp_byte1 == 0xAA) && (*timestamp_byte2 == 0xAF)) reti();
        if ((*timestamp_byte2 == 0xAA) && (*timestamp_byte3 == 0xAF)) reti();

        switch (timestamp_tx_counter)
        {
            case 1:
                USARTD1_DATA = 0xAA;
                break;
            case 2:
                USARTD1_DATA = 0xAF;
                break;
            case 4:
                USARTD1_DATA = *timestamp_byte0;
                break;
            case 6:
                USARTD1_DATA = *timestamp_byte1;
                break;
            case 7:
                USARTD1_DATA = *timestamp_byte2;
                break;
            // The final byte is dispatched much later than the previous 5.
            case 1998:
                USARTD1_DATA = *timestamp_byte3;
                break;
        }
    }
```

Example of a microcontroller C++ code for converting the four received encoded bytes to the timestamp:
````C
    #define HARP_SYNC_OFFSET_US (672)

    // Assume 4 bytes of timestamp data (without header) have been written to this array.
    alignas(uint32_t) volatile uint8_t sync_data_[4];

    // reinterpret 4-byte sequence as a little-endian uint32_t.
    uint32_t encoded_sec = *(reinterpret_cast<uint32_t*>(self->sync_data_));
    // Convert received timestamp to the current time in microseconds.
    // Add 1[s] per protocol spec since 4-byte sequence encodes the **previous** second.
    uint64_t curr_us = ((static_cast<uint64_t>(encoded_sec) + 1) * 1e6) - HARP_SYNC_OFFSET_US;
````

A full example demonstrating a state machine receiving the 6-byte sequence can be found in the [Pico Core](https://github.com/AllenNeuralDynamics/harp.core.rp2040/blob/main/firmware/src/harp_synchronizer.cpp).

---


## Physical connection

The physical connection is made by a simple 3.5mm audio cable.

The connector pinout for a device *receiving* the timestamp is shown below:

!["SynchReceiverSchematic](./assets/HarpClockSyncReceiver.png)

A TVS diode is also suggested for ESD protection.

> [!IMPORTANT]
> The device receiving the timestamp must provide 3.3-5V (~10mA) on the audio jack **R** pin.

The schematic snippet for a device *sending* the timestamp is shown below:

!["SynchSenderSchematic](./assets/HarpClockSyncSender.png)

> [!NOTE]
> The device *sending* the timestamp isolates each clock output port, preventing ground loops from forming when connecting the audio jack between sender and receiver.

A supplementary PDF [example](./assets/PhysicalConnector/PhysicalConnector.pdf) of the sender and the receiver is also available.
The connector used is from `Switchcraft Inc.` with PartNo. `35RASMT2BHNTRX`.

A KiCAD schematic template for creating a Harp device based on the [RP2040](https://www.raspberrypi.com/products/rp2040/) microcontroller with circuitry for receiving the timestamp is provided through the [Pico Template](https://github.com/AllenNeuralDynamics/harp.device.pico-template).

## Release Notes

- v1.0
    * First version.

- v1.1.0
  * Refactor documentation to markdown format.
  * Minor typo corrections.
  * Improve clarity of some sections.
  * Adopt semantic versioning.

- v1.1.1
  * Remove table of contents to avoid redundancy with doc generators.
