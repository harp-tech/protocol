<img src="./assets/HarpLogo.svg" width="200">

# Binary Protocol 8-bit (harp-1.0)

## Introduction

The Harp Protocol is a binary communication protocol created in order to facilitate and unify the interaction between different devices. It was designed with efficiency and ease of parsing in mind.

The protocol is based on addresses. Each address points to a certain memory position available in the device. These positions are called registers. Each register is defined by a data type and some meaningful functionality attached to the data.

The Harp Binary Protocol is commonly used for all exchanges between a `Controller` and a `Device`. The controller can be a computer, or a server and the device can be a data acquisition or actuator microcontroller.

The available packets are:

* `Command`: Sent by the Controller to the Device. Command messages can be used to read or write the register contents.
* `Reply`: Sent by the Device in response to a Command.
* `Event`: Sent by the Device when an external or internal event of interest happens. An Event message will always carry the contents of the register that the event refers to.

> **Note**
>
> The Harp Binary Protocol uses Little-Endian byte ordering.

## Harp Message specification

The Harp Message contains a minimal amount of information to execute a well-defined exchange of data. It follows the structure below.

| Harp Message |
| ------------ |
| MessageType  |
| Length       |
| Address      |
| Port         |
| PayloadType  |
| Payload      |
| Checksum     |

### MessageType (1 byte)

Specifies the type of the Harp Message.

|   Value   |  Description  |
| :-------  |  ----------- |
| 1 (`Read`)  |  Read the content of the register with address [`RegisterAddress`]  |
| 2 (`Write`) |   Write the content to the register with address [`RegisterAddress`]     |
| 3 (`Event`) |   Send the content of the register with address [`RegisterAddress`]     |

### Length (1 byte)

Contains the number of bytes that are still available and need to be read to complete the Harp message (i.e. number of bytes after the field [`Length`]).

### Address (1 byte)

Contains the address of the register to which the Harp Message refers to.

### Port (1 byte)

If the device is a Hub of Harp Devices, it indicates the origin or destination of the Harp Message. If the field is not used or it’s equal to `0xFF`, it points to the device itself.

### PayloadType (1 byte)

Indicates the type of data available on the [`Payload`].
The structure of this byte follows the following specification:

<table>
<tr>
    <th align="center">7</th>
    <th align="center">6</th>
    <th align="center">5</th>
    <th align="center">4</th>
    <th align="center">3</th>
    <th align="center">2</th>
    <th align="center">1</th>
    <th align="center">0</th>
</tr>
<tr>
    <td align="center">IsSigned</td>
    <td align="center">IsFloat</td>
    <td align="center">0</td>
    <td align="center">HasTimestamp</td>
    <td align="center" colspan="4">Type</td>
</tr>
</table>

#### Type (4 bits)

Specifies the size of the word in the [`Payload`].

|  Value  |  Description  |
| :-----: |  -----------: |
| 1       |    8 bits     |
| 2       |   16 bits     |
| 4       |   32 bits     |
| 8       |   64 bits     |

#### HasTimestamp (1 bit)

If this bit is set the Harp Message contains a timestamp. In this case the fields [`Seconds`] and [`Microseconds`] must be present in the message.

#### IsFloat (1 bit)

This bit indicates whether the [`Payload`] represents fractional values. If the bit is not set, the payload contains integers.

#### IsSigned (1 bit)

If the bit is set, indicates that the [`Payload`] contains integers with signal.

> **Note**
>
> The bits [`IsFloat`] and [`IsSigned`] must never be set simultaneously.

### Payload (? bytes)

The content of the Harp Message.

If the [`HasTimestamp`] flag is set, the following optional fields are present at the beginning of the message payload:

#### Seconds (4 bytes)

Contains the number of seconds (`U32`) of the Harp Timestamp clock. This field is optional. In order to indicate that this field is available, the bit [`HasTimestamp`] in the field [`PayloadType`] needs to be set.

#### Microseconds (2 bytes)

It contains the fractional part of the Harp Timestamp clock in microseconds (`U16` containing the number of microseconds divided by 32).

This field is optional. In order to indicate that this field is available, the bit [`HasTimestamp`] in the field [`PayloadType`] needs to be set.

> **Note**
>
> The full timestamp information can thus be retrieved using the formula:
> Timestamp(s) = [`Seconds`] + [`Microseconds`] * 32 * 10-6

### Checksum (1 byte)

