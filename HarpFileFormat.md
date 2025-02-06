<img src="./assets/HarpLogo.svg" width="200">

# Standardized Harp file format

## Introduction

This document defines a standardized file format for logging data from Harp devices. The file format is based on the [Harp Binary Protocol](./BinaryProtocol-8bit.md) and is designed for efficient data logging and parsing.

One of the main advantages of using a standardized binary communication protocol is that logging data from Harp devices can be largely generalized. In theory, we could simply dump the binary data from the device straight into a single binary file and be done with it. However this is not always the most convenient way to log data. For instance, if one is interested in ingesting only a subset of messages (e.g. only the messages from a particular sensor connected to the Harp device), the previous approach would require a post-processing step to filter out the messages of interest. Furthermore, each address, as per Harp protocol spec, has potentially different data formats (e.g. U8 vs U16) or even different lengths if array registers are involved. This can make it very tedious to parse and analyze a binary file offline, since we will have to examine the header of each and every message in the file to determine how to extract its contents.

This processing step could be entirely eliminated if we could ensure that all messages in a single binary file had the same format. Fortunately, for a any given Harp device, the payload stored in a specific register will have a fixed type and length. This can be leveraged by simply saving messages from a specific register into a different files (also known as a de-multiplexing strategy).

## Harp file format

For each device, we will define a "container" file format that will contain data from a single device, where each register will be saved in a separate binary file:

```plaintext
📦<Device>.harp
 ┣ 📜<DeviceName>_0_<suffix>.bin
 ┣ 📜<DeviceName>_1_<suffix>.bin
 ┣ ...
 ┗📜<DeviceName>_<Reg>_<suffix>.bin
 ```
---

where:

- the character "_" is reserved as a separator between fields.
- `<DeviceName>` should match the `device.yml` metadata file that fully defines the device and can be found in the repository of each device ([e.g.](https://raw.githubusercontent.com/harp-tech/device.behavior/main/device.yml)). This file can be seen as the "ground-truth" specification of the device. It is used to automatically generate documentation, interfaces and data ingestion tools. While this is not a strict requirement, it is highly recommended.
- `<Device>` is an arbitrary name that identifies the device being used.
- `<Reg>` is the register number that is logged in the binary file.
- `<suffix>` is an optional suffix that can be co-opted by the user to add any additional information to the file name (e.g. a timestamp, a sequence number, etc).
- `.harp` is the file extension for the container file.

### The optional `device.yml` file

Including the `device.yml` file that corresponds to the device interface used to log the device's data is recommended. This shall be achieved by simply appending a `device.yml` file to the `harp` file. The container thus becomes:
```plaintext
📦<Device>.harp
 ┣ 📜<DeviceName>_0_<suffix>.bin
 ┣ 📜<DeviceName>_1_<suffix>.bin
 ┣ ...
 ┣ 📜<DeviceName>_<Reg>_<suffix>.bin
 ┗ 📜device.yml (Optional) ```
---
```

## Best practices and application notes

### Logging the device's initial configuration

Most of the registers in a given Harp device are not emitting period events. As such, it is impossible to know their state unless explicitly queried. This is particularly important for the configuration registers, which define the behavior of the device, as well as metadata registers (e.g. versions). Fortunately, the [Device specification](./Device.md) defines a feature for dumping the values of all registers during acquisition. This can achieved by sending a single message to the `R_OPERATION_CTRL` register with a Bit3 set to 1. This will trigger the device to send a volley of `READ` type messages with the contents of all registers.

> [!IMPORTANT]
> In your experiments, always validate that your logging routine has fully initialized before requesting a reading dump from the device. Failure to do so may result in missing data.


## Release notes

- v0.1
    * First draft.
