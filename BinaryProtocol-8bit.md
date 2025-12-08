<img src="./assets/HarpLogo.svg" width="200">

# Binary Protocol 8-bit

This document defines the binary communication protocol used to facilitate and unify the interaction between different Harp devices, and between computers or other controllers and Harp devices. It was designed with efficiency and ease of parsing in mind.

## Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Message Interface

The Harp Binary Protocol SHOULD be used for all exchanges between a **Controller** and a **Device**. The Controller is typically a computer, or a server. The Device is typically a data acquisition or actuator microcontroller.

Exchanges of data using the protocol are based on messages addressed to specific registers, as defined in the [Device Interface](Device.md#device-interface).

> [!NOTE]
>
> The Harp Binary Protocol uses Little-Endian byte ordering.

## Harp Message Format

All Harp messages MUST follow the structure below, specifying the minimal amount of information for a well-defined exchange of data.

| Harp Message                               |
| ------------------------------------------ |
| [MessageType](#messagetype-1-byte)         |
| [Length](#length-1-byte)                   |
| [ExtendedLength](#extendedlength-2-bytes)* |
| [Address](#address-1-byte)                 |
| [Port](#port-1-byte)                       |
| [PayloadType](#payloadtype-1-byte)         |
| [Timestamp](#timestamp-6-bytes)*           |
| [Payload](#payload--bytes)                 |
| [Checksum](#checksum-1-byte)               |

> [!NOTE]
> 
> Fields marked with * can be included or omitted under specific conditions. Check the corresponding section for details.

### MessageType (1 byte)

Specifies the type and other operation flags of the Harp message. The structure of this byte MUST follow the below specification:

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
    <td align="center">0</td>
    <td align="center">0</td>
    <td align="center">0</td>
    <td align="center">0</td>
    <td align="center">Error</td>
    <td align="center">0</td>
    <td align="center" colspan="2">Type</td>
</tr>
</table>

#### Type (2 bits)

Specifies the type of the Harp message.

|   Value   |  Description  |
| :-------  |  ----------- |
| 1 (`Read`)  |  Read the contents of the register with the specified [`Address`](#address-1-byte)  |
| 2 (`Write`) |   Write the contents to the register with the specified [`Address`](#address-1-byte)     |
| 3 (`Event`) |   Send the contents of the register with the specified [`Address`](#address-1-byte)     |

#### Error flag (1 bit)

When this flag is set, the message represents an error reply sent from the Device to a request from the Controller. This flag SHOULD NOT be set in any other messages. This flag SHALL NOT be set in any messages sent from the Controller to the Device.

### Length (1 byte)

Specifies the number of bytes (`U8`) after this field that are still available and need to be read to complete the Harp message. If one byte is not enough to express the length of the message, the `Length` field MUST be set to 255. In this case the [`ExtendedLength`](#extendedlength-2-bytes) field MUST be included.

### ExtendedLength (2 bytes)

Specifies the number of bytes (`U16`) after this field that are still available and need to be read to complete the Harp message. If this field is used, the [`Length`](#length-1-byte) field MUST be set to 255.

### Address (1 byte)

Specifies the address of the register to which the message payload refers to.

### Port (1 byte)

Specifies the origin or destination Device of a Harp message, to be used when a hub Device is mediating access to several Devices. If the field is unused or if it refers to the Device itself, its value MUST be `0xFF`.

### PayloadType (1 byte)

Indicates the type of data available in [`Payload`](#payload--bytes). The structure of this byte MUST follow the below specification:

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
    <td align="center" colspan="4">Size</td>
</tr>
</table>

#### Size (4 bits)

Specifies the size of each word in [`Payload`](#payload--bytes).

|  Value  |  Description  |
| :-----: |  -----------: |
| 1       |    8 bits     |
| 2       |   16 bits     |
| 4       |   32 bits     |
| 8       |   64 bits     |

#### HasTimestamp (1 bit)

If the Harp message contains a timestamp, this bit MUST be set. In this case the fields [`Seconds`](#seconds-4-bytes) and [`Microseconds`](#microseconds-2-bytes) MUST be included in the message.

#### IsFloat (1 bit)

This bit indicates whether [`Payload`](#payload--bytes) encodes fractional values. If the bit is not set, the payload contains integers.

> [!NOTE]
>
> The bit [`IsFloat`] MUST NOT be set with 8-bit or 16-bit sized payloads.

#### IsSigned (1 bit)

This bit indicates whether [`Payload`](#payload--bytes) encodes integers with signal. If the bit is not set, the payload contains unsigned integers.

> [!NOTE]
>
> The bits [`IsFloat`] and [`IsSigned`] MUST NOT be set simultaneously.

### Timestamp (6 bytes)

Specifies the value of the Device Harp clock. If the [`HasTimestamp`](#hastimestamp-1-bit) flag is set, the following fields MUST be present before the message payload.

#### Seconds (4 bytes)

Specifies the number of whole seconds (`U32`) in the Harp Timestamp.

#### Microseconds (2 bytes)

Specifies the fractional part of the Harp Timestamp (`U16`) encoded as the number of microseconds divided by 32.

> [!NOTE]
>
> The full timestamp information, in seconds, can be retrieved using the formula:  
> `Timestamp = Seconds + Microseconds * 32e-6`

### Payload (? bytes)

The contents of the Harp message.

### Checksum (1 byte)

The sum of all bytes (`U8`) contained in the other fields of the Harp message structure. The receiver of the message MUST calculate its own checksum from all received bytes and compare it against the received value in this field. If the two values do not match, the Harp message SHOULD be discarded.

## Implementation Notes and Code Examples

Below we present technical notes and reference implementation examples for some of the protocol features.

### MessageType and ErrorFlag

The following pseudo-code snippet illustrates how to check for the [`Error`](#error-flag-1-bit) flag in the [`MessageType`](#messagetype-1-byte) field:

```C#
    int errorMask = 0x08;

    if (MessageType & errorMask)
    {
        printf(“Error detected.\n”);
    }
```

### Parsing PayloadType

The following pseudo-code snippet illustrates how all possible [`PayloadType`](#payloadtype-1-byte) values are defined.

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

Bit masking can be used to check whether time information is available, regardless of the payload type:

```C
int hasTimestamp = 0x10;

if (PayloadType & hasTimestamp)
{
    printf(“Time information is available in the Harp message payload.\n”);
}
```

### Using Checksum to validate communication integrity

Example of how to calculate the [`Checksum`](#checksum-1-byte) in C:

```C
unsigned char Checksum = 0;
int i = 0;
for (; i < Length + 1; i++)
{
    Checksum += HarpMessage(i);
}
```

### Parsing [Payload] with Arrays

The [`Payload`](#payload--bytes) field can contain a single value, or an array of values of the same type. The first step to parse these payloads is to first find the number of values contained in the [`Payload`](#payload--bytes) field. The following code example demonstrates how to calculate the array length for both timestamped and non-timestamped payloads:

```C
int arrayLength;
int hasTimestamp = 0x10;
int sizeMask = 0x0F;

if (PayloadType & hasTimestamp)
{
    // Harp message with time information
    arrayLength = (Length – 10) / (PayloadType & sizeMask )
}
else
{
    // Harp message without time information
    arrayLength = (Length – 4) / (PayloadType & sizeMask )
}
```

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

- v1.5.0
  * Add requirements language.
  * Changed naming of Command to Request.
  * Clarify request-reply contract and add event stream patterns.
  * Avoid scattering of message specification features.
  * Discourage the use of polymorphic register behavior.