The sum of all bytes (`U8`) contained in the Harp Message.
The receiver of the message should calculate the checksum and compare it with the received. If they don’t match, the Harp Message should be discarded.

---

## Features and Code Examples

Some of the fields described on the previous chapter have special features. These are presented next.

### MessageType and ErrorFlag

The field [`Command`] has an Error flag on the 4th least significant bit. When this bit is set it means that an error has occured.
Examples of possible errors cane be:

  1. The controller tries to read from a register that doesn’t exist;
  2. The controller tries to write invalid data to a certain register;
  3. The [`PayloadType`] doesn’t match the target register specification.

A simple code in C to check for error will be:

```C
    int errorMask = 0x08;

    if (Command & errorMask)
    {
    printf(“Error detected.\n”);
    }
```

### Harp Message Length

If one byte is not enough to express the length of the Harp Message, use [`Length`] equal to 255 and add after an unsigned 16 bits word with the Harp Message length.

Replace the [`Length`] with:
    [255] (1 byte) [`ExtendedLength`] (2 bytes)

### Parsing PayloadType

For the definition of the `PayloadType` types, a `C#` code snippet is presented.

Note that the time information can appear without an element Timestamp<>.

```C#
  int isUnsigned = 0x00;
  int isSigned = 0x80;
  int isFloat = 0x40;
  int hasTimestamp = 0x10;

  enum PayloadType 
  {
      U8  = (isUnsigned | 1),
      S8  = (isSigned   | 1),
      U16 = (isUnsigned | 2),
      S16 = (isSigned   | 2),
      U32 = (isUnsigned | 4),
      S32 = (isSigned   | 4),
      U64 = (isUnsigned | 8),
      S64 = (isSigned   | 8),
      Float = (isFloat  | 4),
      Timestamp = hasTimestamp,
      TimestampedU8  = (hasTimestamp | U8),
      TimestampedS8  = (hasTimestamp | S8),
      TimestampedU16 = (hasTimestamp | U16),
      TimestampedS16 = (hasTimestamp | S16),
      TimestampedU32 = (hasTimestamp | U32),
      TimestampedS32 = (hasTimestamp | S32),
      TimestampedU64 = (hasTimestamp | U64),
      TimestampedS64 = (hasTimestamp | S64),
      TimestampedFloat = (hasTimestamp | Float)
  }
```

The field `PayloadType` has a flag on the 5th least significant bit that indicates if the time information is available on the Harp Message. The existence of this flag is useful to know if the fields [`Seconds`] and [`Microseconds`] are present on the Harp Message.
In `C` one can check if the time information is avaible by using the following snippet:

```C
int hasTimestamp = 0x10;

if (PayloadType &  hasTimestamp )
{
    printf(“The time information is available on the Harp Message’s Payload.\n”);
}
```

### Using Checksum to validate communication integrity

The [`Checksum`] field is the sum of all bytes contained in the Harp Message. The receiver of the message should calculate the checksum and compare it with the received. If they don’t match, the Harp Message should be discarded.
Example on how to calculate the [`Checksum`] in C language:

```C
unsigned char Checksum = 0;
int i = 0;
for (; i < Length + 1; i++ )
{
    Checksum += HarpMessage(i);
}
```

### Parsing [Payload] with Arrays

The [`Payload`] element can contain a single, or an array of values of the same type. The first step to parse these payloads is to first find the number of values contained on the [`Payload`] element. This can be done using the following `C` code example:

```C
int arrayLength;
int hasTimestamp = 0x10;
int sizeMask = 0x0F;

if (PayloadType & hasTimestamp)
{
    // Harp Message has time information
    arrayLength = (Length – 10) / (PayloadType & sizeMask )
}
else
{
    // Harp Message doesn’t have time information
    arrayLength = (Length – 4) / (PayloadType & sizeMask )
}
```
---

## Typical usage

### Commands

