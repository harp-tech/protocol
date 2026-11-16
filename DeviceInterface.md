# Device Interface Specification

This document defines the YAML format used to describe the interface of a Harp device. A device interface file is the machine-readable contract for a specific Harp device: it declares every application register, its payload layout, and the set of masks used to interpret register values. Tooling such as code generators, documentation builders, and validation libraries SHOULD consume this file as the single source of truth for a device's register map and functionality.

## Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Relationship to Other Specifications

- [**Binary Protocol**](BinaryProtocol-8bit.md) — defines the wire format for all Harp messages (message type, payload type encoding, byte order, checksum, etc.).
- [**Device Registers and Operation**](Device.md) — defines the behavioral contract every Harp device must follow (operation modes, request-reply patterns, core registers). The device interface file describes _which_ registers a specific device exposes, not _how_ the protocol operates. Additionally, the device interface further specifies application registers and their payloads, which are outside the scope of the core device specification.

## Document Structure Overview

The root level of the device interface file (`device.yml`) contains metadata fields describing the device and a `registers` map that declares all application registers. Optional `bitMasks` and `groupMasks` sections define named masks that can be referenced by registers.

The file MUST declare the four required metadata fields (`name`, `whoAmI`, `version`, `protocolVersion`) and the `registers` map. The `bitMasks` and `groupMasks` sections are OPTIONAL and SHOULD be included when registers reference named masks.

The device interface format is formally defined by a set of JSON Schema files:

| Schema           | Description                                                                                                 |
| :--------------- | :---------------------------------------------------------------------------------------------------------- |
| `device.json`    | Top-level schema for device interface files. Requires device metadata and references `core.json`.           |
| `core.json`      | Schema for core device properties. Requires `protocolVersion` and references `registers.json`.              |
| `registers.json` | Defines the structure of registers, bit masks, group masks, payload members, and all associated properties. |

