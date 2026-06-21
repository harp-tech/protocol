# Device Interface Specification

This document defines the YAML format used to describe the interface of a Harp device. A device interface file is the machine-readable contract for a specific Harp device: it declares every application register, its payload layout, and the set of masks used to interpret register values. Tooling such as code generators, documentation builders, and validation libraries SHOULD consume this file as the single source of truth for a device's register map and functionality.

## Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Relationship to Other Specifications

- [**Binary Protocol**](Protocol.md) — defines the wire format for all Harp messages (message type, payload type encoding, checksum, etc.).
- [**Device Registers and Operation**](Device.md) — defines the behavioral contract every Harp device must follow (operation modes, request-reply patterns, core registers). The device interface file describes *which* registers a specific device exposes, not *how* the protocol operates. Additionally, the device interface further specifies application registers and their payloads, which are outside the scope of the core device specification.

## Document Structure Overview

A device interface file is a YAML document whose schema is defined by `./schema/device.json`. The root level of the document contains metadata fields describing the device and a `registers` map that declares all application registers. Optional `bitMasks` and `groupMasks` sections define named masks that can be referenced by registers.

The file MUST declare all four metadata fields (`device`, `whoAmI`, `firmwareVersion`, `hardwareTargets`) and the `registers` map. The `bitMasks` and `groupMasks` sections are OPTIONAL and SHOULD be included when registers reference named masks.

A YAML language-server schema directive SHOULD be placed at the top of the file to enable editor validation and autocompletion:

```yaml
# yaml-language-server: $schema=https://harp-tech.org/draft-02/schema/device.json
```

## Device Metadata