The device that implements this Harp Protocol receives `Write` and `Read` commands from the controller, and replies with a message from the same address and same type, timestamped with the hardware time at which the command was applied. This behavior is core to the protocol and is expected to be implemented by all devices that use it. As a rule of thumb, for each `Write` or `Read` command, a single reply message should be returned from the device. The message should be emitted from the same register that the command was issued to. It should be noted that the payload of the returned value might be different from the one issued by the command, as the device can operate/transform the issued `Write` command. ([see "Register Polymorphism" section below](#register-polymorphism)).

> Exceptions to the previous contract are possible but should be avoided. The single supported exception is the `R_OPERATION_CTRL` (via  **DUMP [Bit 3]**) that allows the controller to request a dump of all registers in the device. In this case, the device should reply with a single `Write` message from `R_OPERATION_CTRL`, honoring the previous contract, but will it also emit a volley of `Read` messages, one for each register in the device.

Some Harp Messages are shown below to demonstrate the typical usage of the protocol between a device and a controller. Note that timestamp information is usually omitted in messages sent from the controller to the device, since actions are expected to run as soon as possible.

We will use the following abbreviations:

- [CMD] is a Command (From the Controller to the Device);
- [RPL] is a Reply (From Device to the Controller)
- [EVT] is an Event. (A message sent from the Device to the Controller without a command (*i.e.* request) from the Controller)

#### Write Message

- [CMD] **Controller**:       `2`  `Length` `Address` `Port` `PayloadType` `T` `Checksum`
- [RPL] **Device**: `2`  `Length` `Address` `Port` `PayloadType` `Timestamp<T>` `Checksum`       OK
- [RPL] **Device**: `10` `Length` `Address` `Port` `PayloadType` `Timestamp<T>` `Checksum`       ERROR

The timestamp information in the [RPL] represents the time when the register with [Address] was updated.

#### Read Message

- [CMD] **Controller**: `1` `4`      `Address` `Port` `PayloadType` `Checksum`
- [RPL] **Device**: `1` `Length` `Address` `Port` `PayloadType` `Timestamp<T>` `Checksum`       OK
- [RPL] **Device**: `9` `10`     `Address` `Port` `PayloadType` `Timestamp<T>` `Checksum`        ERROR

The timestamp information in the [RPL] represents the time when the register with [Address] was read.

#### Event message

- [EVT] **Device**: `3` `Length` `Address` `Port` `PayloadType` `Timestamp<T>` `Checksum`      OK

The timestamp information in [EVT] represents the time when the register with [Address] was read.

### Intended Usage

#### Register polymorphism


While it is possible to have different types of data in the same register, we **STRONGLY** discourage this practice. The protocol was designed to be as simple as possible, and having different types of data in the same register would make the parsing of the messages unnecessary more complex. As a rule, each register should: (1) have a single data type (e.g. `U8`) for all message types (`Read`, `Write`, `Event`), (2) the payload should have the same "function"/"meaning" regardless of the message type (see examples below), and (3) the payload data should be of the same size for all message types.
It should be noted that this guide doesnt necessarly mean that the payload issued by a `Write` message should be the same as the one issued by a `Read` message, as the device can operate/transform the issued `Write`.


> **Examples**
>
> Consider the following register:
>
>```
>   CameraFrequency:
>   - Address: 32
>   - Type: U8
>   - Access: Read, Write
>   - Description: Sets the frequency of the camera in Hz.
>```
>
> DO NOT ❌
>
>   - Return the frequency in U16 for a `Read` command and the frequency in U8 for a `Write` command. (i.e. Share the same data type.)
>   - Return the frequency in Hz for a `Read` command and the period in seconds for a `Write` command. (i.e. share the same function/meaning.)
>
> DO ✅
>
>   - Return the frequency in U8 for both a `Read` and `Write` command.
>   - Return the frequency in Hz for both a `Read` and a `Write` command.
>   - `Write` a value of `101` to set the frequency, but both `Read` and `Write` return the frequency of 100Hz. This behavior is perfectly acceptable as the device might not be able to set the frequency to the exact value requested by the controller, and instead returns the value that was set.

---

## Release notes:

- v0.1
    * First draft.

- v0.2
    * Changed Event Command to 3.

- v0.3
    * Cleaned up document and added C code examples.
    * First release.

- v1.0
    * Updating naming of the protocol fields, etc, to latest naming review.
    * Major release.

- v1.1
    * Corrected [`PayloadType`] list on page 2.

- v1.2
    * Changed device naming to Controller and Peripheral.

- v1.3
    * Minor corrections.

- v1.4.0
  * Refactor documentation to markdown format.
  * Minor typo corrections.
  * Improve clarity of some sections.
  * Adopt semantic versioning.

- v1.4.1
  * Remove table of contents to avoid redundancy with doc generators.
  * Avoid using verbatim literals in titles.
  * Change device naming to Controller and Device.

- v1.4.2
  * Clarify request-reply contract.
  * Discourage the use of polymorphic register behavior.