<img src="./assets/HarpLogo.svg" width="200">

# Timestamp Broadcasting

This document proposes a serial communication protocol for broadcasting the current Harp time to non-Harp devices. The signal can be recorded alongside data acquired using a local clock, allowing the recorded data to be aligned with the Harp time base during post-hoc analysis.

> [!NOTE]
>
> This specification is a proposal under discussion in [protocol issue #128](https://github.com/harp-tech/protocol/issues/128).

## Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Motivation

Non-Harp acquisition systems often record data using independent local clocks. Recording a digital signal carrying the Harp time provides a common reference for aligning these recordings with data acquired by Harp devices. Including the whole second in each transmission allows the reference time to be recovered even when recordings start at different times or individual transmissions are lost.

Timestamp broadcasting is intended for post-hoc alignment across acquisition systems. Devices requiring online clock synchronization SHOULD use the [Harp Synchronization Clock](SynchronizationClock.md).

Implementation of timestamp broadcasting is OPTIONAL. Future Harp clock generator devices SHOULD provide a timestamp broadcasting output. Other Harp devices MAY provide this functionality using an available digital output.

## Serial Interface

Timestamp broadcasting uses an asynchronous serial signal on a digital output. The output MUST remain HIGH when idle. Each byte MUST be transmitted using one LOW start bit, eight data bits, no parity bit, and one HIGH stop bit (8N1). Data bits within each byte MUST be transmitted least significant bit first.

### Baud Rate

The baud rate MAY be fixed or configurable. A Device implementing timestamp broadcasting MUST document its baud rate or expose the active baud rate through a readable register that is included in a [register dump](Device.md#r_operation_ctrl-u8--operation-mode-configuration).

Devices with a configurable baud rate MUST document the supported values and the default value. The selected rate MUST allow the complete transmission packet to finish before the next whole second, leaving an idle HIGH interval between packets.

The baud rate SHOULD be selected according to the sampling rate of the recording device. Lower baud rates allow the signal to be recorded by systems with lower sampling rates, but increase the duration of each transmission. The recording device SHOULD acquire multiple samples per bit to allow reliable decoding.

Existing implementations use 1 kbps. A common recommended default remains an [unresolved question](#unresolved-questions).

### Transmission Packet (4 bytes)

Each transmission packet MUST encode the current Harp time in whole seconds as an unsigned 32-bit integer (`U32`), corresponding to [`R_TIMESTAMP_SECOND`](Device.md#r_timestamp_second-u32--system-timestamp-seconds). All timestamp broadcasting packets MUST use Little-Endian byte ordering and follow the structure below:

| Byte | 0 | 1 | 2 | 3 |
| ---- | ---- | ---- | ---- | ---- |
| Current Time (`U32`) | Bits 0–7 | Bits 8–15 | Bits 16–23 | Bits 24–31 |

The four bytes MUST be transmitted consecutively, with the start bit of each subsequent byte immediately following the stop bit of the preceding byte. No header, fractional timestamp, or checksum is transmitted.

At 1 kbps, each bit lasts 1 ms and the complete packet occupies 40 ms, including the start and stop bits of all four bytes. At 1.2 kbps, the packet occupies approximately 33.3 ms.

### Transmission Timing

While timestamp broadcasting is enabled, the Device MUST transmit one packet at the start of each whole second of its Harp clock. The first falling edge, from the idle HIGH level to the LOW start bit of the first byte, MUST mark the start of the whole second encoded in that packet. The Device MUST capture the whole-second value at this boundary and use the captured value for all four bytes.

The timing error between the first falling edge and the whole-second boundary SHOULD be less than 32 μs. Devices MUST document the maximum timing error of their output. Implementations SHOULD validate this error at the physical output, including the effects of interrupt latency and serial peripheral scheduling.

For example, at the start of Harp second `42`, the output transitions LOW to begin the first start bit, and the Device transmits `0x2A`, `0x00`, `0x00`, and `0x00`. The time associated with that first falling edge is `42` seconds, rather than the time at which reception of the packet completes.

## Device Interface

Devices MUST document the output connector, pin assignment, logic levels, and any configuration required to enable timestamp broadcasting. The electrical output MUST be compatible with the recording device's input. Serial framing alone does not imply the use of RS-232 voltage levels or the physical connector defined by the Harp Synchronization Clock.

Configuration SHOULD be provided through device-specific registers following the [Device Interface](Device.md#device-interface). A configurable baud rate SHOULD be exposed as a `U32` register whose value is the number of bits transmitted per second. The register address, supported values, and access permissions MUST be documented in the Device specification.

Changes to the baud rate MUST NOT take effect partway through a packet. Devices SHOULD apply changes between packets and begin transmission at the new rate on the next whole-second boundary. Output enable controls and any sharing of the output with other Device functionality MUST be documented.

Timestamp broadcasting MUST NOT interfere with the timing or operation of the Harp Synchronization Clock when both outputs are enabled. No new core register address is assigned by this proposal.

## Post-hoc Alignment

A non-Harp acquisition system records the timestamp broadcasting signal alongside its other input channels, using its local clock. The recording MUST retain the active baud rate and the local timing information needed to decode the signal and locate each packet's first falling edge.

A decoder SHOULD identify packets from the idle interval preceding the first start bit, verify the start and stop bits of each byte, and reconstruct the Little-Endian `U32` value. Malformed or incomplete packets SHOULD be discarded. Each successfully decoded packet provides a pair consisting of the local acquisition time of its first falling edge and the transmitted whole second of the Harp clock.

Alignment software can use these pairs to estimate the offset and relative clock drift between the two recordings. For example, packets encoding seconds `42` and `43`, recorded at local times `10.000` and `11.001` seconds, provide two reference points for interpolating local timestamps onto the Harp time base.

Software SHOULD detect discontinuities in the decoded Harp time and treat continuous segments separately when estimating the mapping between clocks. A reset or manual change of the Harp clock MUST NOT be interpreted as continuous clock drift. Alignment accuracy depends on the output timing error, the recording sample rate, and the method used to estimate the clock mapping. Successful decoding alone does not guarantee sub-millisecond alignment.

Existing [Harp timestamp alignment routines](https://github.com/harp-tech/harp-python/pull/38) provide a starting point for implementing decoding and post-hoc alignment. Decoder compatibility with the framing and timing specified here requires verification.

## Drawbacks

Providing an additional output requires hardware resources and firmware scheduling. Some serial peripherals cannot begin transmission at an arbitrary whole-second boundary with the proposed timing accuracy, requiring a software or other hardware implementation. The recording system must also allocate an input channel and sample sufficiently quickly for the selected baud rate.

The packet does not include a checksum. Serial framing checks and comparisons between successive timestamps can help detect errors, but cannot identify every corrupted packet.

## Alternatives

A pulse-per-second output provides a timing reference with a simpler implementation, but does not encode the absolute Harp second. An external timestamp interpreter could receive the native Harp Synchronization Clock and produce a timestamp broadcasting signal, allowing existing clock generators to support this feature without modification.

## Unresolved Questions

- Should the common recommended baud rate be 1 kbps for compatibility with existing implementations, or a standard UART rate such as 1.2 kbps?
- Should the baud rate and output enable controls eventually be assigned standardized device-specific or core registers?
- Should an error of less than 32 μs at the first start bit be REQUIRED, or remain RECOMMENDED with a documented implementation limit?

## Relevant Discussions

- [Specification for downsampled clock synchronization protocol](https://github.com/harp-tech/protocol/issues/128).
- [Standards review board discussion #238](https://github.com/orgs/harp-tech/discussions/238), summarized in the [issue meeting notes](https://github.com/harp-tech/protocol/issues/128#issuecomment-6066398774).
- [Behavior timestamp serial output](https://github.com/harp-tech/device.behavior/pull/3).
- [White Rabbit auxiliary UART output](https://github.com/AllenNeuralDynamics/harp.device.white-rabbit#aux-uart-output).
