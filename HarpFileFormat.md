<img src="./assets/HarpLogo.svg" width="200">

# Standardized Harp file format

## Introduction

This document defines a standardized file format for logging data from Harp devices. The file format is based on the [Harp Binary Protocol](./BinaryProtocol-8bit.md) and is designed for efficient data logging and parsing.

One of the main advantages of using a standardized binary communication protocol is that logging data from Harp devices can be largely generalized. Conceptually, because all Harp messages share a common standard structure, we can write all the binary data emitted from a device directly into a single binary file. However, this is not always the most convenient way to log data. For instance, if one is interested in ingesting only a subset of messages (e.g. only the messages from a particular sensor connected to the Harp device), this approach would require a post-processing step to filter out the messages of interest. Furthermore, each address, as per Harp protocol spec, has potentially different data formats (e.g. U8 vs U16) or even different lengths if array registers are involved. This can make it more complex to parse and analyze a binary file offline, since we will have to examine the header of each and every message in the file to determine how to extract its contents.

This processing step could be entirely eliminated if we could ensure that all messages in a single binary file had the same format. Fortunately, for any given Harp device, the payload stored in a specific register address is guaranteed to have a fixed format. This can be leveraged in order to save messages from a specific register into different fixed-format files, by employing a de-multiplexing strategy.

## Harp file format

For each device, we define a "container" file format which is essentially a folder that will store data from a single device, and where the payload from messages coming from each register is saved sequentially to a separate binary file:

```plaintext
📦<Device>
 ┣ 📜<DeviceName>_0_<suffix>.bin
 ┣ 📜<DeviceName>_1_<suffix>.bin
 ┣ ...
 ┗📜<DeviceName>_<Reg>_<suffix>.bin
 ```
---

The various components of this convention are detailed below.

- the character `_` is reserved as a separator between fields.
- `<DeviceName>` should match the `device.yml` metadata file that fully defines the device and can be found in the repository of each device ([e.g.](https://raw.githubusercontent.com/harp-tech/device.behavior/main/device.yml)). This file can be seen as the "ground-truth" specification of the device. It is used to automatically generate documentation, interfaces and data ingestion tools. While this is not a strict requirement, it is highly recommended.
- `<Device>` is an arbitrary name that identifies the device being used.
- `<Reg>` is the register number that is logged in the binary file.
- `<suffix>` is an optional suffix that can be co-opted by the user to add any additional information to the file name (e.g. a timestamp, a sequence number, etc). If there is no `<suffix>`, the final `_` should be omitted.
- `.harp` is the extension for the container folder.

### The optional `device.yml` file

Including the `device.yml` file that corresponds to the interface used to log the device's data is recommended. To do this, we place a `device.yml` file at the root of the container folder. The folder structure thus becomes:
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

Most registers in a Harp device will not emit periodic events. As such, it is impossible to know their state unless explicitly queried. For configuration registers we do want to know this state, since it will define the behavior of the device at runtime. We also want to include metadata registers such as the device name and versions. Fortunately, the [Device specification](./Device.md) defines a feature for dumping the values of all registers during acquisition. By sending a single message to the `R_OPERATION_CTRL` register with `Bit3` set to 1, we can make the device send a rapid sequence of `READ` type messages with the contents of all registers.

> [!IMPORTANT]
> In your experiments, always validate that your logging routine has fully initialized before requesting a read dump from the device. Failure to do so may result in missing data.


## Release notes

- v0.1
    * First draft.