A YAML version and language-server schema directive SHOULD be placed at the top of the file to enable editor validation and autocompletion. Editors supporting the [YAML Language Server](https://github.com/redhat-developer/yaml-language-server) use the directive to validate the file against `device.json`:

```yaml
%YAML 1.1
---
# yaml-language-server: $schema=https://harp-tech.org/draft-03/schema/device.json
```

> [!NOTE]
> The JSON schema validates the _structure_ of the file. Some rules in this document cannot be expressed in JSON Schema (for example, that a `maskType` refers to a declared mask, or that an `interfaceType` matches the size of the payload it reinterprets). These are marked with RFC 2119 keywords in the relevant sections and summarized in [Constraints Beyond the Schema](#constraints-beyond-the-schema). Tooling such as [`Harp.Generators`](https://github.com/harp-tech/generators) checks them when loading the file and SHOULD reject a file that violates them.

## Device Metadata

| Field             |   Type  | Required | Description                                                                                                                                                                                                                                             |
| :---------------- | :-----: | :------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `name`            |  string |   Yes    | The name of the device, matching its entry in the [harp-tech/whoami](https://github.com/harp-tech/whoami) registry (e.g. `Behavior`). MUST be PascalCase.                                                                                               |
| `whoAmI`          | integer |   Yes    | The unique identity class of the device, as registered in the [harp-tech/whoami](https://github.com/harp-tech/whoami) repository. Corresponds to core register `R_WHO_AM_I` (address 0).                                                                |
| `version`         |  string |   Yes    | The version of the device interface, in `"<major>.<minor>"` format (e.g. `"3.4"`). The major and minor components of `FIRMWARE` in [`R_VERSION`](Device.md#r_version-u8-array--device-version-information) MUST be equal to it.                         |
| `protocolVersion` |  string |   Yes    | The version of the core interface implemented by the device, in `"<major>.<minor>"` format (e.g. `"2.0"`). The major and minor components of `PROTOCOL` in [`R_VERSION`](Device.md#r_version-u8-array--device-version-information) MUST be equal to it. |
| `description`     |  string |    No    | A summary description of the device interface, used in generated documentation. MUST be a single line.                                                                                                                                                  |

**Example:**

```yaml
description: Controls the digital and analog lines of a behavior rig.
name: Behavior
whoAmI: 1216
version: "3.4"
protocolVersion: "2.0"
```

## Core Registers

Every Harp device also exposes a set of core registers (addresses 0–31) defined in a separate [`core.yml`](./schema/core.yml) file that follows the same YAML schema described in this document. Core registers handle device identification, timestamping, operation mode control, and other shared functionality. As these registers are common to all devices, `core.yml` does not need to be included alongside `device.yml`. See [Device Registers and Operation](Device.md#core-registers) for the full specification of core register behavior.

The device interface file MUST NOT define registers with addresses below 32. Application registers start at address 32.

Should downstream tooling require the `core.yml` specification, they should simply merge it with the device interface file, since both files share the same schema. For example, a code generator can read both `core.yml` and a device's interface file, validate them separately, and then combine their `registers` sections to produce a unified register map for that device.

The masks declared in `core.yml` (e.g. `EnableFlag`, `OperationMode`) are in scope for the device interface file: a `maskType` MAY reference them without redeclaring them. A mask declared in the device interface file with the same name as a core mask takes precedence over it.

## Registers

The `registers` section is a map where each key is the register name (PascalCase by convention) and the value is a register definition object.

### Register Properties

| Property        | Type               | Required | Default  | Description                                                                                                                              |
| :-------------- | :----------------- | :------: | :------: | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `address`       | integer (0–255)    |   Yes    |    —     | The unique 8-bit address of the register. Application registers MUST use addresses ≥ 32.                                                 |
| `type`          | string             |   Yes    |    —     | The payload type. One of: `U8`, `S8`, `U16`, `S16`, `U32`, `S32`, `U64`, `S64`, `Float`.                                                 |
| `access`        | string or string[] |   Yes    |    —     | The access mode(s) of the register. A single value or an array of 1–3 unique values from: `Read`, `Write`, `Event`.                      |
| `length`        | integer (≥ 1)      |    No    |    —     | The number of elements in the register payload. If present, the payload is an array. See [Payload Length](#payload-length).              |
| `description`   | string             |    No    |    —     | A summary description of the register function. MUST be a single line.                                                                   |
| `minValue`      | number             |    No    |    —     | The minimum allowable value for the register payload.                                                                                    |
| `maxValue`      | number             |    No    |    —     | The maximum allowable value for the register payload.                                                                                    |
| `defaultValue`  | number             |    No    |    —     | The default value for the register payload. MUST lie within `minValue` and `maxValue` when those are declared.                           |
| `maskType`      | string             |    No    |    —     | The name of a `bitMask` or `groupMask` used to interpret the payload value.                                                              |
| `interfaceType` | string             |    No    |    —     | The name of the type used to represent the payload value in high-level interfaces. See [Interface Types](#interface-types).              |
| `converter`     | string             |    No    |  `None`  | Whether a hand-written converter parses and formats the payload. One of: `None`, `Payload`, `RawPayload`. See [Converters](#converters). |
| `visibility`    | string             |    No    | `public` | Whether the register is exposed in the high-level interface. One of: `public`, `private`. See [Visibility](#visibility).                 |
| `deprecated`    | boolean            |    No    | `false`  | Whether the register is deprecated.                                                                                                      |
| `volatile`      | boolean            |    No    | `false`  | Whether the register value can be saved to non-volatile memory. Volatile registers are not persisted.                                    |
| `payloadSpec`   | object             |    No    |    —     | Defines named members within a structured payload. See [Payload Specification](#payload-specification).                                  |

### Payload Length

The presence of `length`, not only its value, determines the shape of the payload:

- If `length` is **omitted**, the payload is a single scalar value of type `type`.
- If `length` is **present**, the payload is an array of exactly `length` elements of type `type`. This holds even for `length: 1`, which declares a one-element array rather than a scalar.

High-level interfaces represent the two cases differently (e.g. `ushort` versus `ushort[]`), so `length: 1` SHOULD only be used when an array representation is intended.

```yaml
Threshold: # scalar U16
  address: 40
  type: U16
  access: Write
Thresholds: # array of 3 × U16
  address: 41
  type: U16
  length: 3
  access: Write
```

Array elements are transmitted in order of increasing index. Each multi-byte element is individually encoded in little-endian byte order, as specified by the [Binary Protocol](BinaryProtocol-8bit.md); the order of the elements themselves is NOT reversed.

### Access Modes

Every register MUST declare an `access` field, which determines which Harp message types are valid for it:

| Access  | Behavior                                                                                                                          |
| :------ | :-------------------------------------------------------------------------------------------------------------------------------- |
| `Read`  | The register supports `Read` requests from the Controller. The device replies with the current register value.                    |
| `Write` | The register supports `Write` requests from the Controller. The device updates the register and replies with the resulting value. |
| `Event` | The device MAY send unsolicited `Event` messages from this register when a relevant trigger occurs.                               |

A register that specifies only `Event` as its access mode is implicitly read-only from the Controller's perspective — the Controller cannot write to it, and the device pushes data when events occur.

A single access mode is written as a scalar value:

```yaml
InfoRegister:
  address: 33
  type: U8
  access: Read
  description: A simple read-only register that returns a status code.
```

When multiple access modes are needed, they MUST be expressed as a YAML sequence (1–3 unique values):

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

The following rules apply to every `maskType`, whether on a register or on a [payload member](#payload-specification):

- It MUST name a mask declared in the device interface file or in `core.yml`.
- When it names a bit mask, every bit of that mask MUST fit within the payload element (e.g. a mask used by a `U8` register MUST NOT declare `0x100`). On a payload member with a `mask`, the bits MUST fit within that member mask after it is shifted down to bit 0 (see [Mask-Based Members](#mask-based-members-bitfield-payloads)).
- If `interfaceType` is also declared, it takes precedence over `maskType` as the type of the value.

**Example:**

```yaml
DigitalInputState:
  address: 32
  access: Event
  type: U8
  maskType: DigitalInputs
  description: Reflects the state of DI digital lines of each Port
```

### Visibility

Registers that are not meant to be exposed in high-level interfaces (e.g. code-generated classes) can be marked with `visibility: private`.

```yaml
CalibrationOffset:
  address: 33
  type: U8
  access: Read
  visibility: private
  description: Stores the factory calibration offset.
```

### Reserved Registers

A [reserved register](Device.md#reserved-registers) holds an address with no defined function, either for future use or to retire the address of a removed register. A reserved register MUST be named `Reserved` followed by its address, and MUST declare `visibility: reserved`. The schema validates it against a separate, restricted definition:

| Property      | Required | Default                    | Notes                                           |
| :------------ | :------: | :------------------------- | :---------------------------------------------- |
| `address`     |   Yes    | —                          | The reserved address.                           |
| `visibility`  |   Yes    | —                          | MUST be `reserved`.                             |
| `type`        |    No    | `U8`                       | The payload type the address is reserved for.   |
| `length`      |    No    | —                          | The payload length the address is reserved for. |
| `access`      |    No    | `Read`                     | MUST be `Read`.                                 |
| `description` |    No    | `Reserved for future use.` | A summary description. MUST be a single line.   |

No other property is allowed.

```yaml
Reserved40:
  address: 40
  visibility: reserved
  type: U16
  length: 2
  description: Reserved for future use.
```

The declared `type` and `length` matter: assigning a function to an address reserved for future use is a minor change only if the new register keeps the payload type and length of the reserved declaration. See [Reserved Registers](Device.md#reserved-registers) in Device Registers and Operation.

## Payload Specification

When a register has `length` greater than 1 (i.e. an array payload), the `payloadSpec` field MAY be used to assign names, descriptions, and constraints to individual elements within the payload. This is useful for registers that pack multiple logical values into a single array.

Similarly, when a single-element register packs multiple logical fields into one word using bit masks, `payloadSpec` MAY be used to document each bitfield.

### Payload Member Properties

Each key in `payloadSpec` is a member name, and the value is an object with the following properties:

| Property        |   Type  | Required | Description                                                                                                                              |
| :-------------- | :-----: | :------: | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `offset`        | integer |    No    | The zero-based index at which this member starts within the payload array. Ignored if the register has no `length`.                      |
| `length`        | integer |    No    | The number of elements this member spans. If omitted, the member is the single element at `offset`.                                      |
| `mask`          | integer |    No    | The bitmask used to read and write this member within a single payload word.                                                             |
| `description`   |  string |    No    | A summary description of the payload member. MUST be a single line.                                                                      |
| `minValue`      |  number |    No    | The minimum allowable value for this member.                                                                                             |
| `maxValue`      |  number |    No    | The maximum allowable value for this member.                                                                                             |
| `defaultValue`  |  number |    No    | The default value for this member. MUST lie within `minValue` and `maxValue` when those are declared.                                    |
| `maskType`      |  string |    No    | The name of a mask used to interpret this member's value.                                                                                |
| `interfaceType` |  string |    No    | The type name used for this member in high-level interfaces.                                                                             |
| `converter`     |  string |    No    | Whether a hand-written converter parses and formats this member. One of: `None`, `Payload`, `RawPayload`. See [Converters](#converters). |
| `deprecated`    | boolean |    No    | Whether the payload member is deprecated (default: `false`).                                                                             |

A member is located within the payload using two **independent** coordinates, either or both of which MAY be present:

- `offset` (with optional `length`) selects _which element(s)_ of the payload array the member occupies.
- `mask` selects _which bits_ within a payload word the member occupies.

These coordinates are orthogonal and MAY be combined: a member can specify both an `offset` (to pick an element of an array) **and** a `mask` (to pick a bitfield within that element). See [Combining Offset and Mask](#combining-offset-and-mask).

> [!NOTE]
> A member `mask` and a [bit mask](#bit-masks) answer different questions, and are often used together.
>
> - A member `mask` says **where** a value is: which bits of a payload word belong to the member. It is a single integer, it has no name of its own, and it is not shared with other registers.
> - A bit mask (or group mask), declared in the `bitMasks` (or `groupMasks`) section and referenced with `maskType`, says **what** a value means: the names of its individual flags (or of its exclusive values). It is a named type, and any number of registers or members MAY reference it.
>
> A member that needs both declares both. For example, in [`OperationControl`](#mask-based-members-bitfield-payloads) the `OperationMode` member uses `mask: 0x3` to select bits 0–1 of the register, and `maskType: OperationMode` to name the values those two bits can hold. A register that holds nothing but flags, such as `DigitalInputState` above, needs only `maskType`, since the flags occupy the whole payload. A member that holds a plain number, such as `PulseWidth` in [Combining Offset and Mask](#combining-offset-and-mask), needs only a member `mask`.

Members also need not cover the payload exhaustively. A `payloadSpec` is a _sparse annotation_: elements or bits that no member describes are simply left undocumented, and gaps between members are permitted.

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
    Heartbeat:
      description: Specifies whether the device should report the content of the heartbeat register each second.
      maskType: EnableFlag
      mask: 0x4
    DumpRegisters:
      description: Specifies whether the device should report the content of all registers on initialization.
      interfaceType: bool
      mask: 0x8
    MuteReplies:
      description: Specifies whether the replies to all commands will be muted, i.e. not sent by the device.
      interfaceType: bool
      mask: 0x10
    # VisualIndicators (0x20) and OperationLed (0x40) omitted for brevity
    Alive:
      description: Specifies whether the device should report the content of the seconds register each second.
      maskType: EnableFlag
      mask: 0x80
      deprecated: true
```

A member value is expressed relative to its mask, shifted down to bit 0. Its `minValue`, `maxValue`, and `defaultValue`, and the values of any `maskType` it references, are given in that shifted range: a member with `mask: 0xFF00` takes values `0`–`255`. Masks of members that share the same element SHOULD NOT overlap.

### Combining Offset and Mask

When an array payload packs multiple bitfields into _individual elements_, members combine both coordinates: `offset` selects the array element and `mask` selects the bits within it. Several members MAY share the same `offset` while occupying different bit ranges via distinct `mask` values.

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

The `interfaceType` field names the type used to represent a value in high-level interfaces (e.g. code-generated classes). It does not change the wire `type`; it tells consumers how to _reinterpret_ the raw payload elements.

When `interfaceType` is applied to a member that spans multiple elements (`length` > 1), the indicated elements are combined into a single value of that type:

**Example — Version information (from `core.yml`, descriptions omitted):**

```yaml
Version:
  address: 19
  type: U8
  length: 32
  access: Read
  payloadSpec:
    ProtocolVersion: # 3 × U8 reinterpreted as one HarpVersion
      offset: 0
      length: 3
      interfaceType: HarpVersion
    FirmwareVersion:
      offset: 3
      length: 3
      interfaceType: HarpVersion
    HardwareVersion:
      offset: 6
      length: 3
      interfaceType: HarpVersion
    CoreId: # 3 × U8 reinterpreted as a string
      offset: 9
      length: 3
      interfaceType: string
    InterfaceHash: # 20 × U8 left as a raw array (no interfaceType)
      offset: 12
      length: 20
```

The span is reinterpreted over the raw payload bytes, so a multi-byte result follows the little-endian byte order of the [Binary Protocol](BinaryProtocol-8bit.md). For example, a member with `offset: 13`, `length: 4`, and `interfaceType: uint` over a `U8` payload reads bytes 13–16 as one little-endian 32-bit unsigned integer.

`interfaceType` MAY also be applied at the **register level** (with no `payloadSpec`), in which case the whole payload is reinterpreted. Only `bool`, `string`, or a type handled by a [converter](#converters) are meaningful here:

```yaml
Label:
  address: 35
  type: U8
  length: 16
  access: Write
  interfaceType: string
CustomPayload:
  address: 36
  type: U32
  length: 3
  access: Read
  interfaceType: HarpVersion
  converter: Payload
```

When `interfaceType` is applied at the register level **together with** a `payloadSpec`, it names the payload type instead of reinterpreting it. See [Payload Types](#payload-types).

### Interface Types

The set of valid `interfaceType` names is open-ended: the schema accepts any string, and tooling MAY support additional names. The following names are standardized and SHOULD be supported by tooling that consumes `interfaceType`. New names MAY be standardized in the future if widespread use cases emerge.

| Interface Type | Wire type | Notes                                                                                                                                               |
| :------------- | :-------: | :-------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bool`         |    any    | Boolean flag. Reads `true` if the value is non-zero. A member using it MUST NOT span more than one element.                                         |
| `byte`         |    `U8`   | 8-bit unsigned integer.                                                                                                                             |
| `sbyte`        |    `S8`   | 8-bit signed integer.                                                                                                                               |
| `ushort`       |   `U16`   | 16-bit unsigned integer.                                                                                                                            |
| `short`        |   `S16`   | 16-bit signed integer.                                                                                                                              |
| `uint`         |   `U32`   | 32-bit unsigned integer.                                                                                                                            |
| `int`          |   `S32`   | 32-bit signed integer.                                                                                                                              |
| `ulong`        |   `U64`   | 64-bit unsigned integer.                                                                                                                            |
| `long`         |   `S64`   | 64-bit signed integer.                                                                                                                              |
| `float`        |  `Float`  | 32-bit IEEE 754 floating-point value.                                                                                                               |
| `string`       |    `U8`   | UTF-8 text over a span of bytes. The payload `type` MUST be `U8`, and the register or member MUST declare a `length`.                               |
| `HarpVersion`  |    `U8`   | A [semantic version](https://semver.org/) (`major.minor.patch`). Without a converter, it MUST be used on a member spanning exactly 3 `U8` elements. |

Unless a [converter](#converters) is declared, a primitive name (`byte` through `float`) MUST fit the elements it represents:

- On a member that declares `length`, the primitive MUST be the size of the elements it spans. For example, `uint` (4 bytes) MAY span 4 × `U8` or 2 × `U16`, but not 2 × `U8`. A register cannot do this directly: declare a spanning `payloadSpec` member instead.
- On a single element (a member without `length`, or a scalar register), the primitive MUST match the wire type (e.g. `int` requires `S32`).
- On a member with a `mask`, any primitive MAY be used (e.g. `byte` for the `0xFF00` field of a `U16` word).

Any other name is treated as a custom type that the consuming tooling does not know how to build. A custom `interfaceType` MUST be accompanied by a [converter](#converters), except when it names a [payload type](#payload-types).

### Payload Types

When a register declares a `payloadSpec`, tooling generates a structured type to hold its members. By default this type is named after the register with a `Payload` suffix (e.g. `AnalogDataPayload` for `AnalogData`). A register-level `interfaceType` overrides this name.

Several registers MAY share one payload type by declaring the same `interfaceType`. All registers that share a payload type MUST declare the same `type`, the same `length`, and an identical `payloadSpec`. Anchors and aliases are a convenient way to guarantee this:

```yaml
Rgb0:
  address: 71
  type: U8
  length: 3
  access: Write
  interfaceType: RgbPayload
  payloadSpec: &rgbPayload
    Red:
      offset: 0
    Green:
      offset: 1
    Blue:
      offset: 2
Rgb1:
  address: 72
  type: U8
  length: 3
  access: Write
  interfaceType: RgbPayload
  payloadSpec: *rgbPayload
```

A payload type is part of the public interface if any register using it has `public` visibility.

### Converters

A converter delegates the conversion between the wire payload and its `interfaceType` to hand-written code that accompanies the generated interface. It is the escape hatch for representations that cannot be described declaratively, and for custom `interfaceType` names. When a converter is declared, the [primitive type rules](#interface-types) do not apply.

| Converter    | Behavior                                                                                                                      |
| :----------- | :---------------------------------------------------------------------------------------------------------------------------- |
| `None`       | Default. Tooling performs the conversion itself.                                                                              |
| `Payload`    | The converter receives the payload already decoded as `type` (a scalar, an array, or the member's span of elements).          |
| `RawPayload` | The converter receives the raw payload bytes. Useful when the payload does not decompose into elements of a single wire type. |

```yaml
CustomMemberConverter:
  address: 38
  type: U8
  length: 5
  access: Read
  payloadSpec:
    Header:
      offset: 0
    Data:
      offset: 1
      length: 2
      interfaceType: int # 2 bytes into a 4-byte int: only possible with a converter
      converter: Payload
```

The form of the converter is specific to each target language. For example, `Harp.Generators` emits `partial` method declarations (`ParsePayload` and `FormatPayload`) in C#, and imports converter functions from a companion `converters` module in Python, except for standardized types such as `HarpVersion`.

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

Bit mask values represent individual flags that can be OR-ed together, and are subject to the following rules:

- Each value MUST be a single bit (a power of two). Combinations of flags are expressed by OR-ing members in the high-level interface, not by declaring them as members.
- A value of `0` is permitted only for a member named `None`, representing the empty set.
- Each value MUST be unique within the mask.
- Each value MUST fit within 32 bits.

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

Group mask values are _typically_ sequential integers starting from zero, since they represent mutually exclusive modes or states. This is a convention, not a requirement: the schema accepts any integer values, and non-sequential values (e.g. `0x1`, `0x2`, `0x4`, `0xA`) are permitted. Each value MUST fit within 32 bits.

> [!Note] Following the naming convention for Enums proposed by [Microsoft](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/enum), `GroupMask` names SHOULD be singular (e.g. `MimicOutput`) since they represent a single choice among options, and value names SHOULD also be singular (e.g. `DIO0`) since they represent individual states.

## Style Guide

Identifiers declared in a device interface file are not private to the file: code generators lift register names, mask names, and payload member names directly into the public surface of the interfaces they emit (classes, properties, enumerations, and enumeration members). A name chosen here becomes a name a downstream user must type.

For this reason, device interface files SHOULD follow the [.NET Framework Design Guidelines](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/) for naming, in particular [Capitalization Conventions](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/capitalization-conventions), [General Naming Conventions](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/general-naming-conventions), and [Enum Design](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/enum). The remaining conventions in this section are derived from existing Harp device interfaces, of which [`device.behavior`](https://github.com/harp-tech/device.behavior/blob/main/device.yml) is the reference implementation.

### Casing Summary

| Element                   | Casing                 | Rationale                                                             | Example                                |
| :------------------------ | :--------------------- | :-------------------------------------------------------------------- | :------------------------------------- |
| Device `name`             | `PascalCase`           | Becomes the name of the generated device type; required by the schema | `Behavior`, `SoundCard`                |
| Register name             | `PascalCase`           | Becomes a public type or member in generated interfaces               | `DigitalInputState`, `PwmDutyCycleDO0` |
| `bitMasks` entry name     | `PascalCase`, plural   | Becomes a flags enumeration; multiple values combine                  | `DigitalOutputs`, `PwmOutputs`         |
| Bit name                  | `PascalCase`, singular | Becomes a single flag member                                          | `DOPort0`, `Led1`                      |
| `groupMasks` entry name   | `PascalCase`, singular | Becomes a simple enumeration; one value at a time                     | `MimicOutput`                          |
| Group mask value name     | `PascalCase`, singular | Becomes a single enumeration member                                   | `Position`, `Displacement`             |
| `payloadSpec` member name | `PascalCase`           | Becomes a property on the generated payload type                      | `AnalogInput0`, `Red0`                 |
| YAML anchor name          | `camelCase`            | Authoring aid only; never surfaces in a generated interface           | `&pulseDO`, `&rgbType`                 |
| Schema property key       | `camelCase`            | Fixed by the schema, not author-chosen                                | `maskType`, `protocolVersion`          |

Names MUST NOT contain underscores, hyphens, or any other non-alphanumeric character. Note that this differs from the `SCREAMING_SNAKE_CASE` used for core register names in [Device Registers and Operation](Device.md#core-registers) (e.g. `R_WHO_AM_I`): those are conventional names for the registers as described by the protocol, whereas the identifiers in this file are the names of the generated interface members (e.g. `WhoAmI`).

### Acronyms and Abbreviations

Abbreviations and contractions SHOULD NOT be used — prefer `PulseDuration` over `PulseDur`. Acronyms are capitalized according to their length, following the .NET rule:

- **Two-letter acronyms** keep both letters capitalized: `DI`, `DO`, `IO`, `IR` — as in `DIPort0`, `PulseDO0`, `MimicPort0IR`.
- **Acronyms of three or more letters** are treated as ordinary words and PascalCased: `Pwm` (not `PWM`), `Rgb` (not `RGB`), `Led` (not `LED`), `Adc` (not `ADC`) — as in `PwmFrequencyDO0`, `RgbAll`, `Led1Current`.

Only widely accepted acronyms SHOULD be used, and only where the expanded form would be unreasonably verbose.

### Register Names

Register names SHOULD read as noun phrases when the register holds state, and as verb phrases when writing to the register performs an action:

```yaml
DigitalInputState:  # holds state — noun phrase
AnalogData:         # holds state — noun phrase
EncoderMode:        # holds state — noun phrase
StartCameras:       # performs an action — verb phrase
EncoderReset:       # performs an action — verb phrase
```

Registers belonging to the same functional family SHOULD share a leading term so that they sort and autocomplete together, with the distinguishing qualifier and any index following it:

```yaml
PulseDOPort0: # <Family><Target><Index>
PulseDOPort1:
PwmFrequencyDO0:
PwmDutyCycleDO0:
MimicPort0Valve:
```

Indices SHOULD be zero-based and appended without a separator (`Led0`, `Camera1Frame`), matching the hardware numbering printed on the device.

Register names SHOULD be unique across the whole device — including against core register names — since consumers typically merge `core.yml` and the device interface file into a single namespace.

### Mask and Payload Member Names

Mask naming follows [Enum Design](https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/enum) and is described in detail under [Bit Masks](#bit-masks) and [Group Masks](#group-masks). Two further rules apply:

- Mask names MUST NOT carry a `Mask`, `Flag`, `Flags`, or `Enum` suffix; the section the mask is declared in already conveys its kind.
- Bit and value names MUST NOT carry a prefix repeating the mask name. Within `DigitalOutputs`, the flag is `DOPort0`, not `DigitalOutputsDOPort0`.
- A `groupMasks` entry that has a natural "nothing selected" state SHOULD name that value `None` and assign it `0`.

`payloadSpec` member names SHOULD describe the quantity the member carries rather than its position in the payload — `AnalogInput0` and `Encoder` rather than `Element0` and `Element1`.

### Descriptions

The `description` field SHOULD be supplied for every register, bit, and group mask value, since it is the source of the documentation comments in generated interfaces. Descriptions SHOULD:

- Fit on a single line. Multi-line descriptions (e.g. YAML `|` block scalars) MUST NOT be used, since they cannot be carried into single-line documentation comments.
- Begin with a capital letter and read as a single sentence.
- Use the third person to state what the register _is_ or _does_ (`Reflects the state of DI digital lines of each Port`, `Specifies the duty cycle of the PWM at DO0`), rather than addressing the reader.
- Be terminated with a period, applied consistently across the file.
- Be written as plain unquoted YAML scalars, reserving quoting for values that genuinely require it.

### Value Formatting

- Bit mask and `mask` values SHOULD be written in hexadecimal with uppercase digits (`0x1`, `0x80`, `0x3FF`), since their bit structure is the point.
- Group mask values SHOULD be written in decimal, since they are ordinarily sequential.
- `version` and `protocolVersion` MUST be quoted (`"3.4"`), otherwise YAML parses them as floating-point numbers and `"3.10"` would collapse to `3.1`.
- Indentation SHOULD be two spaces per level, and the file SHOULD open with the `%YAML 1.1` directive, the `---` document start, and the schema directive comment.

> [!NOTE]
> Some names in existing device interfaces predate this guide and do not follow it — `EncoderModeMask` carries a forbidden `Mask` suffix, and `PortDigitalIOS` pluralizes an acronym awkwardly. These names are retained because changing them is a breaking change for every downstream consumer. New names SHOULD follow this guide; existing names SHOULD only be corrected as part of a deliberate major revision of the device interface.

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
    <<: *startPulse # inherits DigitalOutput and PulseWidth
    Frequency: # and adds further members
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

## Constraints Beyond the Schema

The following rules are stated throughout this document but cannot be checked by the JSON schema alone. Tooling that loads a device interface file SHOULD check them and report every violation found.

| Rule                                                                                                              | Section                                              |
| :---------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------- |
| Every `description` is a single line.                                                                             | [Descriptions](#descriptions)                        |
| `defaultValue` lies within `minValue` and `maxValue`.                                                             | [Register Properties](#register-properties)          |
| `maskType` names a bit mask or group mask declared in the file or in `core.yml`.                                  | [Mask Type Reference](#mask-type-reference)          |
| The bits of a referenced bit mask fit within the payload element, or within the (shifted) member `mask`.          | [Mask Type Reference](#mask-type-reference)          |
| Bit mask values are single, unique bits; zero is only allowed for `None`.                                         | [Bit Masks](#bit-masks)                              |
| Bit mask and group mask values fit within 32 bits.                                                                | [Bit Masks](#bit-masks), [Group Masks](#group-masks) |
| `interfaceType: string` is only used with payload type `U8`.                                                      | [Interface Types](#interface-types)                  |
| `interfaceType: bool` does not span more than one element.                                                        | [Interface Types](#interface-types)                  |
| A primitive `interfaceType` matches the wire type on a single element, or the byte size of the elements it spans. | [Interface Types](#interface-types)                  |
| A primitive `interfaceType` is not declared on a register with a `length` and no `payloadSpec`.                   | [Interface Types](#interface-types)                  |
| Registers sharing a payload type declare the same `type`, `length`, and `payloadSpec`.                            | [Payload Types](#payload-types)                      |
| Register addresses are unique, including against `core.yml`.                                                      | [Register Properties](#register-properties)          |