| Field             |  Type   | Required | Description                                                                                                                                                                              |
| :---------------- | :-----: | :------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `device`          | string  |   Yes    | The human-readable name of the device (e.g. `Behavior`).                                                                                                                                 |
| `whoAmI`          | integer |   Yes    | The unique identity class of the device, as registered in the [harp-tech/whoami](https://github.com/harp-tech/whoami) repository. Corresponds to core register `R_WHO_AM_I` (address 0). |
| `firmwareVersion` | string  |   Yes    | The firmware version in `"<major>.<minor>"` format (e.g. `"3.4"`).                                                                                                                       |
| `hardwareTargets` | string  |   Yes    | The hardware version targeted by this firmware, in `"<major>.<minor>"` format (e.g. `"2.0"`).                                                                                            |

**Example:**

```yaml
device: Behavior
whoAmI: 1216
firmwareVersion: "3.4"
hardwareTargets: "2.0"
```

## Core Registers

Every Harp device also exposes a set of core registers (addresses 0–31) that are common to all devices. These registers are defined in a separate file (`core.yml`) and follow the same YAML schema described in this document. Core registers handle device identification, timestamping, operation mode control, and other shared functionality. See [Device Registers and Operation](Device.md#core-registers) for the full specification of core register behavior.

The device interface file MUST NOT define registers with addresses below 32. Application registers start at address 32.

Should downstream tooling require the `core.yml` specification, they should simply merge it with the device interface file, since both files share the same schema. For example, a code generator can read both `core.yml` and a device's interface file, validate them separately, and then combine their `registers` sections to produce a unified register map for that device.

## Registers

The `registers` section is a map where each key is the register name (PascalCase by convention) and the value is a register definition object.

### Register Properties

| Property        | Type               | Required | Default  | Description                                                                                                                     |
| :-------------- | :----------------- | :------: | :------: | :------------------------------------------------------------------------------------------------------------------------------ |
| `address`       | integer (0–255)    |   Yes    |    —     | The unique 8-bit address of the register. Application registers MUST use addresses ≥ 32.                                        |
| `type`          | string             |   Yes    |    —     | The payload type. One of: `U8`, `S8`, `U16`, `S16`, `U32`, `S32`, `U64`, `S64`, `Float`.                                        |
| `length`        | integer (≥ 1)      |    No    |    1     | The number of elements in the register payload. Values greater than 1 indicate an array payload.                                |
| `access`        | string or string[] |   Yes    |    —     | The access mode(s) of the register. A single value or an array of 1–3 unique values from: `Read`, `Write`, `Event`.            |
| `description`   | string             |    No    |    —     | A summary description of the register function.                                                                                 |
| `minValue`      | number             |    No    |    —     | The minimum allowable value for the register payload.                                                                           |
| `maxValue`      | number             |    No    |    —     | The maximum allowable value for the register payload.                                                                           |
| `defaultValue`  | number             |    No    |    —     | The default value for the register payload.                                                                                     |
| `maskType`      | string             |    No    |    —     | The name of a `bitMask` or `groupMask` used to interpret the payload value.                                                     |
| `interfaceType` | string             |    No    |    —     | The name of the type used to represent the payload value in high-level interfaces (e.g. code-generated classes).                |
| `visibility`    | string             |    No    | `public` | Whether the register is exposed in the high-level interface. One of: `public`, `private`.                                       |
| `deprecated`    | boolean            |    No    | `false`  | Whether the register is deprecated.                                                                                             |
| `volatile`      | boolean            |    No    | `false`  | Whether the register value can be saved to non-volatile memory. Volatile registers are not persisted.                           |
| `payloadSpec`   | object             |    No    |    —     | Defines named members within a structured payload. See [Payload Specification](#payload-specification).                         |

### Access Modes

Every register MUST declare an `access` field, which determines which Harp message types are valid for it:

| Access  | Behavior                                                                                                                          |
| :------ | :-------------------------------------------------------------------------------------------------------------------------------- |
| `Read`  | The register supports `Read` requests from the Controller. The device replies with the current register value.                    |
| `Write` | The register supports `Write` requests from the Controller. The device updates the register and replies with the resulting value. |
| `Event` | The device MAY send unsolicited `Event` messages from this register when a relevant trigger occurs.                               |

A register that specifies only `Event` as its access mode is implicitly read-only from the Controller's perspective — the Controller cannot write to it, and the device pushes data when events occur.

When multiple access modes are needed, they SHOULD be expressed as a YAML sequence (1–3 unique values):

```yaml
access: [Write, Event]
```

### Value Constraints

The `minValue` and `maxValue` fields specify the allowable range for the register payload. The device MAY reject writes outside this range (see [Device.md — Error Handling](Device.md#error-handling)).

**Example:**

```yaml
PwmDutyCycleDO0:
  address: 64
  type: U8
  access: Write
  minValue: 1
  maxValue: 99
  description: Specifies the duty cycle of the PWM at DO0.
```

### Mask Type Reference

When a register's payload represents a set of flags or an enumerated value, the `maskType` field SHOULD reference a named mask defined in the [`bitMasks`](#bit-masks) or [`groupMasks`](#group-masks) section. This enables code generators to produce strongly-typed enumerations.

**Example:**

```yaml
DigitalInputState:
  address: 32
  access: Event
  type: U8
  maskType: DigitalInputs
  description: Reflects the state of DI digital lines of each Port
```

### Simple Register Examples

A minimal read-only register:

```yaml
InfoRegister:
  address: 33
  type: U8
  access: Read
  description: A simple read-only register that returns a status code.
```

A write-only register with value constraints:

```yaml
PulseDurationDOPort0:
  address: 46
  type: U16
  access: Write
  minValue: 1
  description: Specifies the duration of the output pulse in milliseconds.
```

## Payload Specification

When a register has `length` greater than 1 (i.e. an array payload), the `payloadSpec` field MAY be used to assign names, descriptions, and constraints to individual elements within the payload. This is useful for registers that pack multiple logical values into a single array.

Similarly, when a single-element register packs multiple logical fields into one word using bit masks, `payloadSpec` MAY be used to document each bitfield.

### Payload Member Properties

Each key in `payloadSpec` is a member name, and the value is an object with the following properties:

| Property        |  Type   | Required | Description                                                                  |
| :-------------- | :-----: | :------: | :--------------------------------------------------------------------------- |
| `offset`        | integer |    No    | The zero-based index at which this member starts within the payload array.   |
| `length`        | integer |    No    | The number of elements this member occupies (default: 1).                    |
| `mask`          | integer |    No    | The bitmask used to read and write this member within a single payload word. |
| `description`   | string  |    No    | A summary description of the payload member.                                 |
| `minValue`      | number  |    No    | The minimum allowable value for this member.                                 |
| `maxValue`      | number  |    No    | The maximum allowable value for this member.                                 |
| `defaultValue`  | number  |    No    | The default value for this member.                                           |
| `maskType`      | string  |    No    | The name of a mask used to interpret this member's value.                    |
| `interfaceType` | string  |    No    | The type name used for this member in high-level interfaces.                 |

A member is located within the payload using two **independent** coordinates, either or both of which MAY be present:

- `offset` (with optional `length`) selects *which element(s)* of the payload array the member occupies.
- `mask` selects *which bits* within a payload word the member occupies.

These coordinates are orthogonal and MAY be combined: a member can specify both an `offset` (to pick an element of an array) **and** a `mask` (to pick a bitfield within that element). See [Combining Offset and Mask](#combining-offset-and-mask).

Members also need not cover the payload exhaustively. A `payloadSpec` is a *sparse annotation*: elements or bits that no member describes are simply left undocumented, and gaps between members are permitted.

The sections below describe each strategy in isolation and then in combination:

### Offset-Based Members (Array Payloads)

For array payloads, each member specifies an `offset` indicating its position in the array. This is the typical approach for registers where `length > 1`.

**Example — Analog data with three channels:**

```yaml
AnalogData:
  address: 44
  type: S16
  length: 3
  access: Event
  description: Voltage at the ADC input and encoder value on Port 2
  payloadSpec:
    AnalogInput0:
      offset: 0
      description: The voltage at the output of the ADC channel 0.
    Encoder:
      offset: 1
      description: The quadrature counter value on Port 2
    AnalogInput1:
      offset: 2
      description: The voltage at the output of the ADC channel 1.
```

This tells consumers that the 3-element `S16` array should be interpreted as `[AnalogInput0, Encoder, AnalogInput1]`.

### Mask-Based Members (Bitfield Payloads)

For single-word registers that pack multiple logical fields into one value using bit masks, each member specifies a `mask` indicating which bits encode that field. This pattern is currently implemented in the `OperationControl` core register:

**Example — Operation control bitfield (from `core.yml`):**

```yaml
OperationControl:
  address: 10
  type: U8
  access: Write
  description: Stores the configuration mode of the device.
  payloadSpec:
    OperationMode:
      description: Specifies the operation mode of the device.
      maskType: OperationMode
      mask: 0x3
    DumpRegisters:
      description: Specifies whether the device should report the content of all registers on initialization.
      interfaceType: bool
      mask: 0x8
    MuteReplies:
      description: Specifies whether the replies to all commands will be muted.
      interfaceType: bool
      mask: 0x10
    Heartbeat:
      description: Specifies whether the device should report the seconds register each second.
      maskType: EnableFlag
      mask: 0x80
```

### Combining Offset and Mask

When an array payload packs multiple bitfields into *individual elements*, members combine both coordinates: `offset` selects the array element and `mask` selects the bits within it. Several members MAY share the same `offset` while occupying different bit ranges via distinct `mask` values.

**Example — a 2-element `U16` payload with bitfields in each word:**

```yaml
StartPulseTrain:
  address: 101
  type: U16
  length: 2
  access: Write
  description: Starts a PWM pulse train.
  payloadSpec:
    DigitalOutput:
      offset: 0
      mask: 0xC00
      maskType: PwmPort
    PulseWidth:
      offset: 0
      mask: 0x3FF
      interfaceType: ushort
    Frequency:
      offset: 1
      mask: 0xFF00
      minValue: 1
      maxValue: 255
      defaultValue: 1
      interfaceType: byte
    PulseCount:
      offset: 1
      mask: 0xFF
      interfaceType: byte
```

Here `DigitalOutput` and `PulseWidth` both read from element `0` (different bit ranges of the same word), and `Frequency` and `PulseCount` both read from element `1`. This example also shows that a masked member MAY carry a `maskType` (here `DigitalOutput` is interpreted through the `PwmPort` group mask) and MAY constrain its value with `minValue`/`maxValue`/`defaultValue`.

### Interface Type and Reinterpretation

The `interfaceType` field names the type used to represent a value in high-level interfaces (e.g. code-generated classes). It does not change the wire `type`; it tells consumers how to *reinterpret* the raw payload elements.

When `interfaceType` is applied to a member that spans multiple elements (`length` > 1), the indicated elements are combined into a single value of that type:

```yaml
Version:
  address: 35
  type: U8
  length: 32
  access: Event
  payloadSpec:
    ProtocolVersion:                 # 3 × U8 reinterpreted as one HarpVersion
      offset: 0
      length: 3
      interfaceType: HarpVersion
    CoreId:                          # 3 × U8 reinterpreted as a string
      offset: 9
      length: 3
      interfaceType: string
    InterfaceHash:                   # 20 × U8 left as a raw array (no interfaceType)
      offset: 12
      length: 20
```

`interfaceType` MAY also be applied at the **register level** (with no `payloadSpec`), in which case the whole payload is reinterpreted:

```yaml
CustomPayload:
  address: 36
  type: U32
  length: 3
  access: Read
  interfaceType: HarpVersion
```

> [!NOTE]
> The set of valid `interfaceType` names is intentionally open-ended (the schema treats it as a free string). Values seen in practice include primitive type names such as `bool`, `byte`, `int`, `uint`, `ushort`, `float`, and `string`, as well as custom type names such as `HarpVersion`. The meaning of each name is defined by the consuming tooling, not by this schema.

### Interface Types

> [!WARNING]
> **TODO.** The canonical list of supported `interfaceType` values is not yet finalized. The entries below are observed in existing device files and are provided as a non-exhaustive working list pending standardization.

| Interface Type | Notes                                              |
| :------------- | :------------------------------------------------- |
| `bool`         | Boolean flag, typically over a single masked bit.  |
| `byte`         | 8-bit unsigned integer.                            |
| `int`          | Signed integer.                                    |
| `uint`         | Unsigned integer.                                  |
| `ushort`       | 16-bit unsigned integer.                           |
| `float`        | Floating-point value.                              |
| `string`       | Text, typically over a span of byte elements.      |
| `HarpVersion`  | Custom type composed from multiple elements.       |

## Bit Masks

The `bitMasks` section defines flag-style enumerations where **multiple bits MAY be set simultaneously**. Each entry is a named mask containing a `bits` map (REQUIRED) and an OPTIONAL `description`.

### Bit Mask Structure

```yaml
bitMasks:
  <MaskName>:
    description: <string>
    bits:
      <BitName>: <value>
      <BitName>:
        value: <integer>
        description: <string>
```

Each bit entry can be either:
- A bare integer value (shorthand), or
- An object with `value` (required) and `description` (optional).

### Example

```yaml
bitMasks:
  DigitalInputs:
    description: Specifies the state of port digital input lines.
    bits:
      DIPort0:
        value: 0x1
        description: Port 0 digital input
      DIPort1:
        value: 0x2
        description: Port 1 digital input
      DIPort2:
        value: 0x4
        description: Port 2 digital input
      DI3:
        value: 0x8
        description: Digital input DI3

  DigitalOutputs:
    description: Specifies the state of port digital output lines.
    bits:
      DOPort0: 0x1
      DOPort1: 0x2
      DOPort2: 0x4
      SupplyPort0: 0x8
      SupplyPort1: 0x10
      SupplyPort2: 0x20
      Led0: 0x40
      Led1: 0x80
      Rgb0: 0x100
      Rgb1: 0x200
      DO0: 0x400
      DO1: 0x800
      DO2: 0x1000
      DO3: 0x2000
```

Bit mask values SHOULD be powers of two (or combinations thereof), since they represent individual flags that can be OR-ed together.

> [!Note] Following the naming convention for Enums proposed by [Microsoft](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/enum), `BitMask` names SHOULD be plural (e.g. `DigitalOutputs`) since multiple values can be combined, and bit names SHOULD be singular (e.g. `DOPort0`) since they represent individual flags.

## Group Masks

The `groupMasks` section defines enumerations where **exactly one value is selected at a time** (mutually exclusive). Each entry is a named mask containing a `values` map (REQUIRED) and an OPTIONAL `description`.

### Group Mask Structure

```yaml
groupMasks:
  <MaskName>:
    description: <string>
    values:
      <ValueName>: <value>
      <ValueName>:
        value: <integer>
        description: <string>
```

The value format is identical to bit masks — either a bare integer or an object with `value` and `description`.

### Example

```yaml
groupMasks:
  MimicOutput:
    description: Specifies the target IO on which to mimic the specified register.
    values:
      None: 0
      DIO0:
        value: 1
        description: Is reflected on DIO0
      DIO1:
        value: 2
        description: Is reflected on DIO1
      DIO2:
        value: 3
        description: Is reflected on DIO2
      DO0:
        value: 4
        description: Is reflected on DO0
      DO1:
        value: 5
        description: Is reflected on DO1
      DO2:
        value: 6
        description: Is reflected on DO2
      DO3:
        value: 7
        description: Is reflected on DO3

  EncoderModeMask:
    description: Specifies the type of reading made from the quadrature encoder.
    values:
      Position: 0
      Displacement: 1
```

Group mask values are *typically* sequential integers starting from zero, since they represent mutually exclusive modes or states. This is a convention, not a requirement: the schema accepts any integer values, and non-sequential values (e.g. `0x1`, `0x2`, `0x4`, `0xA`) are permitted.

> [!Note] Following the naming convention for Enums proposed by [Microsoft](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/enum), `GroupMask` names SHOULD be singular (e.g. `MimicOutput`) since they represent a single choice among options, and value names SHOULD also be singular (e.g. `DIO0`) since they represent individual states.

## YAML Authoring Conventions

We target YAML 1.1 for device interface files, which allows us to leverage features like anchors and aliases to reduce duplication and improve maintainability. The following conventions are allowed when authoring device interface YAML files.

### YAML Anchors and Aliases

Device interface files frequently contain groups of registers that share the same type, access mode, and other properties. YAML anchors (`&name`) and aliases (`*name`) MAY be used to reduce duplication. The merge key (`<<:`) allows overriding specific fields while inheriting the rest.

**Example — Defining a family of pulse duration registers:**

```yaml
registers:
  PulseDOPort0: &pulseDO
    address: 46
    type: U16
    access: Write
    minValue: 1
    description: Specifies the duration of the output pulse in milliseconds.
  PulseDOPort1:
    <<: *pulseDO
    address: 47
  PulseDOPort2:
    <<: *pulseDO
    address: 48
```

Here, `PulseDOPort1` and `PulseDOPort2` inherit all properties from the anchor `&pulseDO` but override the `address` field. Additional fields such as `description` MAY also be overridden as needed.

A `payloadSpec` map MAY itself be anchored and merged into another register, allowing a common set of payload members to be reused and extended:

```yaml
StartPulse:
  address: 100
  type: U16
  access: Write
  payloadSpec: &startPulse
    DigitalOutput:
      offset: 0
      mask: 0xC00
      maskType: PwmPort
    PulseWidth:
      offset: 0
      mask: 0x3FF
      interfaceType: ushort
StartPulseTrain:
  address: 101
  type: U16
  length: 2
  access: Write
  payloadSpec:
    <<: *startPulse        # inherits DigitalOutput and PulseWidth
    Frequency:             # and adds further members
      offset: 1
      mask: 0xFF00
      interfaceType: byte
```

### Anchor Scoping

Anchors MAY reference values as well as objects. For example, a common payload type can be shared across registers using a value anchor:

```yaml
Rgb0:
  address: 71
  type: &rgbType U8
  length: 3
  access: &rgbAccess Write
  description: Specifies the state of the RGB0 LED channels.
Rgb1:
  address: 72
  type: *rgbType
  length: 3
  access: *rgbAccess
  description: Specifies the state of the RGB1 LED channels.
```

### Private registers

Registers that are not meant to be exposed in high-level interfaces (e.g. code-generated classes) can be marked with `visibility: private`. This is commonly used for reserved registers that fill gaps in the address space to maintain contiguity.

```yaml
Reserved0: &reserved
  address: 33
  type: U8
  access: Read
  description: Reserved for future use
  visibility: private
Reserved1:
  <<: *reserved
  address: 84
```

## Schema Reference

The device interface YAML format is formally defined by a set of JSON Schema files:

| Schema           | Description                                                                                                 |
| :--------------- | :---------------------------------------------------------------------------------------------------------- |
| `device.json`    | Top-level schema for device interface files. Requires device metadata and references `core.json`.           |
| `core.json`      | Schema for core device properties. Requires `protocolVersion` and references `registers.json`.              |
| `registers.json` | Defines the structure of registers, bit masks, group masks, payload members, and all associated properties. |

Editors supporting the [YAML Language Server](https://github.com/redhat-developer/yaml-language-server) can validate device interface files by adding the schema directive shown in the [Document Structure Overview](#document-structure-overview).
